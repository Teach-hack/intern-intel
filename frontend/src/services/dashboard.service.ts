import { apiClient } from '../lib/axios';
import { DashboardResponse } from '../types/dashboard';

export const dashboardService = {
  getOverview: async () => {
    const response = await apiClient.get<DashboardResponse>('/dashboard');
    return response.data;
  },
};
