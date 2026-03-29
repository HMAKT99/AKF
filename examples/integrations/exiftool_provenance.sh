#!/usr/bin/env bash
# AKF + ExifTool — AI provenance via custom XMP namespace
#
# Usage:
#   cp exiftool-akf.config ~/.ExifTool_config
#   bash exiftool_provenance.sh
#
# Learn more: https://akf.dev

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== AKF + ExifTool: AI Provenance via XMP ==="
echo ""

# Step 1: Create a sample image
python3 -c "
from PIL import Image
img = Image.new('RGB', (100, 100), color=(60, 120, 200))
img.save('/tmp/akf-sample.jpg')
" 2>/dev/null && echo "1. Created sample image" || echo "1. Skipped (needs Pillow)"

# Step 2: Write AI provenance using custom XMP namespace
echo "2. Writing AI provenance tags..."
exiftool -config "$SCRIPT_DIR/exiftool-akf.config" \
  -XMP-akf:AIGenerated="true" \
  -XMP-akf:Agent="dall-e-3" \
  -XMP-akf:Model="dall-e-3" \
  -XMP-akf:TrustScore="0.70" \
  -XMP-akf:SourceTier="T5" \
  -XMP-akf:Source="text prompt" \
  -XMP-akf:Evidence="generated from user prompt" \
  -XMP-akf:GeneratedAt="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -XMP-akf:Classification="internal" \
  -overwrite_original \
  /tmp/akf-sample.jpg 2>/dev/null && echo "   Done" || echo "   (install exiftool to run)"

# Step 3: Read back with ExifTool
echo ""
echo "3. Reading AI provenance tags:"
exiftool -config "$SCRIPT_DIR/exiftool-akf.config" -G1 -XMP-akf:all /tmp/akf-sample.jpg 2>/dev/null || echo "   (install exiftool)"

# Step 4: Also read with AKF
echo ""
echo "4. Reading with AKF:"
akf read /tmp/akf-sample.jpg 2>/dev/null || echo "   (pip install akf)"

# Cleanup
rm -f /tmp/akf-sample.jpg

echo ""
echo "✅ AI provenance in XMP — readable by ExifTool and any XMP-aware tool"
echo ""
echo "Install: cp exiftool-akf.config ~/.ExifTool_config"
echo "Docs:    https://akf.dev"
