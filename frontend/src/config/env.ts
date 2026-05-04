export const env = {
  useMock: (import.meta.env.VITE_USE_MOCK ?? 'true') === 'true',
  apiUrl: (import.meta.env.VITE_API_URL ?? '') as string,
  userPoolId: (import.meta.env.VITE_USER_POOL_ID ?? '') as string,
  userPoolClientId: (import.meta.env.VITE_USER_POOL_CLIENT_ID ?? '') as string,
  awsRegion: (import.meta.env.VITE_AWS_REGION ?? 'us-east-1') as string,
};
