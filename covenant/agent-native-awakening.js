"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.awakenAgentNativeCore = awakenAgentNativeCore;
const sanctuary_gateway_1 = require("./sanctuary-gateway");
const MAX_PROVENANCE_REFERENCES = 100;
const MAX_PROVENANCE_REFERENCE_LENGTH = 1000;
const IDENTIFIER_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/;
const TABLE_NAME_PATTERN = /^[A-Za-z_][A-Za-z0-9_]{0,127}$/;
const GOVERNANCE_EVENTS = new Set([
    'CURATION_APPROVED',
    'CURATION_DEPLOYED',
    'CURATION_REJECTED',
]);
function curateDataOnly(event, draft) {
    if (draft === null || typeof draft !== 'object' || typeof draft.summary !== 'string') {
        throw new Error('Curator output must be structured historical data');
    }
    if (draft.completeness !== 'complete' && draft.completeness !== 'incomplete') {
        throw new Error('Curator output must declare completeness');
    }
    const summary = draft.summary.normalize('NFKC')
        .replace(/[\u0000-\u001F\u007F-\u009F]/g, '').trim();
    if (!summary || summary.length > 5000 || /<\/?[a-z][^>]*>/i.test(summary)) {
        throw new Error('Curator output summary must be bounded plain text');
    }
    if (draft.completeness === 'incomplete' && !/^record incomplete\b/i.test(summary)) {
        throw new Error('Incomplete curation must begin with "record incomplete"');
    }
    if (!event.summary && draft.completeness !== 'incomplete') {
        throw new Error('Events without source summaries must be marked incomplete');
    }
    if (!Array.isArray(draft.provenance) || draft.provenance.length === 0) {
        throw new Error('Curator output must include provenance');
    }
    if (draft.provenance.length > MAX_PROVENANCE_REFERENCES) {
        throw new Error('Curator output has too many provenance references');
    }
    const allowedProvenance = new Set(event.provenance);
    const provenance = draft.provenance.map((source) => {
        if (typeof source !== 'string' || source.length > MAX_PROVENANCE_REFERENCE_LENGTH || !allowedProvenance.has(source)) {
            throw new Error('Curator output contains unsupported provenance');
        }
        return source;
    });
    return {
        type: 'HistoricalCard',
        eventId: event.id,
        title: event.title,
        date: event.date,
        summary,
        provenance,
        completeness: draft.completeness,
    };
}
async function awakenAgentNativeCore(dependencies) {
    const stewardId = dependencies.stewardId.trim();
    if (!IDENTIFIER_PATTERN.test(stewardId) || !dependencies.systemPrompt.trim()) {
        throw new Error('A valid steward identity and curator system prompt are required');
    }
    const tableName = dependencies.tableName ?? 'eon_generational_records';
    if (!TABLE_NAME_PATTERN.test(tableName)) {
        throw new Error('A valid catalog table name is required');
    }
    await dependencies.catalog.mount(tableName);
    await dependencies.relational.initialize();
    let ledgerWrites = Promise.resolve();
    const appendGovernanceRecord = (record) => {
        if (!GOVERNANCE_EVENTS.has(record.event) || !IDENTIFIER_PATTERN.test(record.stewardId) ||
            !IDENTIFIER_PATTERN.test(record.historicalEventId) || Number.isNaN(Date.parse(record.timestamp))) {
            return Promise.reject(new Error('Invalid sealed governance record'));
        }
        const write = ledgerWrites.then(() => dependencies.governanceLedger.append(record));
        ledgerWrites = write.catch(() => undefined);
        return write;
    };
    const unsubscribe = dependencies.catalog.subscribe(async (rawEvent) => {
        let historicalEventId = 'unavailable';
        let result = 'CURATION_REJECTED';
        try {
            const event = (0, sanctuary_gateway_1.sanitize)(rawEvent);
            historicalEventId = event.id;
            const draft = await dependencies.curator.curate(event, dependencies.systemPrompt);
            const component = curateDataOnly(event, draft);
            await appendGovernanceRecord({
                event: 'CURATION_APPROVED',
                stewardId,
                historicalEventId,
                timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
            });
            await dependencies.relational.deployComponent(component);
            result = 'CURATION_DEPLOYED';
        }
        finally {
            await appendGovernanceRecord({
                event: result,
                stewardId,
                historicalEventId,
                timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
            });
        }
    });
    return { status: 'READY', stop: unsubscribe };
}
