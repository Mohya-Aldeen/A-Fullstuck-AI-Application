import type { Citation } from '@/lib/chat'
import {
  citationPanelSubtitle,
  citationPanelTitle,
} from '@/lib/citations'
import { Button } from '@/components/ui/button'

type SourcePassagePanelProps = {
  citation: Citation | null
  onClose: () => void
}

export function SourcePassagePanel({
  citation,
  onClose,
}: SourcePassagePanelProps) {
  if (!citation) {
    return (
      <aside className="hidden w-80 shrink-0 border-l border-border bg-muted/20 lg:flex lg:flex-col">
        <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
          <p className="text-sm font-medium">Source passage</p>
          <p className="mt-2 text-xs text-muted-foreground">
            Click a citation on an assistant message to verify the underlying
            filing excerpt.
          </p>
        </div>
      </aside>
    )
  }

  const subtitle = citationPanelSubtitle(citation)
  const filingUrl = citation.source?.source_url

  return (
    <aside className="flex w-full shrink-0 flex-col border-t border-border bg-muted/20 lg:w-80 lg:border-l lg:border-t-0">
      <div className="flex items-start justify-between gap-2 border-b border-border px-4 py-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">
            {citationPanelTitle(citation)}
          </p>
          {subtitle ? (
            <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
          ) : null}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="shrink-0 lg:hidden"
          onClick={onClose}
        >
          Close
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {citation.excerpt ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
            {citation.excerpt}
          </p>
        ) : (
          <p className="text-sm italic text-muted-foreground">
            Source passage unavailable for this citation.
          </p>
        )}
        {filingUrl ? (
          <a
            href={filingUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-block text-xs font-medium text-primary underline-offset-2 hover:underline"
          >
            Open filing on SEC
          </a>
        ) : null}
      </div>
    </aside>
  )
}
