import { useState } from 'react'

import { Button } from '@/components/ui/button'

type ComposerProps = {
  disabled?: boolean
  placeholder?: string
  onSubmit: (text: string) => void
}

export function Composer({
  disabled = false,
  placeholder = 'Ask about the filings…',
  onSubmit,
}: ComposerProps) {
  const [text, setText] = useState('')

  function submit() {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setText('')
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    submit()
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-rule bg-background px-6 py-4">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-lg border border-rule bg-card px-3 py-2 transition-colors focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/30">
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            aria-label="Research question"
            className="max-h-40 min-h-[1.75rem] flex-1 resize-none bg-transparent py-1 text-sm leading-6 outline-none field-sizing-content placeholder:text-muted-foreground disabled:opacity-60"
          />
          <Button type="submit" size="sm" disabled={disabled || text.trim().length === 0}>
            Send
          </Button>
        </div>
        <p className="mt-2 text-[0.7rem] text-muted-foreground">
          Enter to send, Shift + Enter for a new line. Every answer cites the
          filing passages behind it.
        </p>
      </div>
    </form>
  )
}
