/**
 * Frontend logging utility.
 *
 * Provides a consistent logging interface that mirrors the backend logging
 * patterns. Supports different log levels, module contexts, and optional
 * remote log shipping for production environments.
 */

/**
 * Log levels in order of severity.
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4,
}

/**
 * Configuration options for the logger.
 */
interface LoggerConfig {
  /** Minimum log level to output */
  minLevel: LogLevel;
  /** Whether to include timestamps */
  includeTimestamp: boolean;
  /** Whether to include module name */
  includeModule: boolean;
  /** Whether to send logs to backend (future feature) */
  remoteLogging: boolean;
}

/**
 * Default logger configuration.
 */
const defaultConfig: LoggerConfig = {
  minLevel: import.meta.env.DEV ? LogLevel.DEBUG : LogLevel.INFO,
  includeTimestamp: true,
  includeModule: true,
  remoteLogging: false,
};

/**
 * Current logger configuration.
 */
let config: LoggerConfig = { ...defaultConfig };

/**
 * Format a log message with timestamp and module context.
 *
 * @param level - Log level string
 * @param module - Module name
 * @param message - Log message
 * @returns Formatted log string
 */
function formatMessage(level: string, module: string, message: string): string {
  const parts: string[] = [];

  if (config.includeTimestamp) {
    const now = new Date().toISOString();
    parts.push(`[${now}]`);
  }

  parts.push(`[${level.toUpperCase().padEnd(5)}]`);

  if (config.includeModule && module) {
    parts.push(`[${module}]`);
  }

  parts.push(message);

  return parts.join(' ');
}

/**
 * Create a logger instance for a specific module.
 *
 * Usage:
 * ```ts
 * const log = logger.create('NetworkService');
 * log.info('Starting scan...');
 * log.debug('Scan params:', { target, scanType });
 * ```
 *
 * @param module - Module name for log context
 * @returns Logger instance with bound module name
 */
function createLogger(module: string) {
  return {
    /**
     * Log a debug message.
     * Only visible in development mode.
     */
    debug(message: string, ...args: unknown[]): void {
      if (config.minLevel <= LogLevel.DEBUG) {
        console.debug(formatMessage('DEBUG', module, message), ...args);
      }
    },

    /**
     * Log an info message.
     */
    info(message: string, ...args: unknown[]): void {
      if (config.minLevel <= LogLevel.INFO) {
        console.info(formatMessage('INFO', module, message), ...args);
      }
    },

    /**
     * Log a warning message.
     */
    warn(message: string, ...args: unknown[]): void {
      if (config.minLevel <= LogLevel.WARN) {
        console.warn(formatMessage('WARN', module, message), ...args);
      }
    },

    /**
     * Log an error message.
     */
    error(message: string, ...args: unknown[]): void {
      if (config.minLevel <= LogLevel.ERROR) {
        console.error(formatMessage('ERROR', module, message), ...args);
      }
    },

    /**
     * Log with explicit level.
     */
    log(level: LogLevel, message: string, ...args: unknown[]): void {
      if (config.minLevel <= level) {
        const levelName = LogLevel[level];
        switch (level) {
          case LogLevel.DEBUG:
            console.debug(formatMessage(levelName, module, message), ...args);
            break;
          case LogLevel.INFO:
            console.info(formatMessage(levelName, module, message), ...args);
            break;
          case LogLevel.WARN:
            console.warn(formatMessage(levelName, module, message), ...args);
            break;
          case LogLevel.ERROR:
            console.error(formatMessage(levelName, module, message), ...args);
            break;
        }
      }
    },

    /**
     * Create a child logger with additional context.
     */
    child(childModule: string) {
      return createLogger(`${module}:${childModule}`);
    },
  };
}

/**
 * Logger factory and configuration.
 */
export const logger = {
  /**
   * Create a logger instance for a module.
   */
  create: createLogger,

  /**
   * Update logger configuration.
   */
  configure(newConfig: Partial<LoggerConfig>): void {
    config = { ...config, ...newConfig };
  },

  /**
   * Set the minimum log level.
   */
  setLevel(level: LogLevel): void {
    config.minLevel = level;
  },

  /**
   * Get the current log level.
   */
  getLevel(): LogLevel {
    return config.minLevel;
  },

  /**
   * Reset to default configuration.
   */
  reset(): void {
    config = { ...defaultConfig };
  },
};
