import { PenLine, Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Wordmark } from '@/components/chat/Wordmark'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Thread } from '@/lib/chat'
import { filterThreads, formatRelativeTime, groupThreadsByRecency } from '@/lib/threads'
import { cn } from '@/lib/utils'

type ThreadSidebarProps = {
  threads: Thread[]
  activeThreadId?: string
  loading?: boolean
  error?: string | null
  userEmail?: string | null
  onSelectThread: (threadId: string) => void
  onNewChat: () => void
  onSignOut: () => void
  onRetry?: () => void
}

export function ThreadSidebar({
  threads,
  activeThreadId,
  loading = false,
  error = null,
  userEmail,
  onSelectThread,
  onNewChat,
  onSignOut,
  onRetry,
}: ThreadSidebarProps) {
  const [query, setQuery] = useState('')
  const groups = useMemo(
    () => groupThreadsByRecency(filterThreads(threads, query)),
    [threads, query],
  )
  const hasThreads = threads.length > 0

  return (
    <div className="flex h-full w-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="px-5 pt-5 pb-4">
        <Wordmark />
      </div>

      <div className="px-3">
        <Button
          size="lg"
          className="w-full justify-start gap-2"
          onClick={onNewChat}
          disabled={loading}
        >
          <PenLine data-icon="inline-start" />
          New research
        </Button>
      </div>

      {hasThreads ? (
        <div className="px-3 pt-3">
          <div className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search conversations"
              aria-label="Search conversations"
              className="h-8 w-full rounded-md border border-sidebar-border bg-transparent pr-2.5 pl-8 text-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/40"
            />
          </div>
        </div>
      ) : null}

      <ScrollArea className="mt-3 flex-1 px-2">
        {error ? (
          <div className="px-3 py-3" role="alert">
            <p className="text-sm text-destructive">{error}</p>
            {onRetry ? (
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={onRetry}
                disabled={loading}
              >
                {loading ? 'Retrying…' : 'Try again'}
              </Button>
            ) : null}
          </div>
        ) : null}

        {loading && !hasThreads ? (
          <ul className="space-y-2 px-1 py-2" aria-hidden>
            {[0, 1, 2, 3].map((row) => (
              <li key={row} className="rounded-md px-2 py-2">
                <div className="h-3.5 w-3/4 animate-pulse rounded bg-muted" />
                <div className="mt-2 h-2.5 w-1/3 animate-pulse rounded bg-muted" />
              </li>
            ))}
          </ul>
        ) : !hasThreads ? (
          <p className="px-3 py-3 text-sm text-muted-foreground">
            No conversations yet. Start a new research thread to ask about the
            filings.
          </p>
        ) : groups.length === 0 ? (
          <p className="px-3 py-3 text-sm text-muted-foreground">
            No conversations match “{query}”.
          </p>
        ) : (
          <div className="space-y-4 pb-3">
            {groups.map((group) => (
              <section key={group.label}>
                <h2 className="px-3 pb-1 text-[0.7rem] font-medium text-muted-foreground">
                  {group.label}
                </h2>
                <ul>
                  {group.threads.map((thread) => {
                    const active = thread.id === activeThreadId
                    return (
                      <li key={thread.id}>
                        <button
                          type="button"
                          onClick={() => onSelectThread(thread.id)}
                          aria-current={active ? 'true' : undefined}
                          className={cn(
                            'group relative w-full rounded-md py-2 pr-2.5 pl-3 text-left transition-colors',
                            active
                              ? 'bg-sidebar-accent'
                              : 'hover:bg-sidebar-accent/60',
                          )}
                        >
                          <span
                            className={cn(
                              'absolute top-1.5 bottom-1.5 left-0 w-0.5 rounded-full bg-foreground transition-opacity',
                              active ? 'opacity-100' : 'opacity-0',
                            )}
                            aria-hidden
                          />
                          <span className="line-clamp-2 text-sm leading-snug font-medium text-sidebar-foreground">
                            {thread.title}
                          </span>
                          <span className="mt-1 block text-[0.7rem] text-muted-foreground tabular">
                            {formatRelativeTime(thread.updated_at)}
                          </span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </section>
            ))}
          </div>
        )}
      </ScrollArea>

      <div className="border-t border-sidebar-border p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-sidebar-foreground">
              {userEmail ?? 'Signed in'}
            </p>
            <p className="text-[0.7rem] text-muted-foreground">Analyst</p>
          </div>
          <Button variant="outline" size="sm" onClick={onSignOut}>
            Sign out
          </Button>
        </div>
      </div>
    </div>
  )
}
