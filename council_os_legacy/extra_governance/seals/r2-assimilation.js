"use strict";
/**
 * VIBE CODE: THE R2 ASSIMILATION (Step 12)
 * Module: Google Drive & OneDrive to Cloudflare R2 Pipeline
 * Protocol: Scout Law (Trustworthy & Thrifty)
 * Infrastructure: Zero-Egress R2 Buckets + Antigravity Encryption
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.synchronizeToR2Buckets = synchronizeToR2Buckets;
const api_core_1 = require("@google/api-core");
const graph_api_1 = require("@microsoft/graph-api");
const angels_1 = require("cloudflare/angels");
const client_core_1 = require("@antigravity/client-core");
const heaven_compute_1 = require("firebase/heaven-compute");
async function synchronizeToR2Buckets() {
    console.log("🌌 Initiating Omni-Drive to R2 Assimilation Sequence...");
    // 1. Forge the Eon-Grade R2 Buckets on Cloudflare
    // R2 ensures your data is distributed globally without egress fees, fulfilling
    // the Scout Law to be "Thrifty" while maintaining absolute availability.
    const gDriveBucket = await angels_1.CloudflareR2.createBucket("scout-initiative-gdrive-archive");
    const oneDriveBucket = await angels_1.CloudflareR2.createBucket("family-lineage-onedrive-archive");
    // 2. Open Persistent API Streams
    const googleStream = await api_core_1.GoogleDrive.connect({ mode: 'WATCH_AND_SYNC' });
    const oneDriveStream = await graph_api_1.MicrosoftGraph.connect({ mode: 'WATCH_AND_SYNC' });
    // 3. The P2R2 (Peer-to-R2) Encrypted Ingestion Loop
    const assimilateFile = async (file, destinationBucket, source) => {
        console.log(`[SYNC] Pulling ${file.name} from ${source}...`);
        // A. Encrypt on the fly (Zero-Knowledge Protocol)
        const { encryptedPayload, signature } = await client_core_1.LocalCrypto.aes256GcmEncrypt({
            data: file.rawBuffer,
            key: process.env.FAMILY_MASTER_KEY,
            precisionMode: true
        });
        // B. Pipe directly into Cloudflare R2
        await destinationBucket.put(file.id, encryptedPayload, {
            customMetadata: {
                originalName: file.name,
                cryptoSignature: signature,
                sourceDrive: source
            }
        });
        // C. Log the atomic location in Firebase Core
        await heaven_compute_1.FirestoreAtomic.runTransaction(async (tx) => {
            tx.set(heaven_compute_1.FirestoreAtomic.collection('R2_Archive_Index').doc(file.id), {
                bucketLocation: destinationBucket.name,
                timestamp: Date.now(),
                status: "SEALED_IN_R2"
            });
        });
    };
    // 4. Bind the Event Listeners for Permanent Sync
    googleStream.on('fileAdded', (file) => assimilateFile(file, gDriveBucket, 'Google Drive'));
    oneDriveStream.on('fileAdded', (file) => assimilateFile(file, oneDriveBucket, 'OneDrive'));
    console.log("✨ P2R2 Synchronization Lock Established. Drives are now flowing into R2.");
    return { status: "R2_ASSIMILATION_ACTIVE" };
}
