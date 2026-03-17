# Skill: Convert Between Formats

Convert trust metadata between AKF formats, or extract from any file to standalone `.akf`.

## When to use

- Converting embedded metadata to standalone `.akf` files
- Migrating between compact and descriptive formats
- Batch processing directories of mixed-format files

## Python API

```python
import akf

# Extract metadata from any file
meta = akf.extract("report.docx")

# Convert directory (batch)
akf.convert_directory("./docs/", mode="extract")  # Extract .akf from all files
akf.convert_directory("./docs/", mode="enrich")    # Embed .akf back into files
akf.convert_directory("./docs/", mode="both")      # Both directions

# Format conversions
md = akf.to_markdown("report.akf")
html = akf.to_html("report.akf")
summary = akf.executive_summary("report.akf")
```

## CLI

```bash
# Convert to standalone .akf
akf convert report.docx --output report.akf

# Create sidecar for unsupported formats
akf sidecar video.mp4 --classification internal

# View supported formats
akf formats
```

## Supported conversions

| From | To | Method |
|------|-----|--------|
| `.docx` `.pdf` `.html` `.md` `.png` `.jpg` | `.akf` | Extract embedded metadata |
| `.akf` | `.docx` `.pdf` `.html` `.md` | Embed into target format |
| Any file | `.akf.json` | Create sidecar companion |
| `.akf` | Markdown / HTML | Report generation |
