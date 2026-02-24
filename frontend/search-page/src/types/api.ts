export interface ErrorResponse {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
    request_id?: string
  }
}

export interface ApiResponse<T> {
  data: T
  status: number
  request_id?: string
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  service: string
  version: string
  uptime_seconds: number
  timestamp: string
  dependencies: Record<string, { status: string; latency_ms: number }>
}
