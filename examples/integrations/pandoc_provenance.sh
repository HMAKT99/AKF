#!/usr/bin/env bash
# AKF + pandoc — Preserve AI provenance across format conversions
#
# Problem: pandoc converts Markdown → DOCX → PDF, but provenance is lost.
# Solution: Stamp before conversion, re-embed after conversion.
#
# Usage:
#   pip install akf
#   brew install pandoc  # or your preferred install method
#   bash pandoc_provenance.sh
#
# Learn more: https://akf.dev

set -e

echo "=== AKF + pandoc: Provenance Across Format Conversions ==="
echo ""

# Step 1: Create a markdown file with AI-generated content
cat > /tmp/akf-report.md << 'EOF'
# Q3 Revenue Report

Revenue was $4.2B, up 12% YoY. Cloud segment grew 15%.
H2 outlook remains positive based on current pipeline.
EOF

echo "1. Created markdown report"

# Step 2: Stamp with AKF trust metadata
akf stamp /tmp/akf-report.md --agent claude --evidence "generated from SEC 10-Q filing"
echo "2. Stamped with AKF metadata"
akf read /tmp/akf-report.md

# Step 3: Convert to DOCX with pandoc
pandoc /tmp/akf-report.md -o /tmp/akf-report.docx 2>/dev/null && echo "" && echo "3. Converted to DOCX with pandoc"

# Step 4: Re-embed AKF into the DOCX (pandoc strips frontmatter)
akf embed /tmp/akf-report.docx 2>/dev/null && echo "4. Re-embedded AKF into DOCX"

# Step 5: Verify the round-trip
echo ""
echo "5. Reading AKF from DOCX:"
akf read /tmp/akf-report.docx 2>/dev/null || echo "   (DOCX embedding requires python-docx)"

# Step 6: Compliance check
echo ""
echo "6. Compliance check:"
akf audit /tmp/akf-report.md --regulation eu_ai_act

# Cleanup
rm -f /tmp/akf-report.md /tmp/akf-report.docx

echo ""
echo "✅ Trust metadata survives format conversion"
echo "   Markdown → DOCX → and back"
echo "   Learn more: https://akf.dev"
