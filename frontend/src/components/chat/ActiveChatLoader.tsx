import type { UIMessage } from 'ai'
import { useCallback, useEffect, useState } from 'react'

import { ChatPane } from '@/components/chat/ChatPane'
import { EmptyState } from '@/components/chat/EmptyState'
import type { Citation } from '@/lib/chat'
import {
  chatApi,
  buildCitationsByMessageId,
  storedMessageToUiMessage,
} from '@/lib/chat'
import { formatApiError } from '@/lib/errors'

type ActiveChatLoaderProps = {
  threadId: string
  threadTitle: string
  onThreadActivity?: () => void
}

export function ActiveChatLoader({
  threadId,
  threadTitle,
  onThreadActivity,
}: ActiveChatLoaderProps) {
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | null>(
    null,
  )
  const [initialCitations, setInitialCitations] = useState<Map<
    string,
    Citation[]
  > | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  const loadMessages = useCallback(async () => {
    setLoadError(null)
    setInitialMessages(null)
    setInitialCitations(null)

    try {
      const stored = await chatApi.listMessages(threadId)
      setInitialMessages(stored.map(storedMessageToUiMessage))
      setInitialCitations(buildCitationsByMessageId(stored))
    } catch (error) {
      setLoadError(formatApiError(error))
    }
  }, [threadId])

  useEffect(() => {
    void loadMessages()
  }, [loadMessages])

  if (loadError) {
    return (
      <EmptyState
        title="Could not load this conversation"
        description={loadError}
      />
    )
  }

  if (initialMessages === null || initialCitations === null) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        Loading messages…
      </div>
    )
  }

  return (
    <ChatPane
      key={threadId}
      threadId={threadId}
      threadTitle={threadTitle}
      initialMessages={initialMessages}
      initialCitations={initialCitations}
      onThreadActivity={onThreadActivity}
    />
  )
}
