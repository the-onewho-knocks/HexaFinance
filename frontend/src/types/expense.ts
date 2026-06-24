export interface Expense {
  id: string
  user_id: string
  category: string
  amount: number
  description: string
  date: string
  created_at: string
}

export interface PlannedExpense {
  id: string
  user_id: string
  category: string
  amount: number
  description: string
  target_date: string
  is_recurring: boolean
  created_at: string
}