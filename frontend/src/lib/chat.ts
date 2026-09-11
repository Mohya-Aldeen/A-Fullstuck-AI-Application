import type { UIMessage } from 'ai'

import { api } from '@/lib/api'

export type Thread = {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type Citation = {
  id: string
  chunk_id: string
  citation_index: number
  excerpt: string | null
  page_label: string | null
}

export type StoredMessage = {
  id: string
  role: string
  ui_message: Record<string, unknown>
  sequence: number
  created_at: string
  citations: Citation[]
}

export const chatApi = {
  listThreads(): Promise<Thread[]> {
    return api.get<Thread[]>('/chat/threads')
  },

  createThread(title = 'New chat'): Promise<Thread> {
    return api.post<Thread>('/chat/threads', { title })
  },

  listMessages(threadId: string): Promise<StoredMessage[]> {
    return api.get<StoredMessage[]>(`/chat/threads/${threadId}/messages`)
  },
}

export function storedMessageToUiMessage(stored: StoredMessage): UIMessage {
  const raw = stored.ui_message
  const parts = Array.isArray(raw.parts) ? raw.parts : []
  const role = raw.role

  if (role !== 'user' && role !== 'assistant' && role !== 'system') {
    throw new Error(`Unsupported message role: ${String(role)}`)
  }

  return {
    id: typeof raw.id === 'string' ? raw.id : stored.id,
    role,
    parts,
  } as UIMessage
}

export function buildCitationsByMessageId(
  messages: StoredMessage[],
): Map<string, Citation[]> {
  const map = new Map<string, Citation[]>()
  for (const message of messages) {
    if (message.citations.length > 0) {
      map.set(message.id, message.citations)
    }
  }
  return map
}
