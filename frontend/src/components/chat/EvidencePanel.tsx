import { ExternalLink, FileText, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Citation } from '@/lib/chat'
import {
  citationCompany,
  citationFields,
  citationNumber,
} from '@/lib/citations'
import { cn } from '@/lib/utils'

type EvidencePanelProps = {
  citation: Citation | null
  onClose: () => void
}

export function EvidencePanel({ citation, onClose }: EvidencePanelProps) {
  return (
    <>
      {/* Persistent column on wide screens. */}
      <aside className="hidden h-full min-h-0 w-[380px] shrink-0 flex-col overflow-hidden border-l border-rule bg-muted/20 xl:flex">
        {citation ? (
          <EvidenceBody citation={citation} onClose={onClose} />
        ) : (
          <EvidencePlaceholder />
        )}
      </aside>

      {/* Slide-over drawer below xl. */}
      {citation ? (
        <div className="fixed inset-0 z-40 xl:hidden">
          <button
            type="button"
            aria-label="Close source"
            className="absolute inset-0 bg-foreground/25"
            onClick={onClose}
          />
          <div className="absolute inset-y-0 right-0 flex w-[420px] max-w-[92%] flex-col border-l border-rule bg-background shadow-2xl">
            <EvidenceBody citation={citation} onClose={onClose} />
          </div>
        </div>
      ) : null}
    </>
  )
}

function EvidencePlaceholder() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 px-8 text-center">
      <FileText className="size-5 text-muted-foreground" aria-hidden />
      <p className="text-sm font-medium text-foreground">Source passage</p>
      <p className="text-xs leading-relaxed text-muted-foreground">
        Select a citation mark or an evidence row to read the exact filing
        passage behind a claim.
      </p>
    </div>
  )
}

type EvidenceBodyProps = {
  citation: Citation
  onClose: () => void
}

function EvidenceBody({ citation, onClose }: EvidenceBodyProps) {
  const fields = citationFields(citation)
  const filingUrl = citation.source?.source_url

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-start justify-between gap-3 border-b border-rule px-4 py-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-[3px] border border-rule-strong text-[0.7rem] font-semibold text-foreground tabular">
            {citationNumber(citation)}
          </span>
          <div className="min-w-0">
            <p className="truncate font-serif text-base leading-snug font-semibold text-foreground">
              {citationCompany(citation)}
            </p>
            <p className="text-[0.7rem] text-muted-foreground">Cited source</p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label="Close source"
          onClick={onClose}
        >
          <X />
        </Button>
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <div className="px-4 py-4">
          {fields.length > 0 ? (
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5 border-b border-rule pb-4">
              {fields.map((field) => (
                <div key={field.label} className="contents">
                  <dt className="text-[0.72rem] text-muted-foreground">
                    {field.label}
                  </dt>
                  <dd
                    className={cn(
                      'text-right text-[0.8rem] text-foreground',
                      field.tabular && 'tabular',
                    )}
                  >
                    {field.value}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}

          <div className="pt-4">
            <p className="text-[0.7rem] font-medium text-muted-foreground">
              Passage
            </p>
            {citation.excerpt ? (
              <blockquote className="mt-2 border-l-2 border-rule-strong pl-3 text-[0.9rem] leading-relaxed text-foreground">
                {citation.excerpt}
              </blockquote>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground italic">
                The source passage is unavailable for this citation.
              </p>
            )}
          </div>

          {filingUrl ? (
            <a
              href={filingUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-5 inline-flex items-center gap-1.5 text-xs font-medium text-foreground underline-offset-2 hover:underline"
            >
              Open filing on SEC.gov
              <ExternalLink className="size-3.5" aria-hidden />
            </a>
          ) : null}
        </div>
      </ScrollArea>
    </div>
  )
}
