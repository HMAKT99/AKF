# Skill: Embed Trust Metadata

Embed AKF trust metadata directly into files — DOCX, PDF, images, HTML, and more.

## When to use

- After generating or modifying documents
- When adding trust metadata to existing files
- Before distributing AI-touched content

## Supported formats

| Format | Embedding method |
|--------|-----------------|
| `.docx` `.xlsx` `.pptx` | OOXML custom XML part |
| `.pdf` | PDF metadata stream |
| `.html` | JSON-LD script tag |
| `.md` | YAML frontmatter |
| `.png` `.jpg` | EXIF/XMP metadata |
| `.json` | Reserved `_akf` key |
| Other | Sidecar `.akf.json` file |

## Python API

```python
import akf

# Embed into any file (format auto-detected)
akf.embed("report.docx",
          claims=[
              {"content": "Revenue $4.2B", "confidence": 0.98, "source": "SEC 10-Q"},
              {"content": "Cloud growth 15%", "confidence": 0.85, "source": "Gartner"},
          ],
          classification="confidential")

# Extract from any file
meta = akf.extract("report.docx")
```

## CLI

```bash
akf embed report.docx --classification confidential \
  --claim "Revenue $4.2B" --trust 0.98
akf extract report.docx
akf convert report.docx --output report.akf
```
