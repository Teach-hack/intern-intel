export const featureFlags = {
  ENABLE_ADMIN: process.env.NEXT_PUBLIC_ENABLE_ADMIN === 'true',
  ENABLE_ANALYTICS: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
  ENABLE_NOTIFICATIONS: process.env.NEXT_PUBLIC_ENABLE_NOTIFICATIONS === 'true',
  ENABLE_RESUME_AI: process.env.NEXT_PUBLIC_ENABLE_RESUME_AI === 'true',
  ENABLE_PWA: process.env.NEXT_PUBLIC_ENABLE_PWA === 'true',
};
