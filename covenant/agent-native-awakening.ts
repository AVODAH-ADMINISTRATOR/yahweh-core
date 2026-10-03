import { MAX_PROVENANCE_ENTRIES, sanitize, type HistoricalEvent } from './sanctuary-gateway'

export interface CuratorDraft {
  summary: string
  provenance: string[]
  completeness: 'complete' | 'incomplete'
}

export interface CuratedComponent extends CuratorDraft {
  type: 'HistoricalCard'
  eventId: string
  title: string
  date: string
}

export interface DataCatalog {
  mount(tableName: string): Promise<void>
  subscribe(listener: (event: unknown) => Promise<void>): () => void
}

export interface RelationalCore {
  initialize(): Promise<void>
  deployComponent(component: CuratedComponent): Promise<void>
}

export interface CuratorAgent {
  curate(event: HistoricalEvent, systemPrompt: string): Promise<CuratorDraft>
}

export interface GovernanceRecord {
  event: 'CURATION_DEPLOYED' | 'CURATION_REJECTED'
  stewardId: string
  historicalEventId: string
  timestamp: string
}

export interface GovernanceLedger {
  append(record: GovernanceRecord): Promise<void> | void
}

export interface AwakeningDependencies {
  catalog: DataCatalog
  relational: RelationalCore
  curator: CuratorAgent
  governanceLedger: GovernanceLedger
  stewardId: string
  systemPrompt: string
  tableName?: string
  now?: () => Date
}

function curateDataOnly(event: HistoricalEvent, draft: CuratorDraft): CuratedComponent {
  if (draft === null || typeof draft !== 'object' || typeof draft.summary !== 'string') {
    throw new Error('Curator output must be structured historical data')
  }
  if (draft.completeness !== 'complete' && draft.completeness !== 'incomplete') {
    throw new Error('Curator output must declare completeness')
  }
  const summary = draft.summary.normalize('NFKC')
    .replace(/[\u0000-\u001F\u007F-\u009F]/g, '').trim()
  if (!summary || summary.length > 5000 || /<\/?[a-z][^>]*>/i.test(summary)) {
    throw new Error('Curator output summary must be bounded plain text')
  }
  if (draft.completeness === 'incomplete' && !/^record incomplete\b/i.test(summary)) {
    throw new Error('Incomplete curation must begin with "record incomplete"')
  }
  if (!event.summary && draft.completeness !== 'incomplete') {
    throw new Error('Events without source summaries must be marked incomplete')
  }
  if (!Array.isArray(draft.provenance) || draft.provenance.length === 0) {
    throw new Error('Curator output must include provenance')
  }
  if (draft.provenance.length > MAX_PROVENANCE_ENTRIES) {
    throw new Error('Curator output includes too many provenance entries')
  }

  const allowedProvenance = new Set(event.provenance)
  const provenance = draft.provenance.map((source) => {
    if (typeof source !== 'string' || !allowedProvenance.has(source)) {
      throw new Error('Curator output contains unsupported provenance')
    }
    return source
  })

  return {
    type: 'HistoricalCard',
    eventId: event.id,
    title: event.title,
    date: event.date,
    summary,
    provenance,
    completeness: draft.completeness,
  }
}

export async function awakenAgentNativeCore(dependencies: AwakeningDependencies): Promise<{ status: 'READY'; stop: () => void }> {
  const stewardId = dependencies.stewardId.trim()
  if (!stewardId || !dependencies.systemPrompt.trim()) {
    throw new Error('A steward identity and curator system prompt are required')
  }

  await dependencies.catalog.mount(dependencies.tableName ?? 'eon_generational_records')
  await dependencies.relational.initialize()

  const unsubscribe = dependencies.catalog.subscribe(async (rawEvent) => {
    let historicalEventId = 'unavailable'
    let rejected = true
    const record = async (result: GovernanceRecord['event']) => {
      await dependencies.governanceLedger.append({
        event: result,
        stewardId,
        historicalEventId,
        timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
      })
    }
    try {
      const event = sanitize(rawEvent)
      historicalEventId = event.id
      const draft = await dependencies.curator.curate(event, dependencies.systemPrompt)
      const component = curateDataOnly(event, draft)
      rejected = false
      await record('CURATION_DEPLOYED')
      rejected = true
      await dependencies.relational.deployComponent(component)
      rejected = false
    } finally {
      if (rejected) await record('CURATION_REJECTED')
    }
  })

  return { status: 'READY', stop: unsubscribe }
}
