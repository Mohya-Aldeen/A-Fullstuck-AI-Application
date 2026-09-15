import { useChat } from '@ai-sdk/react'
import type { UIMessage } from 'ai'
import { useEffect, useMemo, useRef, useState } from 'react'

import { Composer } from '@/components/chat/Composer'
import { EvidencePanel } from '@/components/chat/EvidencePanel'
import { MessageList } from '@/components/chat/MessageList'
import { ResearchStart } from '@/components/chat/ResearchStart'
import { RetrievalStatus } from '@/components/chat/RetrievalStatus'
import type { Citation } from '@/lib/chat'
import { buildCitationsByMessageId, chatApi } from '@/lib/chat'
import { createChatTransport } from '@/lib/chat-transport'
import { formatChatError } from '@/lib/errors'

type ChatPaneProps = {
  threadId: string
  threadTitle: string
  initialMessages: UIMessage[]
  initialCitations: Map<string, Citation[]>
  pendingPrompt?: string | null
  onPromptConsumed?: () => void
  onThreadActivity?: () => void
}

export function ChatPane({
  threadId,
  threadTitle,
  initialMessages,
  initialCitations,
  pendingPrompt,
  onPromptConsumed,
  onThreadActivity,
}: ChatPaneProps) {
  const transport = useMemo(() => createChatTransport(), [])
  const [citationsByMessageId, setCitationsByMessageId] =
    useState(initialCitations)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const sentPromptRef = useRef(false)

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

  // Auto-send a starter prompt handed off from the home screen (once).
  useEffect(() => {
    if (!pendingPrompt || sentPromptRef.current) return
    if (messages.length > 0) {
      sentPromptRef.current = true
      onPromptConsumed?.()
      return
    }
    if (status !== 'ready') return
    sentPromptRef.current = true
    void sendMessage({ text: pendingPrompt })
    onPromptConsumed?.()
  }, [pendingPrompt, status, messages.length, sendMessage, onPromptConsumed])

  // Escape closes the source panel.
  useEffect(() => {
    if (!selectedCitation) return
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setSelectedCitation(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selectedCitation])

  function handleSelectCitation(citation: Citation) {
    setSelectedCitation((current) =>
      current?.id === citation.id ? null : citation,
    )
  }

  function handleSubmit(text: string) {
    setSelectedCitation(null)
    void sendMessage({ text })
  }

  return (
    <section className="flex min-h-0 flex-1 overflow-hidden">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-rule px-6 py-3">
          <h1 className="truncate text-sm font-medium text-foreground">
            {threadTitle}
          </h1>
          <span className="hidden shrink-0 text-[0.7rem] text-muted-foreground tabular sm:block">
            10-K filings, FY2021–FY2025
          </span>
        </header>

        {messages.length === 0 ? (
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain">
            <ResearchStart busy={isBusy} onSelectPrompt={handleSubmit} />
          </div>
        ) : (
          <MessageList
            messages={messages}
            citationsByMessageId={citationsByMessageId}
            selectedCitationId={selectedCitation?.id ?? null}
            onSelectCitation={handleSelectCitation}
            chatStatus={status}
          />
        )}

        <div className="shrink-0">
          <RetrievalStatus status={status} errorMessage={errorMessage} />
          <Composer disabled={isBusy} onSubmit={handleSubmit} />
        </div>
      </div>

      <EvidencePanel
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </section>
  )
}
