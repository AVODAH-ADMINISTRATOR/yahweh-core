"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.awakenAgentNativeCore = awakenAgentNativeCore;
const sanctuary_gateway_1 = require("./sanctuary-gateway");
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
    if (draft.provenance.length > sanctuary_gateway_1.MAX_PROVENANCE_ENTRIES) {
        throw new Error('Curator output includes too many provenance entries');
    }
    const allowedProvenance = new Set(event.provenance);
    const provenance = draft.provenance.map((source) => {
        if (typeof source !== 'string' || !allowedProvenance.has(source)) {
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
    if (!stewardId || !dependencies.systemPrompt.trim()) {
        throw new Error('A steward identity and curator system prompt are required');
    }
    await dependencies.catalog.mount(dependencies.tableName ?? 'eon_generational_records');
    await dependencies.relational.initialize();
    const unsubscribe = dependencies.catalog.subscribe(async (rawEvent) => {
        let historicalEventId = 'unavailable';
        let rejected = true;
        const record = async (result) => {
            await dependencies.governanceLedger.append({
                event: result,
                stewardId,
                historicalEventId,
                timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
            });
        };
        try {
            const event = (0, sanctuary_gateway_1.sanitize)(rawEvent);
            historicalEventId = event.id;
            const draft = await dependencies.curator.curate(event, dependencies.systemPrompt);
            const component = curateDataOnly(event, draft);
            rejected = false;
            await record('CURATION_DEPLOYED');
            rejected = true;
            await dependencies.relational.deployComponent(component);
            rejected = false;
        }
        finally {
            if (rejected)
                await record('CURATION_REJECTED');
        }
    });
    return { status: 'READY', stop: unsubscribe };
}
