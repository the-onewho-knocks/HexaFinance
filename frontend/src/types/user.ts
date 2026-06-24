export interface UserProfile {
  id: string
  email: string
  name: string
  avatar_url: string | null
  fake_balance: number
  created_at: string
  updated_at: string
}

export interface UpdateProfilePayload {
  name?: string
  avatar_url?: string
}

export interface BalanceAction {
  amount: number
}