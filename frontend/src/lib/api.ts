import { request, type HttpRequestOptions } from '@/lib/http'

export { ApiError } from '@/lib/http'

type RequestExtras = Omit<HttpRequestOptions, 'method' | 'body'>

export const api = {
  get<T>(path: string, options?: RequestExtras): Promise<T> {
    return request<T>(path, { ...options, method: 'GET' })
  },
  post<T>(path: string, body?: unknown, options?: RequestExtras): Promise<T> {
    return request<T>(path, { ...options, method: 'POST', body })
  },
  put<T>(path: string, body?: unknown, options?: RequestExtras): Promise<T> {
    return request<T>(path, { ...options, method: 'PUT', body })
  },
  patch<T>(path: string, body?: unknown, options?: RequestExtras): Promise<T> {
    return request<T>(path, { ...options, method: 'PATCH', body })
  },
  delete<T>(path: string, options?: RequestExtras): Promise<T> {
    return request<T>(path, { ...options, method: 'DELETE' })
  },
}
