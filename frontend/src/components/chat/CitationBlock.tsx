import type { Citation } from '@/lib/chat'

type CitationBlockProps = {
  citations: Citation[]
}

export function CitationBlock({ citations }: CitationBlockProps) {
  if (citations.length === 0) return null

  const sorted = [...citations].sort(
    (a, b) => a.citation_index - b.citation_index,
  )

  return (
    <div className="mt-3 space-y-2 border-t border-border pt-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Sources
      </p>
      <ul className="space-y-2">
        {sorted.map((citation) => (
          <li
            key={citation.id}
            className="rounded-md border border-border bg-muted/40 p-3 text-sm"
          >
            <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">
                Citation {citation.citation_index + 1}
              </span>
              {citation.page_label ? (
                <span>Page {citation.page_label}</span>
              ) : null}
            </div>
            {citation.excerpt ? (
              <p className="whitespace-pre-wrap text-foreground/90">
                {citation.excerpt}
              </p>
            ) : (
              <p className="text-muted-foreground italic">
                Source passage unavailable
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
