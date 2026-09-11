import type { ChatStatus } from 'ai'

type ChatStatusBarProps = {
  status: ChatStatus
  errorMessage: string | null
}

function statusLabel(status: ChatStatus): string | null {
  switch (status) {
    case 'submitted':
      return 'Sending…'
    case 'streaming':
      return 'Assistant is responding…'
    case 'ready':
    case 'error':
      return null
    default:
      return null
  }
}

export function ChatStatusBar({ status, errorMessage }: ChatStatusBarProps) {
  const label = statusLabel(status)

  if (!label && !errorMessage) return null

  return (
    <div className="border-t border-border px-4 py-2 text-sm">
      {errorMessage ? (
        <p className="text-destructive" role="alert">
          {errorMessage}
        </p>
      ) : label ? (
        <p className="text-muted-foreground">{label}</p>
      ) : null}
    </div>
  )
}
