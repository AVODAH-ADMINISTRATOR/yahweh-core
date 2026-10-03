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

  it('bounds catalog provenance references and their size', () => {
    expect(() => sanitize({ ...event, provenance: Array(101).fill('archive:source') })).toThrow('supported limit')
    expect(() => sanitize({ ...event, provenance: ['x'.repeat(513)] })).toThrow('too long')
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
    expect(governanceLedger.records.map((record) => record.event)).toEqual([
      'CURATION_APPROVED',
      'CURATION_DEPLOYED',
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

  it('requires explicit incomplete wording when curator marks a record incomplete', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const governanceLedger = mockGovernanceLedger()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: {
        async curate() {
          return { summary: 'partial record missing source details', provenance: event.provenance, completeness: 'incomplete' }
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

  it('bounds curator provenance output', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: {
        async curate() {
          return { summary: event.summary, provenance: Array(101).fill(event.provenance[0]), completeness: 'complete' }
        },
      },
      governanceLedger: mockGovernanceLedger(),
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('supported limit')
    expect(relational.deployed).toHaveLength(0)
    runtime.stop()
  })

  it('persists governance approval before deployment', async () => {
    const catalog = mockCatalog()
    const deployedAndRecorded: string[] = []
    const relational = mockRelational()
    const governanceLedger = {
      append(record: { event: string }) {
        deployedAndRecorded.push(`record:${record.event}`)
      },
    }
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational: {
        async initialize() {},
        async deployComponent(component) {
          deployedAndRecorded.push('deploy')
          await relational.deployComponent(component)
        },
      },
      curator: mockCurator(),
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await catalog.emit(event)
    expect(deployedAndRecorded).toEqual(['record:CURATION_APPROVED', 'deploy', 'record:CURATION_DEPLOYED'])
    runtime.stop()
  })

  it('does not deploy when durable governance recording fails', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: mockCurator(),
      governanceLedger: {
        append() {
          throw new Error('governance storage unavailable')
        },
      },
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('governance storage unavailable')
    expect(relational.deployed).toHaveLength(0)
    runtime.stop()
  })
})
