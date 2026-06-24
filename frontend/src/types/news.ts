export interface NewsArticle {
  id: string
  title: string
  summary: string
  url: string
  source: string
  sentiment: 'positive' | 'negative' | 'neutral'
  sentiment_score: number
  symbols: string[]
  categories: string[]
  published_at: string
}