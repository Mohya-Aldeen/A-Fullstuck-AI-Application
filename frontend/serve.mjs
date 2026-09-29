/**
 * Serves the Vite production build on Railway.
 *
 * React Router paths such as /sign-in and /chat/:id are not real files.
 * Unknown paths with no file extension fall back to index.html so the
 * browser app can handle the route. No extra static-server dependency.
 */
import { createReadStream, existsSync, statSync } from 'node:fs'
import { createServer } from 'node:http'
import { extname, join, normalize, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('./dist', import.meta.url))
const port = Number(process.env.PORT ?? 4173)

const types = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
}

function insideRoot(path) {
  const resolved = normalize(path)
  return resolved === root || resolved.startsWith(root + sep)
}

function resolveFile(urlPath) {
  const decoded = decodeURIComponent((urlPath ?? '/').split('?')[0])
  const candidate = normalize(join(root, decoded))
  if (!insideRoot(candidate)) return null
  if (existsSync(candidate) && statSync(candidate).isFile()) return candidate
  if (existsSync(candidate) && statSync(candidate).isDirectory()) {
    const index = join(candidate, 'index.html')
    if (existsSync(index)) return index
  }
  if (extname(decoded)) return null
  const fallback = join(root, 'index.html')
  return existsSync(fallback) ? fallback : null
}

const server = createServer((req, res) => {
  if (!existsSync(root)) {
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' })
    res.end('frontend/dist is missing. Run pnpm build first.')
    return
  }
  const file = resolveFile(req.url)
  if (!file) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' })
    res.end('Not found')
    return
  }
  res.writeHead(200, {
    'Content-Type': types[extname(file)] ?? 'application/octet-stream',
  })
  if (req.method === 'HEAD') {
    res.end()
    return
  }
  createReadStream(file).pipe(res)
})

server.listen(port, '0.0.0.0', () => {
  console.log(`frontend listening on ${port}`)
})
