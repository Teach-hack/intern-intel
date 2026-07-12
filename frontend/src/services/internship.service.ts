import { apiClient } from '../lib/axios';
import { Internship as InternshipType } from '../types/internship';

export const internshipService = {
  getInternships: async (params: Record<string, string | number | boolean>) => {
    const response = await apiClient.get<InternshipType[]>('/internships', { params });
    return response.data;
  },
  getInternship: async (id: number) => {
    const response = await apiClient.get<InternshipType>(`/internships/${id}`);
    return response.data;
  },
};
