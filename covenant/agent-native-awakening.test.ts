import { describe, expect, it } from 'vitest'
import { awakenAgentNativeCore } from './agent-native-awakening'
import { mockCatalog, mockCurator, mockGovernanceLedger, mockRelational } from './agent-native-awakening.mocks'
import { sanitize } from './sanctuary-gateway'

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

  it('mounts the archive, sanitizes history, and deploys one data-only component', async () => {
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
    expect(governanceLedger.records).toEqual([
      {
        event: 'CURATION_APPROVED',
        stewardId: 'steward-1',
        historicalEventId: event.id,
        timestamp: '2026-10-03T00:00:00.000Z',
      },
      {
        event: 'CURATION_DEPLOYED',
        stewardId: 'steward-1',
        historicalEventId: event.id,
        timestamp: '2026-10-03T00:00:00.000Z',
      },
    ])
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

  it('rejects invalid target identifiers and oversized catalog provenance', () => {
    expect(() => sanitize({ ...event, id: '../outside' })).toThrow('target identifier')
    expect(() => sanitize({ ...event, provenance: Array(101).fill(event.provenance[0]) })).toThrow('too many provenance')
    expect(() => sanitize({ ...event, provenance: ['x'.repeat(1001)] })).toThrow('too long')
  })

  it('bounds curator provenance output', async () => {
    const catalog = mockCatalog()
    const provenance = Array.from({ length: 100 }, (_, index) => `archive:source-${index}`)
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational: mockRelational(),
      curator: {
        async curate() {
          return { summary: event.summary, provenance: [...provenance, provenance[0]], completeness: 'complete' }
        },
      },
      governanceLedger: mockGovernanceLedger(),
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await expect(catalog.emit({ ...event, provenance })).rejects.toThrow('too many provenance')
    runtime.stop()
  })

  it('rejects an unsafe catalog table name before mounting', async () => {
    const catalog = mockCatalog()
    await expect(awakenAgentNativeCore({
      catalog,
      relational: mockRelational(),
      curator: mockCurator(),
      governanceLedger: mockGovernanceLedger(),
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
      tableName: 'records; DROP TABLE records',
    })).rejects.toThrow('table name')
    expect(catalog.mounted).toEqual([])
  })

  it('serializes governance writes and records approval before deployment', async () => {
    const catalog = mockCatalog()
    const actions: string[] = []
    let activeWrites = 0
    let maximumActiveWrites = 0
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational: {
        async initialize() {},
        async deployComponent(component) {
          actions.push(`deploy:${component.eventId}`)
        },
      },
      curator: mockCurator(),
      governanceLedger: {
        async append(record) {
          activeWrites += 1
          maximumActiveWrites = Math.max(maximumActiveWrites, activeWrites)
          actions.push(`ledger:${record.event}:${record.historicalEventId}`)
          await new Promise((resolve) => setTimeout(resolve, 5))
          actions.push(`ledger-durable:${record.event}:${record.historicalEventId}`)
          activeWrites -= 1
        },
      },
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await Promise.all([
      catalog.emit(event),
      catalog.emit({ ...event, id: 'founders-day-1963' }),
    ])

    expect(maximumActiveWrites).toBe(1)
    expect(actions.indexOf(`ledger-durable:CURATION_APPROVED:${event.id}`)).toBeLessThan(actions.indexOf(`deploy:${event.id}`))
    expect(actions.indexOf('ledger-durable:CURATION_APPROVED:founders-day-1963')).toBeLessThan(actions.indexOf('deploy:founders-day-1963'))
    runtime.stop()
  })

  it('does not deploy when approval cannot be durably recorded', async () => {
    const catalog = mockCatalog()
    const deployed: unknown[] = []
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational: {
        async initialize() {},
        async deployComponent(component) {
          deployed.push(component)
        },
      },
      curator: mockCurator(),
      governanceLedger: {
        async append(record) {
          if (record.event === 'CURATION_APPROVED') throw new Error('ledger unavailable')
        },
      },
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('ledger unavailable')
    expect(deployed).toHaveLength(0)
    runtime.stop()
  })

  it('requires explicit incomplete wording when curator marks a record incomplete', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const governanceLedger = mockGovernanceLedger()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: {
        async curate() {
          return { summary: 'Evidence is insufficient.', provenance: event.provenance, completeness: 'incomplete' }
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
})
