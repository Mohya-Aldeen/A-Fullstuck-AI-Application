import { useEffect, useState } from 'react'

import { useAuth } from '@/components/auth/useAuth'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { api, ApiError } from '@/lib/api'
import { signOut } from '@/lib/auth'

type MeResponse = {
  id: string
  email: string | null
}

export function HomePage() {
  const { session } = useAuth()
  const [me, setMe] = useState<MeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    void api
      .get<MeResponse>('/me')
      .then((data) => {
        if (!cancelled) setMe(data)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.isNetworkError) {
          setError(
            'Could not reach the backend. Is it running on VITE_API_BASE_URL?',
          )
          return
        }
        if (err instanceof ApiError) {
          setError(err.message)
          return
        }
        setError('Failed to verify session with the backend')
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Document Copilot</CardTitle>
          <CardDescription>
            Signed in as {session?.user.email ?? 'unknown'}. Chat comes next —
            this page confirms your token reaches FastAPI.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}
          {me ? (
            <dl className="grid gap-2 text-sm">
              <div>
                <dt className="text-muted-foreground">Backend user id</dt>
                <dd className="font-mono">{me.id}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Backend email</dt>
                <dd>{me.email ?? '—'}</dd>
              </div>
            </dl>
          ) : error ? null : (
            <p className="text-sm text-muted-foreground">
              Checking GET /me…
            </p>
          )}
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              void signOut()
            }}
          >
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
