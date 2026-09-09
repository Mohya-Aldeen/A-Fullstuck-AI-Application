function requiredText(name: string, value: unknown): string {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`Missing required env var: ${name}`)
  }
  return value.trim()
}

function requiredUrl(name: string, value: unknown): string {
  const text = requiredText(name, value)
  let parsed: URL
  try {
    parsed = new URL(text)
  } catch {
    throw new Error(`Invalid URL in ${name}: ${text}`)
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error(`Invalid URL in ${name}: ${text}`)
  }
  return text.replace(/\/+$/, '')
}

export const env = {
  apiBaseUrl: requiredUrl(
    'VITE_API_BASE_URL',
    import.meta.env.VITE_API_BASE_URL,
  ),
  supabaseUrl: requiredUrl(
    'VITE_SUPABASE_URL',
    import.meta.env.VITE_SUPABASE_URL,
  ),
  supabaseAnonKey: requiredText(
    'VITE_SUPABASE_ANON_KEY',
    import.meta.env.VITE_SUPABASE_ANON_KEY,
  ),
}
