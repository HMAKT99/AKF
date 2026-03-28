#!/usr/bin/env bash
# AKF + ExifTool — AI provenance in EXIF/XMP metadata
#
# Read and write AKF trust metadata using ExifTool.
# Works with any image, video, or document format ExifTool supports.
#
# Usage:
#   pip install akf
#   brew install exiftool  # or your preferred install method
#   bash exiftool_provenance.sh
#
# Learn more: https://akf.dev

set -e

echo "=== AKF + ExifTool: AI Provenance in EXIF/XMP ==="
echo ""

# Step 1: Create a sample image
python3 -c "
from PIL import Image
img = Image.new('RGB', (100, 100), color=(60, 120, 200))
img.save('/tmp/akf-sample.jpg')
" 2>/dev/null || echo "Creating sample image requires Pillow"

echo "1. Created sample image"

# Step 2: Stamp with AKF
akf stamp /tmp/akf-sample.jpg --agent dall-e-3 --evidence "generated from text prompt"
echo "2. Stamped with AKF trust metadata"

# Step 3: Read with ExifTool
echo ""
echo "3. ExifTool reads the metadata:"
exiftool /tmp/akf-sample.jpg 2>/dev/null | grep -i "akf\|comment\|user" || echo "   (install exiftool to see EXIF output)"

# Step 4: Read with AKF
echo ""
echo "4. AKF reads it back:"
akf read /tmp/akf-sample.jpg

# Step 5: Write custom AI tags with ExifTool
echo ""
echo "5. Add custom AI tags with ExifTool:"
echo "   exiftool -UserComment='AKF:{\"v\":\"1.0\",\"agent\":\"dall-e-3\",\"t\":0.70}' image.jpg"
echo "   exiftool -XMP:Description='AI-generated image with AKF trust metadata' image.jpg"

# Cleanup
rm -f /tmp/akf-sample.jpg

echo ""
echo "✅ AI provenance in EXIF/XMP — readable by ExifTool and AKF"
echo "   Learn more: https://akf.dev"
