# AKF Integration Examples

Real-world examples of AKF trust metadata working with popular file format libraries.

Every file AI touches should carry provenance. These examples show how.

## Examples

| Library | Format | Example | Stars |
|---------|--------|---------|-------|
| [pypdf](https://github.com/py-pdf/pypdf) | PDF | [pypdf_provenance.py](pypdf_provenance.py) | 10K |
| [python-docx](https://github.com/python-openxml/python-docx) | DOCX | [python_docx_provenance.py](python_docx_provenance.py) | 5.5K |
| [Pillow](https://github.com/python-pillow/Pillow) | Images | [pillow_provenance.py](pillow_provenance.py) | 13K |
| [pandoc](https://github.com/jgm/pandoc) | All formats | [pandoc_provenance.sh](pandoc_provenance.sh) | 43K |
| [ExifTool](https://github.com/exiftool/exiftool) | EXIF/XMP | [exiftool_provenance.sh](exiftool_provenance.sh) | 4.5K |

## Quick Start

```bash
pip install akf

# PDF
python pypdf_provenance.py

# Word
python python_docx_provenance.py

# Images
python pillow_provenance.py

# Format conversion
bash pandoc_provenance.sh
```

## What You Get

Every file stamped with ~15 tokens of JSON:
- **Trust score** (0-1) based on source tier
- **Source provenance** — where the information came from
- **Agent** — which AI model generated it
- **Compliance** — EU AI Act, SOX, HIPAA readiness

The metadata embeds natively — no sidecars. It survives format conversions, email, cloud sync.

## Learn More

- [akf.dev](https://akf.dev)
- [GitHub](https://github.com/HMAKT99/AKF)
- `pip install akf`
