import type { Thread } from '@/lib/chat'

export function filterThreads(threads: Thread[], query: string): Thread[] {
  const q = query.trim().toLowerCase()
  if (!q) return threads
  return threads.filter((thread) => thread.title.toLowerCase().includes(q))
}

export type ThreadGroup = { label: string; threads: Thread[] }

const DAY_MS = 86_400_000

/** Group already-sorted (newest-first) threads into recency buckets. */
export function groupThreadsByRecency(threads: Thread[]): ThreadGroup[] {
  const now = new Date()
  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime()

  const order = ['Today', 'Yesterday', 'Previous 7 days', 'Previous 30 days', 'Older']
  const buckets = new Map<string, Thread[]>(order.map((label) => [label, []]))

  for (const thread of threads) {
    const ts = new Date(thread.updated_at).getTime()
    let label: string
    if (ts >= startOfToday) label = 'Today'
    else if (ts >= startOfToday - DAY_MS) label = 'Yesterday'
    else if (ts >= startOfToday - 7 * DAY_MS) label = 'Previous 7 days'
    else if (ts >= startOfToday - 30 * DAY_MS) label = 'Previous 30 days'
    else label = 'Older'
    buckets.get(label)!.push(thread)
  }

  return order
    .map((label) => ({ label, threads: buckets.get(label)! }))
    .filter((group) => group.threads.length > 0)
}

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso)
  const diff = Date.now() - date.getTime()
  const minutes = Math.round(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)
}
