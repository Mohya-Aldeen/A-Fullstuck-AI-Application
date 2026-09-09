import { Navigate } from 'react-router-dom'

import { AuthForm } from '@/components/auth/AuthForm'
import { useAuth } from '@/components/auth/useAuth'

export function SignInPage() {
  const { session, loading } = useAuth()
  if (loading) return null
  if (session) return <Navigate to="/" replace />
  return <AuthForm mode="sign-in" />
}
