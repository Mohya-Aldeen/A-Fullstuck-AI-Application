import { AlertTriangle, Info } from 'lucide-react'

import { AnswerText } from '@/components/chat/AnswerText'
import { EvidenceList } from '@/components/chat/EvidenceList'
import type { Citation } from '@/lib/chat'
import {
  isGroundingFailureMessage,
  isInsufficientEvidenceMessage,
} from '@/lib/citations'

type AnswerNoteProps = {
  text: string
  citations: Citation[]
  selectedCitationId: string | null
  onSelectCitation: (citation: Citation) => void
  streaming?: boolean
}

export function AnswerNote({
  text,
  citations,
  selectedCitationId,
  onSelectCitation,
  streaming = false,
}: AnswerNoteProps) {
  if (!text && citations.length === 0) return null

  const groundingFailed = Boolean(text) && isGroundingFailureMessage(text)
  const insufficient =
    !groundingFailed &&
    citations.length === 0 &&
    isInsufficientEvidenceMessage(text)

  if (groundingFailed) {
    return (
      <div className="flex gap-3 border border-destructive/30 bg-destructive/5 p-4">
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-destructive" />
        <div>
          <p className="text-sm font-medium text-foreground">
            Grounding check failed
          </p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
            {text}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            No citations were saved for this reply. Try a narrower or more
            specific question.
          </p>
        </div>
      </div>
    )
  }

  const citationsByNumber = new Map<number, Citation>(
    citations.map((citation) => [citation.citation_index + 1, citation]),
  )

  return (
    <div>
      <AnswerText
        text={text}
        citationsByNumber={citationsByNumber}
        selectedCitationId={selectedCitationId}
        onSelectCitation={onSelectCitation}
        streaming={streaming}
      />

      {insufficient ? (
        <div className="mt-4 flex items-center gap-2 border border-rule bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
          <Info className="size-3.5 shrink-0" />
          The corpus does not contain enough evidence to support a cited answer.
        </div>
      ) : null}

      {citations.length > 0 ? (
        <EvidenceList
          citations={citations}
          selectedCitationId={selectedCitationId}
          onSelectCitation={onSelectCitation}
        />
      ) : !streaming && !insufficient && text ? (
        <p className="mt-4 text-xs text-muted-foreground">
          No filing citations were attached to this answer.
        </p>
      ) : null}
    </div>
  )
}
