"""
AKF + Pillow — AI provenance metadata in images

Stamp AI-generated images with trust metadata via EXIF.
Every image carries its origin story.

Usage:
    pip install akf Pillow
    python pillow_provenance.py

Learn more: https://akf.dev
"""

from PIL import Image
from PIL.ExifTags import Base as ExifBase
from akf import stamp, universal as akf_u
import json
import tempfile
import os


def stamp_image_with_akf(image_path, agent="dall-e-3", evidence="generated from prompt"):
    """Stamp an image with AKF trust metadata via EXIF UserComment."""

    # Create AKF trust metadata
    unit = stamp(
        content=f"AI-generated image: {os.path.basename(image_path)}",
        confidence=0.70,
        agent=agent,
        evidence=[evidence],
        ai_generated=True,
    )

    # Use AKF's built-in image embedding (handles EXIF/XMP)
    akf_u.embed(image_path, metadata=unit.to_dict(compact=True))

    return unit


def read_akf_from_image(image_path):
    """Read AKF trust metadata from an image."""
    return akf_u.extract(image_path)


if __name__ == "__main__":
    print("=== AKF + Pillow: AI Provenance in Images ===\n")

    # Create a sample image
    img = Image.new("RGB", (256, 256), color=(60, 120, 200))
    img_path = tempfile.mktemp(suffix=".png")
    img.save(img_path)
    print(f"1. Created image: {img_path}")

    # Stamp with AKF
    unit = stamp_image_with_akf(img_path, agent="dall-e-3", evidence="prompt: blue gradient")
    print(f"2. Stamped with AKF trust metadata")
    print(f"   Trust: {unit.claims[0].confidence}")
    print(f"   AI generated: {unit.claims[0].ai_generated}")

    # Read it back
    akf_data = read_akf_from_image(img_path)
    if akf_data:
        print(f"\n3. Read back from image:")
        print(f"   {json.dumps(akf_data, indent=2)[:200]}...")

    # Cleanup
    os.unlink(img_path)
    print(f"\n✅ Trust metadata embedded in image EXIF/XMP")
    print(f"   Works with PNG, JPEG, TIFF, WebP")
    print(f"   Learn more: https://akf.dev")
