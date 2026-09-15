import type { ChatStatus, UIMessage } from 'ai'
import { useEffect, useRef } from 'react'

import { MessageBubble } from '@/components/chat/MessageBubble'
import type { Citation } from '@/lib/chat'

type MessageListProps = {
  messages: UIMessage[]
  citationsByMessageId: Map<string, Citation[]>
  selectedCitationId: string | null
  onSelectCitation: (citation: Citation) => void
  chatStatus: ChatStatus
}

export function MessageList({
  messages,
  citationsByMessageId,
  selectedCitationId,
  onSelectCitation,
  chatStatus,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const lastMessageId = messages.at(-1)?.id
  const awaitingSources =
    chatStatus === 'streaming' || chatStatus === 'submitted'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-6">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          citations={citationsByMessageId.get(message.id)}
          selectedCitationId={selectedCitationId}
          onSelectCitation={onSelectCitation}
          hideMissingCitationHint={
            message.id === lastMessageId && awaitingSources
          }
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
