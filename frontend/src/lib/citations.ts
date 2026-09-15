import type { Citation } from '@/lib/chat'

export function citationChipLabel(citation: Citation): string {
  const index = citation.citation_index + 1
  const parts: string[] = [`[${index}]`]
  const source = citation.source
  if (source?.ticker) parts.push(source.ticker)
  if (source?.filing_type) parts.push(source.filing_type)
  if (source?.filing_year != null) parts.push(String(source.filing_year))
  else if (source?.filing_date) parts.push(source.filing_date.slice(0, 4))
  if (citation.page_label) parts.push(`p.${citation.page_label}`)
  else if (source?.section_label) parts.push(source.section_label)
  return parts.join(' · ')
}

export function citationPanelTitle(citation: Citation): string {
  const source = citation.source
  if (source?.company_name && source.ticker) {
    return `${source.company_name} (${source.ticker})`
  }
  return `Source ${citation.citation_index + 1}`
}

export function citationPanelSubtitle(citation: Citation): string | null {
  const bits: string[] = []
  const source = citation.source
  if (source?.filing_type) bits.push(source.filing_type)
  if (source?.filing_date) bits.push(source.filing_date)
  if (citation.page_label) bits.push(`Page ${citation.page_label}`)
  if (source?.section_label) bits.push(source.section_label)
  return bits.length > 0 ? bits.join(' · ') : null
}

export function isGroundingFailureMessage(text: string): boolean {
  return text.includes('could not produce a grounded answer')
}
