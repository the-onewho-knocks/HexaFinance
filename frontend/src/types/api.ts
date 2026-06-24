export interface ApiResponse<T>{
    data:T
    message?: string
    error?:string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
}

export interface ApiError {
  message: string
  status: number
  errors?: Record<string, string[]>
}