import { useChat } from '@ai-sdk/react'
import type { UIMessage } from 'ai'
import { useMemo, useState } from 'react'

import { ChatInput } from '@/components/chat/ChatInput'
import { ChatStatusBar } from '@/components/chat/ChatStatusBar'
import { EmptyState } from '@/components/chat/EmptyState'
import { MessageList } from '@/components/chat/MessageList'
import { SourcePassagePanel } from '@/components/chat/SourcePassagePanel'
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
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)

  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    messages: initialMessages,
    transport,
    onFinish: () => {
      void chatApi.listMessages(threadId).then((stored) => {
        setCitationsByMessageId(buildCitationsByMessageId(stored))
        setSelectedCitation((current) => {
          if (!current) return null
          const refreshed = stored
            .flatMap((message) => message.citations)
            .find((citation) => citation.id === current.id)
          return refreshed ?? null
        })
      })
      onThreadActivity?.()
    },
  })

  const errorMessage = error ? formatChatError(error) : null
  const isBusy = status === 'submitted' || status === 'streaming'

  function handleSelectCitation(citation: Citation) {
    setSelectedCitation((current) =>
      current?.id === citation.id ? null : citation,
    )
  }

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-row">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="border-b border-border px-4 py-3">
          <h2 className="truncate text-sm font-medium">{threadTitle}</h2>
        </header>

        {messages.length === 0 ? (
          <EmptyState
            title="Ask about the filings"
            description="Ask about Apple, Amazon, Alphabet, Microsoft, and NVIDIA 10-Ks in the corpus. Answers cite retrieved filing passages — click a source chip to verify."
          />
        ) : (
          <MessageList
            messages={messages}
            citationsByMessageId={citationsByMessageId}
            selectedCitationId={selectedCitation?.id ?? null}
            onSelectCitation={handleSelectCitation}
            chatStatus={status}
          />
        )}

        <ChatStatusBar status={status} errorMessage={errorMessage} />

        <ChatInput
          disabled={isBusy}
          onSubmit={(text) => {
            setSelectedCitation(null)
            void sendMessage({ text })
          }}
        />
      </div>

      <SourcePassagePanel
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </section>
  )
}
