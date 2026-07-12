export const queryKeys = {
  auth: {
    me: ['auth', 'me'],
  },
  internships: {
    all: ['internships'] as const,
    list: (filters: Record<string, unknown>) => [...queryKeys.internships.all, 'list', filters] as const,
    detail: (id: number) => ['internships', 'detail', id],
  },
  admin: {
    users: ['admin', 'users'],
    pipeline: ['admin', 'pipeline'],
    health: ['admin', 'health'],
  },
};
