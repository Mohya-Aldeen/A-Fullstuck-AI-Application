import type { ChatStatus, UIMessage } from 'ai'
import { isTextUIPart } from 'ai'
import { useEffect, useRef } from 'react'

import { AnswerNote } from '@/components/chat/AnswerNote'
import { QuestionBlock } from '@/components/chat/QuestionBlock'
import type { Citation } from '@/lib/chat'
import { cn } from '@/lib/utils'

type MessageListProps = {
  messages: UIMessage[]
  citationsByMessageId: Map<string, Citation[]>
  selectedCitationId: string | null
  onSelectCitation: (citation: Citation) => void
  chatStatus: ChatStatus
}

function messageText(message: UIMessage): string {
  return message.parts
    .flatMap((part) => (isTextUIPart(part) ? [part.text] : []))
    .join('\n')
    .trim()
}

export function MessageList({
  messages,
  citationsByMessageId,
  selectedCitationId,
  onSelectCitation,
  chatStatus,
}: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const lastMessageId = messages.at(-1)?.id
  const busy = chatStatus === 'streaming' || chatStatus === 'submitted'

  useEffect(() => {
    const container = scrollRef.current
    if (!container) return
    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight
    // Only follow the stream when the reader is already near the bottom.
    if (distanceFromBottom < 140) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  return (
    <div
      ref={scrollRef}
      className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain"
    >
      <div className="mx-auto w-full max-w-3xl px-6 py-8">
        <ol className="space-y-6">
          {messages.map((message, index) => {
            const text = messageText(message)
            const isUser = message.role === 'user'
            const isLast = message.id === lastMessageId

            if (isUser) {
              return (
                <li
                  key={message.id}
                  className={cn(index > 0 && 'border-t border-rule pt-8')}
                >
                  <QuestionBlock text={text} />
                </li>
              )
            }

            const citations = citationsByMessageId.get(message.id) ?? []
            if (!text && citations.length === 0) return null

            return (
              <li key={message.id}>
                <AnswerNote
                  text={text}
                  citations={citations}
                  selectedCitationId={selectedCitationId}
                  onSelectCitation={onSelectCitation}
                  streaming={isLast && busy}
                />
              </li>
            )
          })}
        </ol>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
