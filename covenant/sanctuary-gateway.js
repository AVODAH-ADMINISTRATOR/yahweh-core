"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sanitize = sanitize;
exports.MAX_PROVENANCE_REFERENCES = exports.MAX_PROVENANCE_REFERENCE_LENGTH = void 0;
exports.MAX_PROVENANCE_REFERENCES = 100;
exports.MAX_PROVENANCE_REFERENCE_LENGTH = 1000;
const FIELD_LIMITS = {
    id: 256,
    title: 240,
    date: 100,
    summary: 5000,
    provenance: exports.MAX_PROVENANCE_REFERENCE_LENGTH,
};
function cleanText(value, field, maxLength) {
    if (typeof value !== 'string') {
        throw new Error(`Invalid historical event: ${field} must be text`);
    }
    const cleaned = value.normalize('NFKC')
        .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, '')
        .trim();
    if (!cleaned || cleaned.length > maxLength) {
        throw new Error(`Invalid historical event: ${field} is empty or too long`);
    }
    if (/<\/?[a-z][^>]*>/i.test(cleaned)) {
        throw new Error(`Invalid historical event: ${field} must be plain text`);
    }
    return cleaned;
}
function cleanSummary(value) {
    if (value === undefined || value === '')
        return '';
    return cleanText(value, 'summary', FIELD_LIMITS.summary);
}
function sanitize(input) {
    if (input === null || typeof input !== 'object' || Array.isArray(input)) {
        throw new Error('Invalid historical event: expected an object');
    }
    const record = input;
    if (!Array.isArray(record.provenance) || record.provenance.length === 0) {
        throw new Error('Invalid historical event: provenance is required');
    }
    if (record.provenance.length > exports.MAX_PROVENANCE_REFERENCES) {
        throw new Error(`Invalid historical event: provenance exceeds ${exports.MAX_PROVENANCE_REFERENCES} references`);
    }
    return {
        id: cleanText(record.id, 'id', FIELD_LIMITS.id),
        title: cleanText(record.title, 'title', FIELD_LIMITS.title),
        date: cleanText(record.date, 'date', FIELD_LIMITS.date),
        summary: cleanSummary(record.summary),
        provenance: record.provenance.map((item) => cleanText(item, 'provenance', FIELD_LIMITS.provenance)),
    };
}
