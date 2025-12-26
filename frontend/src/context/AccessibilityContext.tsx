import { createContext, useContext, useReducer, useEffect, useCallback, ReactNode } from 'react';

// Color mode options including colorblind-friendly modes
export type ColorMode =
  | 'light'
  | 'dark'
  | 'high-contrast'
  | 'protanopia'
  | 'deuteranopia'
  | 'tritanopia';

// Accessibility settings state
export interface AccessibilityState {
  // Color and visual settings
  colorMode: ColorMode;
  fontSize: number; // 100 to 200 (percentage)

  // Motion settings
  reduceMotion: boolean;

  // Screen reader settings
  screenReaderOptimized: boolean;
  announcements: string[];

  // Focus settings
  showFocusIndicator: boolean;

  // Initialization
  initialized: boolean;
}

// Actions for accessibility reducer
type AccessibilityAction =
  | { type: 'SET_COLOR_MODE'; payload: ColorMode }
  | { type: 'SET_FONT_SIZE'; payload: number }
  | { type: 'SET_REDUCE_MOTION'; payload: boolean }
  | { type: 'SET_SCREEN_READER_OPTIMIZED'; payload: boolean }
  | { type: 'SET_SHOW_FOCUS_INDICATOR'; payload: boolean }
  | { type: 'ANNOUNCE'; payload: string }
  | { type: 'CLEAR_ANNOUNCEMENT' }
  | { type: 'LOAD_PREFERENCES'; payload: Partial<AccessibilityState> }
  | { type: 'RESET_TO_DEFAULTS' };

// Default state
const defaultState: AccessibilityState = {
  colorMode: 'light',
  fontSize: 100,
  reduceMotion: false,
  screenReaderOptimized: false,
  announcements: [],
  showFocusIndicator: true,
  initialized: false,
};

// Storage key for persisting preferences
const STORAGE_KEY = 'cybersec-accessibility-preferences';

// Reducer function
function accessibilityReducer(
  state: AccessibilityState,
  action: AccessibilityAction
): AccessibilityState {
  switch (action.type) {
    case 'SET_COLOR_MODE':
      return { ...state, colorMode: action.payload };
    case 'SET_FONT_SIZE':
      return { ...state, fontSize: Math.min(200, Math.max(100, action.payload)) };
    case 'SET_REDUCE_MOTION':
      return { ...state, reduceMotion: action.payload };
    case 'SET_SCREEN_READER_OPTIMIZED':
      return { ...state, screenReaderOptimized: action.payload };
    case 'SET_SHOW_FOCUS_INDICATOR':
      return { ...state, showFocusIndicator: action.payload };
    case 'ANNOUNCE':
      return { ...state, announcements: [...state.announcements, action.payload] };
    case 'CLEAR_ANNOUNCEMENT':
      return { ...state, announcements: state.announcements.slice(1) };
    case 'LOAD_PREFERENCES':
      return { ...state, ...action.payload, initialized: true };
    case 'RESET_TO_DEFAULTS':
      return { ...defaultState, initialized: true };
    default:
      return state;
  }
}

// Context value interface
interface AccessibilityContextValue {
  state: AccessibilityState;
  setColorMode: (mode: ColorMode) => void;
  setFontSize: (size: number) => void;
  setReduceMotion: (reduce: boolean) => void;
  setScreenReaderOptimized: (optimized: boolean) => void;
  setShowFocusIndicator: (show: boolean) => void;
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
  resetToDefaults: () => void;
}

// Create context
const AccessibilityContext = createContext<AccessibilityContextValue | null>(null);

// Provider component
export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(accessibilityReducer, defaultState);

  // Load preferences from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const preferences = JSON.parse(stored);
        dispatch({ type: 'LOAD_PREFERENCES', payload: preferences });
      } else {
        // Check system preferences
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        dispatch({
          type: 'LOAD_PREFERENCES',
          payload: {
            colorMode: prefersDark ? 'dark' : 'light',
            reduceMotion: prefersReducedMotion,
          },
        });
      }
    } catch (error) {
      console.error('Failed to load accessibility preferences:', error);
      dispatch({ type: 'LOAD_PREFERENCES', payload: {} });
    }
  }, []);

  // Save preferences to localStorage when they change
  useEffect(() => {
    if (state.initialized) {
      const { announcements, initialized, ...preferencesToSave } = state;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferencesToSave));
    }
  }, [state]);

  // Apply color mode to document
  useEffect(() => {
    document.documentElement.setAttribute('data-color-mode', state.colorMode);
  }, [state.colorMode]);

  // Apply font size to document
  useEffect(() => {
    document.documentElement.style.fontSize = `${state.fontSize}%`;
  }, [state.fontSize]);

  // Apply reduced motion preference
  useEffect(() => {
    if (state.reduceMotion) {
      document.documentElement.classList.add('reduce-motion');
    } else {
      document.documentElement.classList.remove('reduce-motion');
    }
  }, [state.reduceMotion]);

  // Apply focus indicator preference
  useEffect(() => {
    if (state.showFocusIndicator) {
      document.documentElement.classList.remove('hide-focus-indicator');
    } else {
      document.documentElement.classList.add('hide-focus-indicator');
    }
  }, [state.showFocusIndicator]);

  // Action creators
  const setColorMode = useCallback((mode: ColorMode) => {
    dispatch({ type: 'SET_COLOR_MODE', payload: mode });
  }, []);

  const setFontSize = useCallback((size: number) => {
    dispatch({ type: 'SET_FONT_SIZE', payload: size });
  }, []);

  const setReduceMotion = useCallback((reduce: boolean) => {
    dispatch({ type: 'SET_REDUCE_MOTION', payload: reduce });
  }, []);

  const setScreenReaderOptimized = useCallback((optimized: boolean) => {
    dispatch({ type: 'SET_SCREEN_READER_OPTIMIZED', payload: optimized });
  }, []);

  const setShowFocusIndicator = useCallback((show: boolean) => {
    dispatch({ type: 'SET_SHOW_FOCUS_INDICATOR', payload: show });
  }, []);

  const announce = useCallback((message: string, _priority: 'polite' | 'assertive' = 'polite') => {
    // Note: priority is accepted for future ARIA live region support
    dispatch({ type: 'ANNOUNCE', payload: message });
    // Clear announcement after screen reader has time to read it
    setTimeout(() => {
      dispatch({ type: 'CLEAR_ANNOUNCEMENT' });
    }, 1000);
  }, []);

  const resetToDefaults = useCallback(() => {
    dispatch({ type: 'RESET_TO_DEFAULTS' });
  }, []);

  const value: AccessibilityContextValue = {
    state,
    setColorMode,
    setFontSize,
    setReduceMotion,
    setScreenReaderOptimized,
    setShowFocusIndicator,
    announce,
    resetToDefaults,
  };

  return (
    <AccessibilityContext.Provider value={value}>
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
    </AccessibilityContext.Provider>
  );
}

// Hook to use accessibility context
export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
}
