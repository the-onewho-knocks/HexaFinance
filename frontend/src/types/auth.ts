export interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
  fake_balance: number
  created_at: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface GoogleLoginPayload {
  credential: string
  client_id: string
}