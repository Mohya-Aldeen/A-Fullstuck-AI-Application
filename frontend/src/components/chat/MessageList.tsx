import type { UIMessage } from 'ai'
import { useEffect, useRef } from 'react'

import { MessageBubble } from '@/components/chat/MessageBubble'
import type { Citation } from '@/lib/chat'

type MessageListProps = {
  messages: UIMessage[]
  citationsByMessageId: Map<string, Citation[]>
}

export function MessageList({
  messages,
  citationsByMessageId,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

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
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
