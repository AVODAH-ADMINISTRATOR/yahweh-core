"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.awakenAgentNativeCore = awakenAgentNativeCore;
const sanctuary_gateway_1 = require("./sanctuary-gateway");
const INCOMPLETE_PREFIX = 'record incomplete';
function createWriteQueue() {
    let tail = Promise.resolve();
    return function enqueue(work) {
        const run = tail.then(work, work);
        tail = run.then(() => undefined, () => undefined);
        return run;
    };
}
function curateDataOnly(event, draft) {
    if (draft === null || typeof draft !== 'object' || typeof draft.summary !== 'string') {
        throw new Error('Curator output must be structured historical data');
    }
    if (draft.completeness !== 'complete' && draft.completeness !== 'incomplete') {
        throw new Error('Curator output must declare completeness');
    }
    const summary = draft.summary.normalize('NFKC')
        .replace(/[\u0000-\u001F\u007F-\u009F]/g, '').trim();
    if (!summary || summary.length > sanctuary_gateway_1.FIELD_LIMITS.summary || /<\/?[a-z][^>]*>/i.test(summary)) {
        throw new Error('Curator output summary must be bounded plain text');
    }
    if (draft.completeness === 'incomplete' && !summary.startsWith(INCOMPLETE_PREFIX)) {
        throw new Error('Incomplete curation must begin with "record incomplete"');
    }
    if (!event.summary && draft.completeness !== 'incomplete') {
        throw new Error('Events without source summaries must be marked incomplete');
    }
    if (!Array.isArray(draft.provenance) || draft.provenance.length === 0) {
        throw new Error('Curator output must include provenance');
    }
    if (draft.provenance.length > sanctuary_gateway_1.FIELD_LIMITS.provenanceCount) {
        throw new Error('Curator output provenance exceeds bound');
    }
    const allowedProvenance = new Set(event.provenance);
    const provenance = draft.provenance.map((source) => {
        if (typeof source !== 'string' || !allowedProvenance.has(source)) {
            throw new Error('Curator output contains unsupported provenance');
        }
        if (source.length > sanctuary_gateway_1.FIELD_LIMITS.provenance) {
            throw new Error('Curator output provenance exceeds bound');
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
    if (!stewardId || !dependencies.systemPrompt.trim()) {
        throw new Error('A steward identity and curator system prompt are required');
    }
    await dependencies.catalog.mount(dependencies.tableName ?? 'eon_generational_records');
    await dependencies.relational.initialize();
    const enqueue = createWriteQueue();
    const unsubscribe = dependencies.catalog.subscribe((rawEvent) => enqueue(async () => {
        let historicalEventId = 'unavailable';
        let deployedRecorded = false;
        const timestamp = (dependencies.now ?? (() => new Date()))().toISOString();
        try {
            const event = (0, sanctuary_gateway_1.sanitize)(rawEvent);
            historicalEventId = event.id;
            const draft = await dependencies.curator.curate(event, dependencies.systemPrompt);
            const component = curateDataOnly(event, draft);
            await dependencies.governanceLedger.append({
                event: 'CURATION_DEPLOYED',
                stewardId,
                historicalEventId,
                timestamp,
            });
            deployedRecorded = true;
            await dependencies.relational.deployComponent(component);
        }
        catch (error) {
            if (!deployedRecorded) {
                await dependencies.governanceLedger.append({
                    event: 'CURATION_REJECTED',
                    stewardId,
                    historicalEventId,
                    timestamp,
                });
            }
            throw error;
        }
    }));
    return { status: 'READY', stop: unsubscribe };
}
