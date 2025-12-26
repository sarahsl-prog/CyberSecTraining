import { createContext, useContext, ReactNode } from 'react';
import { useAccessibility, ColorMode } from './AccessibilityContext';

// Theme tokens that can be used throughout the app
interface ThemeTokens {
  colors: {
    // Semantic colors
    background: string;
    foreground: string;
    primary: string;
    primaryForeground: string;
    secondary: string;
    secondaryForeground: string;
    muted: string;
    mutedForeground: string;
    accent: string;
    accentForeground: string;
    destructive: string;
    destructiveForeground: string;
    border: string;
    ring: string;

    // Severity colors (colorblind-safe)
    severityCritical: string;
    severityHigh: string;
    severityMedium: string;
    severityLow: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  fontWeight: {
    normal: number;
    medium: number;
    semibold: number;
    bold: number;
  };
  transition: {
    fast: string;
    normal: string;
    slow: string;
  };
}

// Theme context value
interface ThemeContextValue {
  colorMode: ColorMode;
  tokens: ThemeTokens;
  isDark: boolean;
  isHighContrast: boolean;
  isColorblindMode: boolean;
}

// Default theme tokens (CSS custom property references)
const defaultTokens: ThemeTokens = {
  colors: {
    background: 'var(--color-background)',
    foreground: 'var(--color-foreground)',
    primary: 'var(--color-primary)',
    primaryForeground: 'var(--color-primary-foreground)',
    secondary: 'var(--color-secondary)',
    secondaryForeground: 'var(--color-secondary-foreground)',
    muted: 'var(--color-muted)',
    mutedForeground: 'var(--color-muted-foreground)',
    accent: 'var(--color-accent)',
    accentForeground: 'var(--color-accent-foreground)',
    destructive: 'var(--color-destructive)',
    destructiveForeground: 'var(--color-destructive-foreground)',
    border: 'var(--color-border)',
    ring: 'var(--color-ring)',
    severityCritical: 'var(--color-severity-critical)',
    severityHigh: 'var(--color-severity-high)',
    severityMedium: 'var(--color-severity-medium)',
    severityLow: 'var(--color-severity-low)',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    full: '9999px',
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  transition: {
    fast: '150ms ease',
    normal: '200ms ease',
    slow: '300ms ease',
  },
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const { state } = useAccessibility();
  const { colorMode } = state;

  const isDark = colorMode === 'dark';
  const isHighContrast = colorMode === 'high-contrast';
  const isColorblindMode = ['protanopia', 'deuteranopia', 'tritanopia'].includes(colorMode);

  const value: ThemeContextValue = {
    colorMode,
    tokens: defaultTokens,
    isDark,
    isHighContrast,
    isColorblindMode,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
