import { logger } from '../monitoring/logger';
import { featureFlags } from '../constants/featureFlags';

export const analytics = {
  track: (eventName: string, properties?: Record<string, unknown>) => {
    if (!featureFlags.ENABLE_ANALYTICS) return;
    // Future: send to Google Analytics, PostHog, Mixpanel, etc.
    logger.info(`[Analytics Track] ${eventName}`, properties);
  },
  identify: (userId: string, traits?: Record<string, unknown>) => {
    if (!featureFlags.ENABLE_ANALYTICS) return;
    logger.info(`[Analytics Identify] User: ${userId}`, traits);
  },
  page: (pageName: string, properties?: Record<string, unknown>) => {
    if (!featureFlags.ENABLE_ANALYTICS) return;
    logger.info(`[Analytics Page View] ${pageName}`, properties);
  },
};
