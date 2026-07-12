import { logger } from './logger';

export const errorReporter = {
  report: (error: unknown, context?: Record<string, unknown>) => {
    // Future: send to Sentry, LogRocket, etc.
    logger.error('Error reported:', error, context);
  },
  setUser: (id: string, email: string) => {
    // Future: identify user in error reporting tool
    logger.debug('Error reporter user set:', { id, email });
  },
  clearUser: () => {
    // Future: clear user in error reporting tool
    logger.debug('Error reporter user cleared');
  },
};
