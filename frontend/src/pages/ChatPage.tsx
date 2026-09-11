import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '@/components/auth/useAuth'
import { ActiveChatLoader } from '@/components/chat/ActiveChatLoader'
import { EmptyState } from '@/components/chat/EmptyState'
import { ThreadSidebar } from '@/components/chat/ThreadSidebar'
import { chatApi, type Thread } from '@/lib/chat'
import { formatApiError } from '@/lib/errors'
import { signOut } from '@/lib/auth'

export function ChatPage() {
  const { threadId } = useParams()
  const navigate = useNavigate()
  const { session } = useAuth()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loadingThreads, setLoadingThreads] = useState(true)
  const [threadsError, setThreadsError] = useState<string | null>(null)
  const [creatingThread, setCreatingThread] = useState(false)

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

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === threadId),
    [threadId, threads],
  )

  async function handleNewChat() {
    setCreatingThread(true)
    try {
      const thread = await chatApi.createThread()
      await refreshThreads()
      navigate(`/chat/${thread.id}`)
    } catch (error) {
      setThreadsError(formatApiError(error))
    } finally {
      setCreatingThread(false)
    }
  }

  return (
    <div className="flex h-svh bg-background">
      <ThreadSidebar
        threads={threads}
        activeThreadId={threadId}
        loading={loadingThreads || creatingThread}
        error={threadsError}
        userEmail={session?.user.email}
        onSelectThread={(id) => navigate(`/chat/${id}`)}
        onNewChat={() => void handleNewChat()}
        onSignOut={() => {
          void signOut()
        }}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        {threadId && activeThread ? (
          <ActiveChatLoader
            threadId={threadId}
            threadTitle={activeThread.title}
            onThreadActivity={() => void refreshThreads()}
          />
        ) : threadId && !loadingThreads ? (
          <EmptyState
            title="Conversation not found"
            description="This thread may have been deleted or you no longer have access."
          />
        ) : (
          <EmptyState
            title="Start a conversation"
            description="Select a thread from the sidebar or create a new chat to ask about SEC filings."
          />
        )}
      </main>
    </div>
  )
}
