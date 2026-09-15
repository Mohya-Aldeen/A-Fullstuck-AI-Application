import type { Citation } from '@/lib/chat'

export function citationNumber(citation: Citation): number {
  return citation.citation_index + 1
}

export function citationCompany(citation: Citation): string {
  const source = citation.source
  if (source?.company_name) return source.company_name
  if (source?.ticker) return source.ticker
  return `Source ${citationNumber(citation)}`
}

export function citationTicker(citation: Citation): string | null {
  return citation.source?.ticker ?? null
}

export function citationFilingType(citation: Citation): string | null {
  return citation.source?.filing_type ?? null
}

export function citationFiscalYear(citation: Citation): number | null {
  const source = citation.source
  if (source?.filing_year != null) return source.filing_year
  if (source?.filing_date) {
    const year = Number(source.filing_date.slice(0, 4))
    return Number.isFinite(year) ? year : null
  }
  return null
}

export function citationLocation(citation: Citation): string | null {
  if (citation.page_label) return `p.${citation.page_label}`
  if (citation.source?.section_label) return citation.source.section_label
  return null
}

export type CitationField = { label: string; value: string; tabular?: boolean }

/** Structured metadata for the source panel — rendered as a definition list. */
export function citationFields(citation: Citation): CitationField[] {
  const fields: CitationField[] = []
  const source = citation.source
  const ticker = citationTicker(citation)
  if (ticker) fields.push({ label: 'Ticker', value: ticker, tabular: true })
  const filingType = citationFilingType(citation)
  if (filingType) fields.push({ label: 'Filing', value: filingType })
  const fiscalYear = citationFiscalYear(citation)
  if (fiscalYear) fields.push({ label: 'Fiscal year', value: `FY${fiscalYear}`, tabular: true })
  if (source?.section_label) fields.push({ label: 'Section', value: source.section_label })
  if (citation.page_label) fields.push({ label: 'Page', value: citation.page_label, tabular: true })
  if (source?.filing_date) {
    fields.push({ label: 'Filed', value: formatFilingDate(source.filing_date), tabular: true })
  }
  if (source?.accession_number) {
    fields.push({ label: 'Accession', value: source.accession_number, tabular: true })
  }
  return fields
}

function formatFilingDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)
}

export function isGroundingFailureMessage(text: string): boolean {
  return text.toLowerCase().includes('could not produce a grounded answer')
}

export function isInsufficientEvidenceMessage(text: string): boolean {
  const t = text.toLowerCase()
  return (
    t.includes('not enough evidence') ||
    t.includes('does not contain enough evidence') ||
    t.includes("doesn't contain enough evidence") ||
    t.includes('insufficient evidence') ||
    t.includes('no evidence in the corpus')
  )
}

export type AnswerSegment =
  | { type: 'text'; text: string }
  | { type: 'ref'; index: number }

/** Split answer text into prose and inline citation markers like `[1]`. */
export function parseAnswerSegments(text: string): AnswerSegment[] {
  const segments: AnswerSegment[] = []
  const pattern = /\[(\d{1,3})\]/g
  let cursor = 0
  let match: RegExpExecArray | null
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      segments.push({ type: 'text', text: text.slice(cursor, match.index) })
    }
    segments.push({ type: 'ref', index: Number(match[1]) })
    cursor = match.index + match[0].length
  }
  if (cursor < text.length) {
    segments.push({ type: 'text', text: text.slice(cursor) })
  }
  return segments
}

/** Split answer text into paragraphs on blank lines. */
export function splitParagraphs(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter((paragraph) => paragraph.length > 0)
}
