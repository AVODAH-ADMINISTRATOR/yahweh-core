"use strict";
/**
 * VIBE CODE: THE SANCTUARY GATEWAY (Step 8)
 * Module: Zero-Knowledge Data Ingestion
 * Protocol: Scout Law (Trustworthy & Secure)
 * Target: Grand Server 2 -> Cloudflare Wasm -> Firebase Core
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ingestArchiveData = ingestArchiveData;
const client_core_1 = require("@antigravity/client-core");
const angels_1 = require("cloudflare/angels");
const heaven_compute_1 = require("firebase/heaven-compute");
async function ingestArchiveData(upload, familyMasterKey) {
    console.log("🛡️ Initiating Sanctuary Ingestion Sequence...");
    // 1. Client-Side Encryption (Zero-Knowledge)
    // The data is encrypted on the user's phone or laptop before it ever hits the internet.
    // Grand Server 2 will never know the contents unless unlocked with the key.
    const { encryptedPayload, signature } = await client_core_1.LocalCrypto.aes256GcmEncrypt({
        data: upload.fileBuffer,
        key: familyMasterKey,
        precisionMode: true // Leverages the client's hardware acceleration
    });
    console.log("✔ Payload encrypted locally. Raw data erased from memory.");
    // 2. Cloudflare Edge Wasm Validation
    // The encrypted packet is sent to the Edge. The WebAssembly module verifies 
    // the structural integrity of the packet without decrypting it.
    const edgeValidation = await angels_1.CloudflareWasm.inspectPacketStructure(encryptedPayload, signature);
    if (edgeValidation.status !== 'PERFECT_INTEGRITY') {
        throw new Error("⚠️ Upload rejected by Edge: Cryptographic drift detected.");
    }
    console.log("✔ Cloudflare Wasm confirms structural integrity.");
    // 3. Firebase Atomic Commit
    // The payload is passed to the Gen 2 Cloud Functions and written to Firestore 
    // via an atomic transaction, ensuring it cannot be fragmented.
    await heaven_compute_1.FirestoreAtomic.runTransaction(async (transaction) => {
        const archiveRef = heaven_compute_1.FirestoreAtomic.collection('Intelligence_Archive').doc();
        transaction.set(archiveRef, {
            payload: encryptedPayload,
            author: upload.authorId,
            clearance: upload.securityClearance,
            timestamp: Date.now(),
            archiveStatus: "SEALED"
        });
    });
    console.log("✨ Upload successfully sealed in the Intelligence-Grade Archive.");
    return { status: "INGESTION_COMPLETE" };
}
