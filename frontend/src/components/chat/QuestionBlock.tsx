type QuestionBlockProps = {
  text: string
}

export function QuestionBlock({ text }: QuestionBlockProps) {
  return (
    <div className="border-l-2 border-foreground pl-4">
      <p className="font-serif text-xl leading-snug font-medium text-foreground">
        {text}
      </p>
    </div>
  )
}
