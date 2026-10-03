import { describe, expect, it } from 'vitest'
import { awakenAgentNativeCore } from './agent-native-awakening'
import { mockCatalog, mockCurator, mockGovernanceLedger, mockRelational } from './agent-native-awakening.mocks'
import { FIELD_LIMITS, sanitize } from './sanctuary-gateway'

const event = {
  id: 'founders-day-1962',
  title: 'Founders Day 1962',
  date: '1962',
  summary: 'A source-recorded Founders Day event.',
  provenance: ['archive:founders-day-1962'],
}

describe('dependency-injected historical curator', () => {
  it('gateway sanitizer rejects markup in historical text', () => {
    expect(() => sanitize({ ...event, title: '<script>not history</script>' })).toThrow('plain text')
  })

  it('gateway sanitizer bounds provenance reference counts', () => {
    const tooMany = Array.from({ length: FIELD_LIMITS.provenanceCount + 1 }, (_, index) => `archive:${index}`)
    expect(() => sanitize({ ...event, provenance: tooMany })).toThrow('too many provenance references')
  })

  it('mounts the archive, sanitizes history, records governance, then deploys one data-only component', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const curator = mockCurator()
    const governanceLedger = mockGovernanceLedger()
    const order: string[] = []
    const originalAppend = governanceLedger.append.bind(governanceLedger)
    governanceLedger.append = async (record) => {
      order.push(`governance:${record.event}`)
      return originalAppend(record)
    }
    const originalDeploy = relational.deployComponent.bind(relational)
    relational.deployComponent = async (component) => {
      order.push('deploy')
      return originalDeploy(component)
    }

    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator,
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
      now: () => new Date('2026-10-03T00:00:00.000Z'),
    })

    await catalog.emit({ ...event, untrustedHtml: '<script>remove me</script>' })

    expect(runtime.status).toBe('READY')
    expect(catalog.mounted).toEqual(['eon_generational_records'])
    expect(relational.initialized).toEqual([true])
    expect(curator.inspected).toEqual([event])
    expect(relational.deployed).toHaveLength(1)
    expect(relational.deployed[0]).toEqual({
      type: 'HistoricalCard',
      eventId: event.id,
      title: event.title,
      date: event.date,
      summary: event.summary,
      provenance: event.provenance,
      completeness: 'complete',
    })
    expect(governanceLedger.records).toEqual([{
      event: 'CURATION_DEPLOYED',
      stewardId: 'steward-1',
      historicalEventId: event.id,
      timestamp: '2026-10-03T00:00:00.000Z',
    }])
    expect(order).toEqual(['governance:CURATION_DEPLOYED', 'deploy'])
    runtime.stop()
  })

  it('rejects events without gateway provenance before curation or deployment', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const curator = mockCurator()
    const governanceLedger = mockGovernanceLedger()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator,
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await expect(catalog.emit({ ...event, provenance: [] })).rejects.toThrow('provenance is required')
    expect(curator.inspected).toHaveLength(0)
    expect(relational.deployed).toHaveLength(0)
    expect(governanceLedger.records[0].event).toBe('CURATION_REJECTED')
    runtime.stop()
  })

  it('requires explicit incomplete prefix when curator marks a record incomplete', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const governanceLedger = mockGovernanceLedger()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: {
        async curate() {
          return {
            summary: 'insufficient evidence without required prefix',
            provenance: event.provenance,
            completeness: 'incomplete',
          }
        },
      },
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Do not fabricate.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('record incomplete')
    expect(relational.deployed).toHaveLength(0)
    expect(governanceLedger.records[0].event).toBe('CURATION_REJECTED')
    runtime.stop()
  })

  it('bounds curator output provenance size and rejects oversized drafts', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const governanceLedger = mockGovernanceLedger()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: {
        async curate(historicalEvent) {
          return {
            summary: historicalEvent.summary,
            provenance: Array.from({ length: FIELD_LIMITS.provenanceCount + 1 }, () => historicalEvent.provenance[0]),
            completeness: 'complete',
          }
        },
      },
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Do not fabricate.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('provenance exceeds bound')
    expect(relational.deployed).toHaveLength(0)
    expect(governanceLedger.records[0].event).toBe('CURATION_REJECTED')
    runtime.stop()
  })

  it('serializes concurrent catalog emissions through one governance/deploy writer', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const governanceLedger = mockGovernanceLedger()
    let active = 0
    let maxActive = 0
    const originalAppend = governanceLedger.append.bind(governanceLedger)
    governanceLedger.append = async (record) => {
      active += 1
      maxActive = Math.max(maxActive, active)
      await new Promise((resolve) => setTimeout(resolve, 5))
      active -= 1
      return originalAppend(record)
    }

    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: mockCurator(),
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await Promise.all([
      catalog.emit({ ...event, id: 'event-a' }),
      catalog.emit({ ...event, id: 'event-b' }),
      catalog.emit({ ...event, id: 'event-c' }),
    ])

    expect(maxActive).toBe(1)
    expect(governanceLedger.records).toHaveLength(3)
    expect(relational.deployed).toHaveLength(3)
    runtime.stop()
  })
})
