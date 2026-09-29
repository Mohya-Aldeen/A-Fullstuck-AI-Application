import { DefaultChatTransport, type UIMessage } from 'ai'

import { env } from '@/lib/env'
import { getAccessToken } from '@/lib/supabase'

export function createChatTransport() {
  return new DefaultChatTransport<UIMessage>({
    api: `${env.apiBaseUrl}/chat/stream`,
    headers: async () => {
      const token = await getAccessToken()
      const headers: Record<string, string> = {}
      if (token) headers.Authorization = `Bearer ${token}`
      return headers
    },
    prepareSendMessagesRequest: ({ id, messages }) => ({
      body: {
        threadId: id,
        messages,
      },
    }),
  })
}
