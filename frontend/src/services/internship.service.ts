import { apiClient } from '../lib/axios';
import { PaginatedResponse as PaginatedResponseType } from '../types/api';
import { Internship as InternshipType } from '../types/internship';

export const internshipService = {
  getInternships: async (params: Record<string, string | number | boolean>) => {
    const response = await apiClient.get<PaginatedResponseType<InternshipType>>('/internships', { params });
    return response.data;
  },
  getInternship: async (id: number) => {
    const response = await apiClient.get<InternshipType>(`/internships/${id}`);
    return response.data;
  },
};
