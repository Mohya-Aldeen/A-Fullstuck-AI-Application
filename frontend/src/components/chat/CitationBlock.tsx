import type { Citation } from '@/lib/chat'
import { citationChipLabel } from '@/lib/citations'
import { cn } from '@/lib/utils'

type CitationBlockProps = {
  citations: Citation[]
  selectedCitationId: string | null
  onSelectCitation: (citation: Citation) => void
}

export function CitationBlock({
  citations,
  selectedCitationId,
  onSelectCitation,
}: CitationBlockProps) {
  if (citations.length === 0) return null

  const sorted = [...citations].sort(
    (a, b) => a.citation_index - b.citation_index,
  )

  return (
    <div className="mt-3 space-y-2 border-t border-border pt-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Sources — click to verify
      </p>
      <ul className="flex flex-wrap gap-2">
        {sorted.map((citation) => {
          const selected = citation.id === selectedCitationId
          return (
            <li key={citation.id}>
              <button
                type="button"
                onClick={() => onSelectCitation(citation)}
                className={cn(
                  'rounded-full border px-3 py-1 text-left text-xs transition-colors',
                  selected
                    ? 'border-primary bg-primary/10 text-foreground'
                    : 'border-border bg-background text-muted-foreground hover:border-primary/50 hover:text-foreground',
                )}
                aria-pressed={selected}
                title={citation.excerpt ?? undefined}
              >
                {citationChipLabel(citation)}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
