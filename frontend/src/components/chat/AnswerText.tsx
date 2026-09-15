import type { Citation } from '@/lib/chat'
import { parseAnswerSegments, splitParagraphs } from '@/lib/citations'
import { cn } from '@/lib/utils'

type AnswerTextProps = {
  text: string
  citationsByNumber: Map<number, Citation>
  selectedCitationId: string | null
  onSelectCitation: (citation: Citation) => void
  streaming?: boolean
}

export function AnswerText({
  text,
  citationsByNumber,
  selectedCitationId,
  onSelectCitation,
  streaming = false,
}: AnswerTextProps) {
  const paragraphs = splitParagraphs(text)
  const blocks = paragraphs.length > 0 ? paragraphs : [text]
  const lastIndex = blocks.length - 1

  return (
    <div className="space-y-4 text-[0.95rem] leading-7 text-foreground">
      {blocks.map((paragraph, blockIndex) => (
        <p key={blockIndex} className="whitespace-pre-line">
          {parseAnswerSegments(paragraph).map((segment, segmentIndex) =>
            segment.type === 'text' ? (
              <span key={segmentIndex}>{segment.text}</span>
            ) : (
              <CitationMark
                key={segmentIndex}
                number={segment.index}
                citation={citationsByNumber.get(segment.index)}
                selected={
                  citationsByNumber.get(segment.index)?.id === selectedCitationId
                }
                onSelect={onSelectCitation}
              />
            ),
          )}
          {streaming && blockIndex === lastIndex ? (
            <span
              className="ml-0.5 inline-block h-4 w-px translate-y-0.5 animate-pulse bg-foreground align-baseline"
              aria-hidden
            />
          ) : null}
        </p>
      ))}
    </div>
  )
}

type CitationMarkProps = {
  number: number
  citation?: Citation
  selected: boolean
  onSelect: (citation: Citation) => void
}

function CitationMark({ number, citation, selected, onSelect }: CitationMarkProps) {
  if (!citation) {
    return (
      <span className="ml-0.5 align-super text-[0.68em] font-medium text-muted-foreground tabular">
        [{number}]
      </span>
    )
  }
  return (
    <button
      type="button"
      onClick={() => onSelect(citation)}
      aria-pressed={selected}
      aria-label={`Show source ${number}`}
      title={citation.excerpt ?? undefined}
      className={cn(
        'mx-px inline-flex min-w-[1.15em] items-center justify-center rounded-[3px] px-1 align-super text-[0.68em] font-semibold tabular transition-colors focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none',
        selected
          ? 'bg-foreground text-background'
          : 'bg-muted text-foreground hover:bg-rule-strong',
      )}
    >
      {number}
    </button>
  )
}
