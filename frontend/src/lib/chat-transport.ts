import { DefaultChatTransport, type UIMessage } from 'ai'

import { env } from '@/lib/env'
import { getAccessToken } from '@/lib/supabase'

export function createChatTransport() {
  return new DefaultChatTransport<UIMessage>({
    api: `${env.apiBaseUrl}/chat/stream`,
    headers: async () => {
      const token = await getAccessToken()
      if (!token) return {}
      return { Authorization: `Bearer ${token}` }
    },
    prepareSendMessagesRequest: ({ id, messages }) => ({
      body: {
        threadId: id,
        messages,
      },
    }),
  })
}
