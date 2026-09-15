import { Menu } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '@/components/auth/useAuth'
import { ActiveChatLoader } from '@/components/chat/ActiveChatLoader'
import { EmptyState } from '@/components/chat/EmptyState'
import { ResearchStart } from '@/components/chat/ResearchStart'
import { ThreadSidebar } from '@/components/chat/ThreadSidebar'
import { Button } from '@/components/ui/button'
import { chatApi, type Thread } from '@/lib/chat'
import { formatApiError } from '@/lib/errors'
import { signOut } from '@/lib/auth'

export function ChatPage() {
  const { threadId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { session } = useAuth()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loadingThreads, setLoadingThreads] = useState(true)
  const [threadsError, setThreadsError] = useState<string | null>(null)
  const [creatingThread, setCreatingThread] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null)

  const refreshThreads = useCallback(async () => {
    try {
      const data = await chatApi.listThreads()
      setThreads(data)
      setThreadsError(null)
    } catch (error) {
      setThreadsError(formatApiError(error))
    } finally {
      setLoadingThreads(false)
    }
  }, [])

  useEffect(() => {
    void refreshThreads()
  }, [refreshThreads])

  // A starter prompt from the home screen arrives as navigation state; capture it
  // once, then drop it from history so a refresh will not resend.
  useEffect(() => {
    const prompt = (location.state as { prompt?: string } | null)?.prompt
    if (prompt) {
      setPendingPrompt(prompt)
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location.key, location.pathname, location.state, navigate])

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === threadId),
    [threadId, threads],
  )

  async function handleNewChat() {
    setSidebarOpen(false)
    setCreatingThread(true)
    try {
      const thread = await chatApi.createThread()
      await refreshThreads()
      navigate(`/chat/${thread.id}`)
    } catch (error) {
      setThreadsError(formatApiError(error))
      await refreshThreads()
    } finally {
      setCreatingThread(false)
    }
  }

  async function handleStartPrompt(prompt: string) {
    setCreatingThread(true)
    try {
      const thread = await chatApi.createThread()
      await refreshThreads()
      navigate(`/chat/${thread.id}`, { state: { prompt } })
    } catch (error) {
      setThreadsError(formatApiError(error))
      await refreshThreads()
    } finally {
      setCreatingThread(false)
    }
  }

  const sidebar = (
    <ThreadSidebar
      threads={threads}
      activeThreadId={threadId}
      loading={loadingThreads || creatingThread}
      error={threadsError}
      userEmail={session?.user.email}
      onSelectThread={(id) => {
        setSidebarOpen(false)
        navigate(`/chat/${id}`)
      }}
      onNewChat={() => void handleNewChat()}
      onSignOut={() => {
        void signOut()
      }}
      onRetry={() => {
        setThreadsError(null)
        setLoadingThreads(true)
        void refreshThreads()
      }}
    />
  )

  let content: React.ReactNode
  if (threadId && activeThread) {
    content = (
      <ActiveChatLoader
        threadId={threadId}
        threadTitle={activeThread.title}
        pendingPrompt={pendingPrompt}
        onPromptConsumed={() => setPendingPrompt(null)}
        onThreadActivity={() => void refreshThreads()}
      />
    )
  } else if (threadId && !loadingThreads) {
    content = (
      <EmptyState
        title="Conversation not found"
        description="This thread may have been deleted, or you no longer have access to it."
      />
    )
  } else if (threadId) {
    content = (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        Loading conversation…
      </div>
    )
  } else {
    content = (
      <ResearchStart
        busy={creatingThread}
        onSelectPrompt={(prompt) => void handleStartPrompt(prompt)}
      />
    )
  }

  return (
    <div className="flex h-svh overflow-hidden bg-background">
      <aside className="hidden h-svh min-h-0 w-[280px] shrink-0 border-r border-rule lg:block xl:w-[300px]">
        {sidebar}
      </aside>

      {sidebarOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Close conversations"
            className="absolute inset-0 bg-foreground/25"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-[300px] max-w-[85%] border-r border-rule bg-sidebar shadow-2xl">
            {sidebar}
          </div>
        </div>
      ) : null}

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-rule px-4 py-2.5 lg:hidden">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Open conversations"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu />
          </Button>
          <span className="font-serif text-base font-semibold tracking-tight">
            Document Copilot
          </span>
        </div>

        <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
          {threadId && activeThread ? (
            content
          ) : (
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain">
              {content}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
