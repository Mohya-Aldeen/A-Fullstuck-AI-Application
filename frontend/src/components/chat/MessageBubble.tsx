import type { UIMessage } from 'ai'
import { isTextUIPart } from 'ai'

import { CitationBlock } from '@/components/chat/CitationBlock'
import type { Citation } from '@/lib/chat'
import { cn } from '@/lib/utils'

type MessageBubbleProps = {
  message: UIMessage
  citations?: Citation[]
}

function messageText(message: UIMessage): string {
  return message.parts
    .flatMap((part) => (isTextUIPart(part) ? [part.text] : []))
    .join('\n')
    .trim()
}

export function MessageBubble({ message, citations = [] }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const text = messageText(message)

  if (!text && citations.length === 0) {
    return null
  }

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'border border-border bg-card text-card-foreground',
        )}
      >
        {text ? (
          <p className="whitespace-pre-wrap">{text}</p>
        ) : null}
        {!isUser ? <CitationBlock citations={citations} /> : null}
      </div>
    </div>
  )
}
