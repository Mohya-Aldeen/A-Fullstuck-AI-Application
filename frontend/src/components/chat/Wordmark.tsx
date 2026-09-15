import { cn } from '@/lib/utils'

type WordmarkProps = {
  className?: string
}

export function Wordmark({ className }: WordmarkProps) {
  return (
    <div className={cn('select-none', className)}>
      <div className="flex items-baseline gap-2">
        <span className="font-serif text-[1.3rem] leading-none font-semibold tracking-tight text-foreground">
          Document Copilot
        </span>
      </div>
      <span className="mt-1.5 block text-[0.65rem] font-medium tracking-[0.18em] text-muted-foreground tabular">
        SEC 10-K RESEARCH
      </span>
    </div>
  )
}
