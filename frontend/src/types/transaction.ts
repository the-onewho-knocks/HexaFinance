export interface Transaction {
  id: string
  user_id: string
  symbol: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  total: number
  timestamp: string
}

export interface TransactionFilters {
  type?: 'buy' | 'sell'
  symbol?: string
  start_date?: string
  end_date?: string
  page?: number
  limit?: number
}