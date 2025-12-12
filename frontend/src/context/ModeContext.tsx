import React, { createContext, useContext, useReducer, useEffect, useCallback, ReactNode } from 'react';
import { apiClient } from '@/services/api-client';
import { logger } from '@/services/logger';

const log = logger.create('ModeContext');

// Application mode type
export type ApplicationMode = 'training' | 'live';

// Mode settings interface matching backend
export interface ModeSettings {
  mode: ApplicationMode;
  require_confirmation_for_live: boolean;
}

// Mode context state
export interface ModeState {
  // Current mode
  mode: ApplicationMode;

  // Loading state
  isLoading: boolean;

  // Error state
  error: string | null;

  // Initialization state
  initialized: boolean;

  // Screen reader announcements
  announcements: string[];
}

// Actions for mode reducer
type ModeAction =
  | { type: 'SET_MODE'; payload: ApplicationMode }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ANNOUNCE'; payload: string }
  | { type: 'CLEAR_ANNOUNCEMENT' }
  | { type: 'INITIALIZE'; payload: ApplicationMode };

// Default state
const defaultState: ModeState = {
  mode: 'training',
  isLoading: false,
  error: null,
  initialized: false,
  announcements: [],
};

// Storage key for persisting mode
const STORAGE_KEY = 'cybersec-app-mode';

// Reducer function
function modeReducer(state: ModeState, action: ModeAction): ModeState {
  switch (action.type) {
    case 'SET_MODE':
      return {
        ...state,
        mode: action.payload,
        error: null,
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'ANNOUNCE':
      return { ...state, announcements: [...state.announcements, action.payload] };
    case 'CLEAR_ANNOUNCEMENT':
      return { ...state, announcements: state.announcements.slice(1) };
    case 'INITIALIZE':
      return {
        ...state,
        mode: action.payload,
        initialized: true,
        isLoading: false,
      };
    default:
      return state;
  }
}

// Context value interface
interface ModeContextValue {
  // Current mode and state
  mode: ApplicationMode;
  isLoading: boolean;
  error: string | null;

  // Actions
  setMode: (mode: ApplicationMode) => Promise<void>;
  toggleMode: () => Promise<void>;
  refreshMode: () => Promise<void>;
}

// Create context
const ModeContext = createContext<ModeContextValue | null>(null);

// Provider component
export function ModeProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(modeReducer, defaultState);

  /**
   * Announce a message to screen readers.
   * Used for mode change notifications.
   */
  const announce = useCallback((message: string) => {
    dispatch({ type: 'ANNOUNCE', payload: message });
    // Clear announcement after screen reader has time to read it
    setTimeout(() => {
      dispatch({ type: 'CLEAR_ANNOUNCEMENT' });
    }, 1000);
  }, []);

  /**
   * Fetch current mode from backend API.
   * Backend is the source of truth for application mode.
   */
  const fetchModeFromBackend = useCallback(async () => {
    log.debug('Fetching mode from backend');
    const result = await apiClient.get<ModeSettings>('/settings/mode');

    if (result.success && result.data) {
      return result.data.mode;
    } else {
      log.warn('Failed to fetch mode from backend, using default', result.error);
      return null;
    }
  }, []);

  /**
   * Save mode to backend API.
   */
  const saveModeToBackend = useCallback(async (mode: ApplicationMode): Promise<boolean> => {
    log.debug('Saving mode to backend', { mode });
    const result = await apiClient.post<ModeSettings>('/settings/mode', {
      mode,
      require_confirmation_for_live: true,
    });

    if (result.success) {
      log.info('Mode saved to backend successfully', { mode });
      return true;
    } else {
      log.error('Failed to save mode to backend', result.error);
      dispatch({ type: 'SET_ERROR', payload: result.error?.detail || 'Failed to save mode' });
      return false;
    }
  }, []);

  /**
   * Initialize mode on mount.
   * Order of precedence:
   * 1. Backend API (source of truth)
   * 2. localStorage (fallback during offline/loading)
   * 3. Default to 'training'
   */
  useEffect(() => {
    async function initializeMode() {
      dispatch({ type: 'SET_LOADING', payload: true });

      try {
        // Try to load from localStorage first for instant UI
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored && (stored === 'training' || stored === 'live')) {
          dispatch({ type: 'SET_MODE', payload: stored as ApplicationMode });
        }

        // Fetch from backend (source of truth)
        const backendMode = await fetchModeFromBackend();

        if (backendMode) {
          // Backend overrides localStorage
          dispatch({ type: 'INITIALIZE', payload: backendMode });
          localStorage.setItem(STORAGE_KEY, backendMode);
          log.info('Mode initialized from backend', { mode: backendMode });
        } else {
          // Backend failed, use localStorage or default
          const fallbackMode = stored === 'live' ? 'live' : 'training';
          dispatch({ type: 'INITIALIZE', payload: fallbackMode });
          log.info('Mode initialized from localStorage/default', { mode: fallbackMode });
        }
      } catch (error) {
        log.error('Failed to initialize mode', error);
        dispatch({ type: 'INITIALIZE', payload: 'training' });
      }
    }

    initializeMode();
  }, [fetchModeFromBackend]);

  /**
   * Persist mode to localStorage when it changes.
   */
  useEffect(() => {
    if (state.initialized) {
      localStorage.setItem(STORAGE_KEY, state.mode);
      log.debug('Mode persisted to localStorage', { mode: state.mode });
    }
  }, [state.mode, state.initialized]);

  /**
   * Set the application mode.
   * Updates both frontend state and backend persistence.
   */
  const setMode = useCallback(async (mode: ApplicationMode) => {
    if (state.mode === mode) {
      log.debug('Mode already set, skipping', { mode });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      // Save to backend first
      const success = await saveModeToBackend(mode);

      if (success) {
        // Update local state
        dispatch({ type: 'SET_MODE', payload: mode });

        // Announce to screen readers
        const modeLabel = mode === 'training' ? 'Training Mode' : 'Live Scanning Mode';
        announce(`Application mode changed to ${modeLabel}`);

        log.info('Mode changed successfully', { mode });
      }
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.mode, saveModeToBackend, announce]);

  /**
   * Toggle between training and live mode.
   */
  const toggleMode = useCallback(async () => {
    const newMode: ApplicationMode = state.mode === 'training' ? 'live' : 'training';
    await setMode(newMode);
  }, [state.mode, setMode]);

  /**
   * Refresh mode from backend.
   * Useful for syncing after external changes.
   */
  const refreshMode = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const backendMode = await fetchModeFromBackend();
      if (backendMode) {
        dispatch({ type: 'SET_MODE', payload: backendMode });
        log.info('Mode refreshed from backend', { mode: backendMode });
      }
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [fetchModeFromBackend]);

  const value: ModeContextValue = {
    mode: state.mode,
    isLoading: state.isLoading,
    error: state.error,
    setMode,
    toggleMode,
    refreshMode,
  };

  return (
    <ModeContext.Provider value={value}>
      {children}
      {/* Screen reader announcer - hidden live region */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {state.announcements[0] || ''}
      </div>
    </ModeContext.Provider>
  );
}

/**
 * Hook to use mode context.
 * Must be used within a ModeProvider.
 */
export function useMode() {
  const context = useContext(ModeContext);
  if (!context) {
    throw new Error('useMode must be used within a ModeProvider');
  }
  return context;
}
