import { apiClient } from '../lib/axios';
import { User } from '../types/user';
import { Internship } from '../types/internship';

// Create a local type until we unify it
export interface SavedJobResponse {
  id: number;
  user_id: number;
  internship_id: number;
  notes: string | null;
  created_at: string;
  internship: Internship;
}

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
  
  // Saved Jobs
  getSavedJobs: async (params?: { skip?: number; limit?: number }) => {
    const response = await apiClient.get<SavedJobResponse[]>('/users/me/saved-jobs', { params });
    return response.data;
  },
  saveJob: async (internshipId: number) => {
    const response = await apiClient.post<SavedJobResponse>(`/users/me/saved-jobs/${internshipId}`);
    return response.data;
  },
  removeSavedJob: async (internshipId: number) => {
    const response = await apiClient.delete(`/users/me/saved-jobs/${internshipId}`);
    return response.data;
  }
};
