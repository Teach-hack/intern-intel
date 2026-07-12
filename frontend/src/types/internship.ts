export interface Internship {
  id: number;
  company: string;
  title: string;
  link: string;
  location: string;
  description?: string;
  date_posted?: string;
  source: string;
  is_active: boolean;
  is_remote: boolean;
  employment_type: string;
  created_at: string;
  updated_at: string;
}
