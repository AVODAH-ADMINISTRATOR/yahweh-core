export interface HistoricalEvent {
  id: string
  title: string
  date: string
  summary: string
  provenance: string[]
}

const FIELD_LIMITS = {
  id: 256,
  title: 240,
  date: 100,
  summary: 5000,
  provenance: 1000,
} as const

const MAX_PROVENANCE_REFERENCES = 100
const TARGET_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/

function cleanText(value: unknown, field: string, maxLength: number): string {
  if (typeof value !== 'string') {
    throw new Error(`Invalid historical event: ${field} must be text`)
  }
  const cleaned = value.normalize('NFKC')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, '')
    .trim()
  if (!cleaned || cleaned.length > maxLength) {
    throw new Error(`Invalid historical event: ${field} is empty or too long`)
  }
  if (/<\/?[a-z][^>]*>/i.test(cleaned)) {
    throw new Error(`Invalid historical event: ${field} must be plain text`)
  }
  return cleaned
}

function cleanSummary(value: unknown): string {
  if (value === undefined || value === '') return ''
  return cleanText(value, 'summary', FIELD_LIMITS.summary)
}

export function sanitize(input: unknown): HistoricalEvent {
  if (input === null || typeof input !== 'object' || Array.isArray(input)) {
    throw new Error('Invalid historical event: expected an object')
  }

  const record = input as Record<string, unknown>
  if (!Array.isArray(record.provenance) || record.provenance.length === 0) {
    throw new Error('Invalid historical event: provenance is required')
  }
  if (record.provenance.length > MAX_PROVENANCE_REFERENCES) {
    throw new Error('Invalid historical event: too many provenance references')
  }

  const id = cleanText(record.id, 'id', FIELD_LIMITS.id)
  if (!TARGET_ID_PATTERN.test(id)) {
    throw new Error('Invalid historical event: id must be a valid target identifier')
  }

  return {
    id,
    title: cleanText(record.title, 'title', FIELD_LIMITS.title),
    date: cleanText(record.date, 'date', FIELD_LIMITS.date),
    summary: cleanSummary(record.summary),
    provenance: record.provenance.map((item) => cleanText(item, 'provenance', FIELD_LIMITS.provenance)),
  }
}
