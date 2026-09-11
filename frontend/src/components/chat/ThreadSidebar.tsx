import { MessageSquarePlus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Thread } from '@/lib/chat'
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
}

function formatThreadTime(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))
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
}: ThreadSidebarProps) {
  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
      <div className="border-b border-sidebar-border p-4">
        <div className="mb-3">
          <h1 className="text-base font-semibold">Document Copilot</h1>
          {userEmail ? (
            <p className="truncate text-xs text-muted-foreground">{userEmail}</p>
          ) : null}
        </div>
        <Button className="w-full" onClick={onNewChat} disabled={loading}>
          <MessageSquarePlus data-icon="inline-start" />
          New chat
        </Button>
      </div>

      <ScrollArea className="flex-1 px-2 py-2">
        {error ? (
          <p className="px-2 py-3 text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}
        {loading ? (
          <p className="px-2 py-3 text-sm text-muted-foreground">
            Loading threads…
          </p>
        ) : threads.length === 0 ? (
          <p className="px-2 py-3 text-sm text-muted-foreground">
            No conversations yet.
          </p>
        ) : (
          <ul className="space-y-1">
            {threads.map((thread) => {
              const active = thread.id === activeThreadId
              return (
                <li key={thread.id}>
                  <button
                    type="button"
                    onClick={() => onSelectThread(thread.id)}
                    className={cn(
                      'w-full rounded-lg px-3 py-2 text-left transition-colors',
                      active
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                        : 'hover:bg-sidebar-accent/60',
                    )}
                  >
                    <span className="line-clamp-2 text-sm font-medium">
                      {thread.title}
                    </span>
                    <span className="mt-1 block text-xs text-muted-foreground">
                      {formatThreadTime(thread.updated_at)}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </ScrollArea>

      <div className="border-t border-sidebar-border p-4">
        <Button variant="outline" className="w-full" onClick={onSignOut}>
          Sign out
        </Button>
      </div>
    </aside>
  )
}
