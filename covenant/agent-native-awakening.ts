import { sanitize, type HistoricalEvent } from './sanctuary-gateway'

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
  event: 'CURATION_PENDING' | 'CURATION_DEPLOYED' | 'CURATION_REJECTED'
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
  if (draft.provenance.length > 32) {
    throw new Error('Curator output contains too many provenance references')
  }

  const allowedProvenance = new Set(event.provenance)
  let provenanceSize = 0
  const provenance = Array.from(draft.provenance, (source) => {
    if (typeof source !== 'string' || !allowedProvenance.has(source)) {
      throw new Error('Curator output contains unsupported provenance')
    }
    provenanceSize += source.length
    if (provenanceSize > 8192) {
      throw new Error('Curator output provenance is too large')
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
    let component: CuratedComponent
    try {
      const event = sanitize(rawEvent)
      historicalEventId = event.id
      const draft = await dependencies.curator.curate(event, dependencies.systemPrompt)
      component = curateDataOnly(event, draft)
    } catch (error) {
      await dependencies.governanceLedger.append({
        event: 'CURATION_REJECTED',
        stewardId,
        historicalEventId,
        timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
      })
      throw error
    }

    const timestamp = (dependencies.now ?? (() => new Date()))().toISOString()
    await dependencies.governanceLedger.append({
      event: 'CURATION_PENDING',
      stewardId,
      historicalEventId,
      timestamp,
    })
    try {
      await dependencies.relational.deployComponent(component)
    } catch (error) {
      await dependencies.governanceLedger.append({
        event: 'CURATION_REJECTED',
        stewardId,
        historicalEventId,
        timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
      })
      throw error
    }
    await dependencies.governanceLedger.append({
      event: 'CURATION_DEPLOYED',
      stewardId,
      historicalEventId,
      timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
    })
  })

  return { status: 'READY', stop: unsubscribe }
}
