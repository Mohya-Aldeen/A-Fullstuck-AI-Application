import { ArrowUpRight } from 'lucide-react'

import {
  CORPUS_COMPANIES,
  CORPUS_FILING_TYPE,
  CORPUS_FISCAL_RANGE,
  STARTER_PROMPTS,
} from '@/lib/corpus'

type ResearchStartProps = {
  onSelectPrompt: (prompt: string) => void
  busy?: boolean
}

export function ResearchStart({ onSelectPrompt, busy = false }: ResearchStartProps) {
  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-8 pb-16 sm:py-12">
      <header>
        <h1 className="font-serif text-3xl leading-tight font-semibold tracking-tight text-foreground sm:text-4xl">
          Ask the filings.
        </h1>
        <p className="mt-3 max-w-xl text-[0.95rem] leading-relaxed text-muted-foreground">
          Document Copilot answers from the SEC 10-K corpus and cites the exact
          filing passage behind every claim. Start from an analyst workflow
          below, or write your own question.
        </p>
      </header>

      <div className="mt-8 grid gap-px overflow-hidden rounded-lg border border-rule bg-rule sm:grid-cols-2">
        {STARTER_PROMPTS.map((item) => (
          <button
            key={item.category}
            type="button"
            disabled={busy}
            onClick={() => onSelectPrompt(item.prompt)}
            className="group flex flex-col gap-2 bg-background p-4 text-left transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none disabled:pointer-events-none disabled:opacity-60"
          >
            <span className="flex items-center justify-between text-xs font-medium text-muted-foreground">
              {item.category}
              <ArrowUpRight className="size-3.5 opacity-0 transition-opacity group-hover:opacity-100" />
            </span>
            <span className="text-sm leading-snug text-foreground">
              {item.prompt}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-8 border-t border-rule pt-4">
        <p className="text-[0.7rem] font-medium tracking-wide text-muted-foreground">
          Corpus
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-foreground">
          {CORPUS_COMPANIES.map((company) => (
            <span key={company.ticker} className="inline-flex items-baseline gap-1.5">
              <span className="font-medium tabular">{company.ticker}</span>
              <span className="text-muted-foreground">{company.name}</span>
            </span>
          ))}
          <span className="text-muted-foreground tabular">
            {CORPUS_FILING_TYPE} · {CORPUS_FISCAL_RANGE}
          </span>
        </div>
      </div>
    </div>
  )
}
