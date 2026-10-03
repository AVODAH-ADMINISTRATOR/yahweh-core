import type {
  CuratorAgent,
  CuratorDraft,
  CuratedComponent,
  DataCatalog,
  GovernanceLedger,
  GovernanceRecord,
  RelationalCore,
} from './agent-native-awakening'
import type { HistoricalEvent } from './sanctuary-gateway'

export function mockCatalog() {
  const mounted: string[] = []
  const listeners = new Set<(event: unknown) => Promise<void>>()
  const catalog: DataCatalog = {
    async mount(tableName) {
      mounted.push(tableName)
    },
    subscribe(listener) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
  }

  return {
    ...catalog,
    mounted,
    async emit(event: unknown) {
      await Promise.all([...listeners].map((listener) => listener(event)))
    },
  }
}

export function mockRelational() {
  const initialized: boolean[] = []
  const deployed: CuratedComponent[] = []
  const relational: RelationalCore = {
    async initialize() {
      initialized.push(true)
    },
    async deployComponent(component) {
      deployed.push(component)
    },
  }
  return { ...relational, initialized, deployed }
}

export function mockCurator() {
  const inspected: HistoricalEvent[] = []
  const curator: CuratorAgent = {
    async curate(event): Promise<CuratorDraft> {
      inspected.push(event)
      return {
        summary: event.summary || 'record incomplete: source summary is absent',
        provenance: event.provenance,
        completeness: event.summary ? 'complete' : 'incomplete',
      }
    },
  }
  return { ...curator, inspected }
}

export function mockGovernanceLedger() {
  const records: GovernanceRecord[] = []
  const ledger: GovernanceLedger = {
    async append(record) {
      records.push(record)
      return { recordId: `governance-${records.length}`, durable: true }
    },
  }
  return { ...ledger, records }
}
