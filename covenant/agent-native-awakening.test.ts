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
    expect(governanceLedger.records).toEqual([{
      event: 'CURATION_PENDING',
      stewardId: 'steward-1',
      historicalEventId: event.id,
      timestamp: '2026-10-03T00:00:00.000Z',
    }, {
      event: 'CURATION_DEPLOYED',
      stewardId: 'steward-1',
      historicalEventId: event.id,
      timestamp: '2026-10-03T00:00:00.000Z',
    }])
    runtime.stop()
  })

  it('bounds provenance reference counts and aggregate size at the gateway', () => {
    expect(() => sanitize({
      ...event,
      provenance: Array(33).fill('archive:source'),
    })).toThrow('too many provenance references')
    expect(() => sanitize({
      ...event,
      provenance: Array(9).fill('x'.repeat(1000)),
    })).toThrow('provenance is too large')
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
          return { summary: 'The source is fragmentary.', provenance: event.provenance, completeness: 'incomplete' }
        },
      },
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Do not fabricate.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('Incomplete curation must begin with "record incomplete"')
    expect(relational.deployed).toHaveLength(0)
    expect(governanceLedger.records[0].event).toBe('CURATION_REJECTED')
    runtime.stop()
  })

  it('bounds curator provenance and records intent before idempotent deployment', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const governanceLedger = mockGovernanceLedger()
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: {
        async curate() {
          return {
            summary: event.summary,
            provenance: Array(33).fill(event.provenance[0]),
            completeness: 'complete',
          }
        },
      },
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('too many provenance references')
    expect(relational.deployed).toHaveLength(0)
    expect(governanceLedger.records[0].event).toBe('CURATION_REJECTED')
    runtime.stop()

    const oversizedEvent = {
      ...event,
      provenance: Array(8).fill('x'.repeat(1000)),
    }
    const oversizedCatalog = mockCatalog()
    const oversizedRelational = mockRelational()
    const oversizedLedger = mockGovernanceLedger()
    const oversizedRuntime = await awakenAgentNativeCore({
      catalog: oversizedCatalog,
      relational: oversizedRelational,
      curator: {
        async curate() {
          return {
            summary: oversizedEvent.summary,
            provenance: Array(9).fill(oversizedEvent.provenance[0]),
            completeness: 'complete',
          }
        },
      },
      governanceLedger: oversizedLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })
    await expect(oversizedCatalog.emit(oversizedEvent)).rejects.toThrow('provenance is too large')
    expect(oversizedRelational.deployed).toHaveLength(0)
    oversizedRuntime.stop()

    const secondCatalog = mockCatalog()
    const secondRelational = mockRelational()
    const secondLedger = mockGovernanceLedger()
    const order: string[] = []
    const secondAppend = secondLedger.append
    secondLedger.append = (record) => {
      order.push(record.event)
      secondAppend(record)
    }
    const secondDeploy = secondRelational.deployComponent
    secondRelational.deployComponent = async (component) => {
      order.push('deploy')
      await secondDeploy(component)
    }
    const secondRuntime = await awakenAgentNativeCore({
      catalog: secondCatalog,
      relational: secondRelational,
      curator: mockCurator(),
      governanceLedger: secondLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })
    await secondCatalog.emit(event)
    await secondCatalog.emit(event)
    expect(order).toEqual([
      'CURATION_PENDING',
      'deploy',
      'CURATION_DEPLOYED',
      'CURATION_PENDING',
      'deploy',
      'CURATION_DEPLOYED',
    ])
    expect(secondRelational.deployed).toHaveLength(1)
    secondRuntime.stop()
  })

  it('does not deploy when the durable curation intent cannot be recorded', async () => {
    const catalog = mockCatalog()
    const relational = mockRelational()
    const governanceLedger = mockGovernanceLedger()
    governanceLedger.append = (record) => {
      if (record.event === 'CURATION_PENDING') {
        throw new Error('governance persistence unavailable')
      }
      governanceLedger.records.push(record)
    }
    const runtime = await awakenAgentNativeCore({
      catalog,
      relational,
      curator: mockCurator(),
      governanceLedger,
      stewardId: 'steward-1',
      systemPrompt: 'Preserve historical fidelity.',
    })

    await expect(catalog.emit(event)).rejects.toThrow('governance persistence unavailable')
    expect(relational.deployed).toHaveLength(0)
    runtime.stop()
  })
})
