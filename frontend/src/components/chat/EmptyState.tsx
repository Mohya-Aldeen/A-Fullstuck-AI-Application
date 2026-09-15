type EmptyStateProps = {
  title: string
  description: string
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <div className="max-w-md text-center">
        <h2 className="font-serif text-xl font-semibold text-foreground">
          {title}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      </div>
    </div>
  )
}
