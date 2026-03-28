"""
AKF + pypdf — AI provenance metadata in PDFs

Embed trust scores, source provenance, and compliance data
into PDF metadata so every AI-generated PDF carries its origin story.

Usage:
    pip install akf pypdf
    python pypdf_provenance.py

Learn more: https://akf.dev
"""

from pypdf import PdfReader, PdfWriter
from akf import stamp, universal as akf_u
import json
import tempfile
import os


def create_sample_pdf():
    """Create a minimal PDF for demonstration."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Title": "Q3 Revenue Report", "/Author": "AI Agent"})
    path = tempfile.mktemp(suffix=".pdf")
    with open(path, "wb") as f:
        writer.write(f)
    return path


def stamp_pdf_with_akf(pdf_path, agent="claude", evidence="generated from quarterly data"):
    """Stamp a PDF with AKF trust metadata in the PDF metadata stream."""

    # Create AKF trust metadata
    unit = stamp(
        content=f"AI-generated PDF: {os.path.basename(pdf_path)}",
        confidence=0.85,
        agent=agent,
        evidence=[evidence],
    )
    akf_json = json.dumps(unit.to_dict(compact=True))

    # Read existing PDF
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)

    # Add AKF metadata to PDF metadata stream
    existing_meta = reader.metadata or {}
    writer.add_metadata({
        **{k: v for k, v in existing_meta.items()},
        "/AKF": akf_json,
        "/AIGenerated": "true",
        "/AIAgent": agent,
        "/AITrustScore": str(unit.claims[0].confidence),
    })

    # Write back
    with open(pdf_path, "wb") as f:
        writer.write(f)

    return unit


def read_akf_from_pdf(pdf_path):
    """Read AKF trust metadata from a PDF."""
    reader = PdfReader(pdf_path)
    meta = reader.metadata

    if meta and "/AKF" in meta:
        akf_data = json.loads(meta["/AKF"])
        return akf_data
    return None


if __name__ == "__main__":
    print("=== AKF + pypdf: AI Provenance in PDFs ===\n")

    # Create a sample PDF
    pdf_path = create_sample_pdf()
    print(f"1. Created PDF: {pdf_path}")

    # Stamp with AKF trust metadata
    unit = stamp_pdf_with_akf(pdf_path, agent="claude-3.5", evidence="SEC 10-Q filing analysis")
    print(f"2. Stamped with AKF trust metadata")
    print(f"   Trust score: {unit.claims[0].confidence}")
    print(f"   Agent: {unit.agent}")

    # Read it back
    akf_data = read_akf_from_pdf(pdf_path)
    print(f"\n3. Read back from PDF:")
    print(f"   {json.dumps(akf_data, indent=2)[:200]}...")

    # Compliance check
    print(f"\n4. Run compliance check:")
    print(f"   $ akf audit {pdf_path} --regulation eu_ai_act")

    # Cleanup
    os.unlink(pdf_path)
    print(f"\n✅ Done — trust metadata survives in the PDF metadata stream")
    print(f"   Learn more: https://akf.dev")
