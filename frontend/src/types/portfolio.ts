
export interface Holding {
  id: string
  user_id: string
  symbol: string
  quantity: number
  avg_price: number
  current_price: number
  total_value: number
  total_cost: number
  gain_loss: number
  gain_loss_percent: number
  updated_at: string
}

export interface Portfolio {
  user_id: string
  holdings: Holding[]
  total_value: number
  total_cost: number
  total_gain_loss: number
  total_gain_loss_percent: number
}

export interface PortfolioMetrics {
  total_value: number
  total_cost: number
  total_gain_loss: number
  total_gain_loss_percent: number
  diversification: { symbol: string; allocation: number }[]
  best_performer: { symbol: string; gain_loss_percent: number }
  worst_performer: { symbol: string; gain_loss_percent: number }
}

export interface BuyOrder {
  user_id: string
  symbol: string
  quantity: number
}

export interface SellOrder {
  user_id: string
  symbol: string
  quantity: number
}