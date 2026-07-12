import { Internship } from './internship';

export interface DashboardOverviewStats {
  total_internships: number;
  new_today: number;
  saved_jobs: number;
  companies: number;
}

export interface DashboardCharts {
  source_distribution: Record<string, number>;
}

export interface DashboardRecent {
  internships: Internship[];
}

export interface DashboardPipeline {
  last_run: string | null;
  status: string;
}

export interface DashboardSystem {
  version: string;
  health: string;
}

export interface DashboardResponse {
  overview: DashboardOverviewStats;
  charts: DashboardCharts;
  recent: DashboardRecent;
  pipeline: DashboardPipeline;
  system: DashboardSystem;
}
