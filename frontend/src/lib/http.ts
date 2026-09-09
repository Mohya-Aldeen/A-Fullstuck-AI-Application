import { env } from '@/lib/env'
import { getAccessToken } from '@/lib/supabase'

const DEFAULT_TIMEOUT_MS = 30_000

export class ApiError extends Error {
  readonly status: number
  readonly isNetworkError: boolean
  readonly body: unknown

  constructor(
    message: string,
    options: { status: number; isNetworkError: boolean; body?: unknown },
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.isNetworkError = options.isNetworkError
    this.body = options.body ?? null
  }
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export type HttpRequestOptions = {
  method?: HttpMethod
  body?: unknown
  headers?: Record<string, string>
  timeoutMs?: number
  signal?: AbortSignal
}

export async function request<T>(
  path: string,
  options: HttpRequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...options.headers,
  }
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const token = await getAccessToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const { signal, cleanup } = timeoutSignal(
    options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
    options.signal,
  )

  let response: Response
  try {
    response = await fetch(apiUrl(path), {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal,
    })
  } catch (error) {
    cleanup()
    throw toNetworkError(error)
  }
  cleanup()

  const body = await readBody(response)
  if (!response.ok) {
    throw new ApiError(messageFromBody(body, response), {
      status: response.status,
      isNetworkError: false,
      body,
    })
  }

  return body as T
}

function apiUrl(path: string): string {
  const suffix = path.startsWith('/') ? path : `/${path}`
  return `${env.apiBaseUrl}${suffix}`
}

function timeoutSignal(
  timeoutMs: number,
  parent?: AbortSignal,
): { signal: AbortSignal; cleanup: () => void } {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  const onParentAbort = () => controller.abort()

  if (parent) {
    if (parent.aborted) controller.abort()
    else parent.addEventListener('abort', onParentAbort)
  }

  return {
    signal: controller.signal,
    cleanup() {
      clearTimeout(timer)
      parent?.removeEventListener('abort', onParentAbort)
    },
  }
}

function toNetworkError(error: unknown): ApiError {
  const timedOut = error instanceof DOMException && error.name === 'AbortError'
  return new ApiError(timedOut ? 'Request timed out' : 'Network request failed', {
    status: 0,
    isNetworkError: true,
  })
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (text === '') return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function messageFromBody(body: unknown, response: Response): string {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const detail = body.detail
    if (typeof detail === 'string' && detail.length > 0) return detail
  }
  return `${response.status} ${response.statusText}`
}
