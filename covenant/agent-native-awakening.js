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
    if (draft.provenance.length > 32) {
        throw new Error('Curator output contains too many provenance references');
    }
    const allowedProvenance = new Set(event.provenance);
    let provenanceSize = 0;
    const provenance = Array.from(draft.provenance, (source) => {
        if (typeof source !== 'string' || !allowedProvenance.has(source)) {
            throw new Error('Curator output contains unsupported provenance');
        }
        provenanceSize += source.length;
        if (provenanceSize > 8192) {
            throw new Error('Curator output provenance is too large');
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
        let component;
        try {
            const event = (0, sanctuary_gateway_1.sanitize)(rawEvent);
            historicalEventId = event.id;
            const draft = await dependencies.curator.curate(event, dependencies.systemPrompt);
            component = curateDataOnly(event, draft);
        }
        catch (error) {
            await dependencies.governanceLedger.append({
                event: 'CURATION_REJECTED',
                stewardId,
                historicalEventId,
                timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
            });
            throw error;
        }
        const timestamp = (dependencies.now ?? (() => new Date()))().toISOString();
        await dependencies.governanceLedger.append({
            event: 'CURATION_PENDING',
            stewardId,
            historicalEventId,
            timestamp,
        });
        try {
            await dependencies.relational.deployComponent(component);
        }
        catch (error) {
            await dependencies.governanceLedger.append({
                event: 'CURATION_REJECTED',
                stewardId,
                historicalEventId,
                timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
            });
            throw error;
        }
        await dependencies.governanceLedger.append({
            event: 'CURATION_DEPLOYED',
            stewardId,
            historicalEventId,
            timestamp: (dependencies.now ?? (() => new Date()))().toISOString(),
        });
    });
    return { status: 'READY', stop: unsubscribe };
}
