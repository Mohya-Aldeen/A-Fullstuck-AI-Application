import type { Citation } from '@/lib/chat'
import {
  citationCompany,
  citationFilingType,
  citationFiscalYear,
  citationLocation,
  citationNumber,
  citationTicker,
} from '@/lib/citations'
import { cn } from '@/lib/utils'

type EvidenceListProps = {
  citations: Citation[]
  selectedCitationId: string | null
  onSelectCitation: (citation: Citation) => void
}

export function EvidenceList({
  citations,
  selectedCitationId,
  onSelectCitation,
}: EvidenceListProps) {
  if (citations.length === 0) return null
  const sorted = [...citations].sort(
    (a, b) => a.citation_index - b.citation_index,
  )

  return (
    <section className="mt-5">
      <h3 className="text-xs font-medium text-muted-foreground">
        Evidence
        <span className="ml-1.5 tabular">({sorted.length})</span>
      </h3>
      <ul className="mt-2 divide-y divide-rule border-y border-rule">
        {sorted.map((citation) => {
          const selected = citation.id === selectedCitationId
          const ticker = citationTicker(citation)
          const filingType = citationFilingType(citation)
          const fiscalYear = citationFiscalYear(citation)
          const location = citationLocation(citation)
          return (
            <li key={citation.id}>
              <button
                type="button"
                onClick={() => onSelectCitation(citation)}
                aria-pressed={selected}
                className={cn(
                  'group relative flex w-full items-start gap-3 py-2.5 pr-2 pl-3 text-left transition-colors',
                  selected ? 'bg-muted' : 'hover:bg-muted/60',
                )}
              >
                <span
                  className={cn(
                    'absolute top-2 bottom-2 left-0 w-0.5 rounded-full bg-foreground transition-opacity',
                    selected ? 'opacity-100' : 'opacity-0',
                  )}
                  aria-hidden
                />
                <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-[3px] border border-rule-strong text-[0.7rem] font-semibold text-foreground tabular">
                  {citationNumber(citation)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-sm font-medium text-foreground">
                      {citationCompany(citation)}
                    </span>
                    <span className="flex shrink-0 items-baseline gap-2 text-[0.72rem] text-muted-foreground tabular">
                      {ticker ? <span>{ticker}</span> : null}
                      {filingType ? <span>{filingType}</span> : null}
                      {fiscalYear ? <span>FY{fiscalYear}</span> : null}
                      {location ? <span>{location}</span> : null}
                    </span>
                  </span>
                  {citation.excerpt ? (
                    <span className="mt-0.5 line-clamp-1 block text-[0.8rem] text-muted-foreground">
                      {citation.excerpt}
                    </span>
                  ) : null}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
