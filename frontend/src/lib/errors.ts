import { ApiError } from '@/lib/api'

export function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isNetworkError) {
      return 'Could not reach the backend. Is it running on VITE_API_BASE_URL?'
    }
    return error.message
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'Something went wrong'
}

export function formatChatError(error: Error): string {
  try {
    const parsed = JSON.parse(error.message) as { detail?: unknown }
    if (typeof parsed.detail === 'string' && parsed.detail.length > 0) {
      return parsed.detail
    }
  } catch {
    // FastAPI errors are not always JSON strings.
  }

  const message = error.message.toLowerCase()
  if (
    message.includes('failed to fetch') ||
    message.includes('network') ||
    message.includes('load failed')
  ) {
    return 'Could not reach the backend while streaming. Check that it is running and CORS allows this origin.'
  }

  return error.message || 'Something went wrong while streaming the response.'
}
