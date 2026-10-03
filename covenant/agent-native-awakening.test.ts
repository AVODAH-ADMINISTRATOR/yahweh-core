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
    const deployComponent = relational.deployComponent
    relational.deployComponent = async (component) => {
      expect(governanceLedger.records.map((record) => record.event)).toEqual(['CURATION_AUTHORIZED'])
      await deployComponent(component)
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
    expect(governanceLedger.records.map((record) => record.event)).toEqual([
      'CURATION_AUTHORIZED',
      'CURATION_DEPLOYED',
    ])
    expect(governanceLedger.records[0]).toMatchObject({
      stewardId: 'steward-1',
      historicalEventId: event.id,
      timestamp: '2026-10-03T00:00:00.000Z',
    })
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
          return { summary: 'Historical details are unavailable.', provenance: event.provenance, completeness: 'incomplete' }
        },
      },
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Do not fabricate.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('begin with \"record incomplete\"')
    expect(relational.deployed).toHaveLength(0)
    expect(governanceLedger.records[0].event).toBe('CURATION_REJECTED')
    runtime.stop()
  })

  it('bounds catalog and curator provenance reference counts', async () => {
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

    await expect(catalog.emit({ ...event, provenance: Array(101).fill('archive:source') }))
      .rejects.toThrow('provenance exceeds 100 references')
    expect(curator.inspected).toHaveLength(0)

    const oversizedCurator = {
      async curate() {
        return {
          summary: event.summary,
          provenance: Array(101).fill(event.provenance[0]),
          completeness: 'complete' as const,
        }
      },
    }
    runtime.stop()
    const secondCatalog = mockCatalog()
    const secondRelational = mockRelational()
    const secondLedger = mockGovernanceLedger()
    const secondRuntime = await awakenAgentNativeCore({
      catalog: secondCatalog,
      relational: secondRelational,
      curator: oversizedCurator,
      governanceLedger: secondLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })
    await expect(secondCatalog.emit(event)).rejects.toThrow('provenance exceeds 100 references')
    expect(secondRelational.deployed).toHaveLength(0)
    expect(secondLedger.records.at(-1)?.event).toBe('CURATION_REJECTED')
    secondRuntime.stop()
  })

  it('does not deploy when durable governance authorization fails', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: mockCurator(),
      governanceLedger: {
        async append() {
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
