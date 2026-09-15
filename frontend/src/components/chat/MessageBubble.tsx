import type { UIMessage } from 'ai'
import { isTextUIPart } from 'ai'

import { CitationBlock } from '@/components/chat/CitationBlock'
import type { Citation } from '@/lib/chat'
import { isGroundingFailureMessage } from '@/lib/citations'
import { cn } from '@/lib/utils'

type MessageBubbleProps = {
  message: UIMessage
  citations?: Citation[]
  selectedCitationId: string | null
  onSelectCitation: (citation: Citation) => void
  hideMissingCitationHint?: boolean
}

function messageText(message: UIMessage): string {
  return message.parts
    .flatMap((part) => (isTextUIPart(part) ? [part.text] : []))
    .join('\n')
    .trim()
}

export function MessageBubble({
  message,
  citations = [],
  selectedCitationId,
  onSelectCitation,
  hideMissingCitationHint = false,
}: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const text = messageText(message)
  const groundingFailed = !isUser && text && isGroundingFailureMessage(text)

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
        {groundingFailed ? (
          <p className="mt-2 text-xs text-destructive" role="alert">
            Grounding check failed — no citations were saved for this reply.
          </p>
        ) : null}
        {!isUser && citations.length > 0 ? (
          <CitationBlock
            citations={citations}
            selectedCitationId={selectedCitationId}
            onSelectCitation={onSelectCitation}
          />
        ) : null}
        {!isUser &&
        !groundingFailed &&
        !hideMissingCitationHint &&
        citations.length === 0 &&
        text ? (
          <p className="mt-2 text-xs text-muted-foreground">
            No filing citations for this message — the corpus may not contain
            enough evidence.
          </p>
        ) : null}
      </div>
    </div>
  )
}
