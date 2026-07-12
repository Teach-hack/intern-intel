import { User } from './user';

export interface AuthTokens {
  access_token: string;
  refresh_token?: string; // Sometimes provided, but typically we rely on BFF to handle this
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface SessionContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: AuthResponse) => void;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}
