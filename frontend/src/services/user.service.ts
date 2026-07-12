import { apiClient } from '../lib/axios';
import { User } from '../types/user';

export const userService = {
  getUsers: async (params?: { skip?: number; limit?: number }) => {
    const response = await apiClient.get<User[]>('/admin/users', { params });
    return response.data;
  },
  updateUserRole: async (id: number, role: string) => {
    const response = await apiClient.patch<User>(`/admin/users/${id}`, { role });
    return response.data;
  },
  deleteUser: async (id: number) => {
    const response = await apiClient.delete(`/admin/users/${id}`);
    return response.data;
  },
};
