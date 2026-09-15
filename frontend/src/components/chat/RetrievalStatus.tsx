import type { ChatStatus } from 'ai'

type RetrievalStatusProps = {
  status: ChatStatus
  errorMessage: string | null
}

export function RetrievalStatus({ status, errorMessage }: RetrievalStatusProps) {
  const busy = status === 'submitted' || status === 'streaming'

  if (errorMessage) {
    return (
      <div className="border-t border-rule bg-destructive/5 px-6 py-2.5">
        <p className="mx-auto max-w-3xl text-sm text-destructive" role="alert">
          {errorMessage}
        </p>
      </div>
    )
  }

  if (!busy) return null

  const label =
    status === 'submitted'
      ? 'Searching the filings…'
      : 'Composing a grounded answer…'

  return (
    <div className="border-t border-rule px-6 pt-0" aria-live="polite">
      <div className="h-0.5 w-full overflow-hidden bg-rule">
        <div className="h-full w-1/3 rounded-full bg-foreground animate-scan" />
      </div>
      <p className="mx-auto max-w-3xl py-2 text-xs text-muted-foreground">
        {label}
      </p>
    </div>
  )
}
