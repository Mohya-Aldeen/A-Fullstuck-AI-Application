import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Wordmark } from '@/components/chat/Wordmark'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  CORPUS_COMPANIES,
  CORPUS_FILING_TYPE,
  CORPUS_FISCAL_RANGE,
} from '@/lib/corpus'
import { signInWithEmail, signUpWithEmail } from '@/lib/auth'

type AuthFormProps = {
  mode: 'sign-in' | 'sign-up'
}

export function AuthForm({ mode }: AuthFormProps) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const isSignUp = mode === 'sign-up'

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setInfo(null)

    if (isSignUp && password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setPending(true)
    try {
      if (isSignUp) {
        const session = await signUpWithEmail(email.trim(), password)
        if (session === null) {
          setInfo(
            'Account created. Check your inbox to confirm your email, then sign in. For local dev you can turn off email confirmation in the Supabase dashboard.',
          )
          return
        }
      } else {
        await signInWithEmail(email.trim(), password)
      }
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <aside className="hidden flex-col justify-between border-r border-rule bg-sidebar p-10 lg:flex">
        <Wordmark />
        <div>
          <h2 className="font-serif text-4xl leading-tight font-semibold tracking-tight text-foreground">
            Grounded answers, straight from the filings.
          </h2>
          <p className="mt-4 max-w-md text-[0.95rem] leading-relaxed text-muted-foreground">
            A research workstation for equity analysts. Ask questions about SEC
            10-K filings and get answers that cite the exact passage behind
            every claim.
          </p>
        </div>
        <div className="border-t border-rule pt-4">
          <p className="text-[0.7rem] font-medium text-muted-foreground">
            Corpus
          </p>
          <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1 text-sm text-foreground">
            {CORPUS_COMPANIES.map((company) => (
              <span key={company.ticker} className="font-medium tabular">
                {company.ticker}
              </span>
            ))}
            <span className="text-muted-foreground tabular">
              {CORPUS_FILING_TYPE}, {CORPUS_FISCAL_RANGE}
            </span>
          </div>
        </div>
      </aside>

      <main className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Wordmark />
          </div>

          <h1 className="font-serif text-2xl font-semibold tracking-tight text-foreground">
            {isSignUp ? 'Create your account' : 'Sign in'}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Email and password only. No Google or SSO.
          </p>

          <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                className="h-9"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete={isSignUp ? 'new-password' : 'current-password'}
                minLength={6}
                className="h-9"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            {isSignUp ? (
              <div className="flex flex-col gap-2">
                <Label htmlFor="confirm-password">Confirm password</Label>
                <Input
                  id="confirm-password"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  minLength={6}
                  className="h-9"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  required
                />
              </div>
            ) : null}
            {error ? (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}
            {info ? (
              <p className="text-sm text-muted-foreground" role="status">
                {info}
              </p>
            ) : null}
            <Button type="submit" size="lg" disabled={pending}>
              {pending ? 'Please wait…' : isSignUp ? 'Create account' : 'Sign in'}
            </Button>
            <p className="text-sm text-muted-foreground">
              {isSignUp ? (
                <>
                  Already have an account?{' '}
                  <Link className="font-medium text-foreground underline underline-offset-2" to="/sign-in">
                    Sign in
                  </Link>
                </>
              ) : (
                <>
                  Need an account?{' '}
                  <Link className="font-medium text-foreground underline underline-offset-2" to="/sign-up">
                    Sign up
                  </Link>
                </>
              )}
            </p>
          </form>
        </div>
      </main>
    </div>
  )
}
