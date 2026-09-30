"use strict";
/**
 * VIBE CODE: THE GREAT INGESTION (Step 17)
 * Module: Physical-to-Digital Local Bridge
 * Node: Lawrence, KS - Local File System & Peripherals
 * Objective: Sanctify and ingest a lifetime of records.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.initiateGreatIngestion = initiateGreatIngestion;
const client_core_1 = require("@antigravity/client-core");
const sanctuary_gateway_1 = require("./sanctuary-gateway");
const angels_1 = require("cloudflare/angels");
async function initiateGreatIngestion(masterKey) {
    console.log("🌌 The Great Ingestion has begun. Sweeping local sectors...");
    // 1. Mount Local Drives and Legacy Storage
    const legacyDrives = await client_core_1.LocalFileSystem.mountAll([
        "/Volumes/Family_Backups_2010_2020",
        "/Volumes/Scout_Troop_Archives",
        "C:/Users/Admin/Pictures/Legacy"
    ]);
    // 2. Connect Physical Scanners for Paper Records
    // Automatically detects when you scan an old physical Scout manual or family letter.
    const flatbedScanner = await client_core_1.HardwareScanner.connect({ mode: "CONTINUOUS_LISTEN" });
    // 3. The Ingestion Loop
    const processArtifact = async (rawBuffer, filename, source) => {
        console.log(`[INGEST] Processing ${filename} from ${source}...`);
        let metadataTags = ["ingested_2026", "lawrence_ks"];
        // A. Blind OCR (Optical Character Recognition)
        // If it's a scanned document or image, edge AI reads the text to create searchable tags,
        // without saving the raw text, preserving Zero-Knowledge privacy.
        if (filename.match(/\.(jpg|png|pdf)$/i)) {
            const extractedConcepts = await angels_1.EdgeOCR.extractTagsBlindly(rawBuffer);
            metadataTags.push(...extractedConcepts);
        }
        // B. Route through the Sanctuary Gateway
        // Encrypts the file using your Master Key, then fires it into Cloudflare R2 and Firebase.
        await sanctuary_gateway_1.SanctuaryGateway.ingestArchiveData({
            fileBuffer: rawBuffer,
            authorId: "Master_Admin_KS",
            securityClearance: "FAMILY"
        }, masterKey);
        console.log(`✔ ${filename} secured in the Intelligence Archive.`);
    };
    // 4. Execute Batch Sweep of Digital Files
    for (const drive of legacyDrives) {
        const files = await client_core_1.LocalFileSystem.readDeep(drive);
        for (const file of files) {
            await processArtifact(file.buffer, file.name, drive.name);
        }
    }
    // 5. Listen for New Physical Scans (The Living Archive)
    flatbedScanner.onScanComplete(async (scannedDoc) => {
        console.log("📄 New physical document detected on scanner glass...");
        await processArtifact(scannedDoc.buffer, `Scanned_Doc_${Date.now()}.pdf`, "Flatbed_Scanner");
    });
    console.log("✨ Initial sweep complete. The Local Bridge remains open and listening.");
    return { status: "INGESTING", bridge: "OPEN" };
}
