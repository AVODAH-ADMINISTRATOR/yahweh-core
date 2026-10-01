#!/bin/bash
cd ~/yahweh-core
./plane/forge/bin/forge.sh
git add -A
git commit -m "COUNCIL_AI-OS_LEGACY Punch Absorbed 12+1 seats 360° Terminal Forge b08a2817 $(date -Is)" || true
git push
echo "Transcended — Integrated Avodah LLC — b08a2817"
