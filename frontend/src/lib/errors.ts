import { ApiError } from '@/lib/api'

export function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isNetworkError) {
      return 'Could not reach the backend. Check VITE_API_BASE_URL and CORS (network error).'
    }
    if (error.status === 401) {
      return 'Your session expired. Sign out and sign in again.'
    }
    if (error.status === 403) {
      return 'You do not have access to this conversation.'
    }
    if (error.status === 502) {
      return 'The backend could not reach Supabase or complete retrieval. Try again shortly.'
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

  if (message.includes('401') || message.includes('unauthorized')) {
    return 'Your session expired. Sign out and sign in again.'
  }
  if (message.includes('502') || message.includes('bad gateway')) {
    return 'Retrieval or persistence failed on the server. Try again or rephrase your question.'
  }
  if (
    message.includes('grounded answer') ||
    message.includes('grounding')
  ) {
    return 'The assistant could not validate citations for this answer. Try a narrower question.'
  }

  return error.message || 'Something went wrong while streaming the response.'
}
