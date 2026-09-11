import { useChat } from '@ai-sdk/react'
import type { UIMessage } from 'ai'
import { useMemo, useState } from 'react'

import { ChatInput } from '@/components/chat/ChatInput'
import { ChatStatusBar } from '@/components/chat/ChatStatusBar'
import { EmptyState } from '@/components/chat/EmptyState'
import { MessageList } from '@/components/chat/MessageList'
import type { Citation } from '@/lib/chat'
import { buildCitationsByMessageId, chatApi } from '@/lib/chat'
import { createChatTransport } from '@/lib/chat-transport'
import { formatChatError } from '@/lib/errors'

type ChatPaneProps = {
  threadId: string
  threadTitle: string
  initialMessages: UIMessage[]
  initialCitations: Map<string, Citation[]>
  onThreadActivity?: () => void
}

export function ChatPane({
  threadId,
  threadTitle,
  initialMessages,
  initialCitations,
  onThreadActivity,
}: ChatPaneProps) {
  const transport = useMemo(() => createChatTransport(), [])
  const [citationsByMessageId, setCitationsByMessageId] =
    useState(initialCitations)

  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    messages: initialMessages,
    transport,
    onFinish: () => {
      void chatApi.listMessages(threadId).then((stored) => {
        setCitationsByMessageId(buildCitationsByMessageId(stored))
      })
      onThreadActivity?.()
    },
  })

  const errorMessage = error ? formatChatError(error) : null
  const isBusy = status === 'submitted' || status === 'streaming'

  return (
    <section className="flex min-w-0 flex-1 flex-col">
      <header className="border-b border-border px-4 py-3">
        <h2 className="truncate text-sm font-medium">{threadTitle}</h2>
      </header>

      {messages.length === 0 ? (
        <EmptyState
          title="Ask about the filings"
          description="Document Copilot answers from ingested SEC filings with citations. Retrieval is not wired yet, but streaming and persistence are live."
        />
      ) : (
        <MessageList
          messages={messages}
          citationsByMessageId={citationsByMessageId}
        />
      )}

      <ChatStatusBar status={status} errorMessage={errorMessage} />

      <ChatInput
        disabled={isBusy}
        onSubmit={(text) => {
          void sendMessage({ text })
        }}
      />
    </section>
  )
}
