export interface User {
  id: number;
  username: string;
  email: string;
  role: 'ADMIN' | 'USER';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
