# Skill: Stream Trust Metadata

Stream trust metadata alongside AI output in real-time using AKF's `.akfl` format.

## When to use

- When streaming LLM responses and need trust metadata attached
- For real-time trust scoring during generation
- When building streaming AI pipelines

## Python API

```python
import akf

# Stream with context manager — metadata auto-attaches on close
with akf.stream("output.md", model="gpt-4o") as s:
    for chunk in llm_response:
        s.write(chunk)

# Or use AKFStream directly
from akf import AKFStream

with AKFStream("analysis.md", model="claude-sonnet-4-20250514") as stream:
    stream.write("## Market Analysis\n")
    stream.write("Revenue grew 12% YoY...")
# .akfl file created alongside with trust metadata
```

## Format

AKF streaming uses JSON Lines (`.akfl`):

```jsonl
{"type":"start","model":"gpt-4o","ts":"2025-07-15T09:30:00Z"}
{"type":"chunk","content":"Revenue grew...","idx":0}
{"type":"chunk","content":"12% YoY","idx":1}
{"type":"end","claims":[{"c":"Revenue grew 12%","t":0.85}],"ts":"2025-07-15T09:30:05Z"}
```

## Key features

- Zero-overhead streaming — metadata attaches at stream close
- Automatic `.akfl` sidecar creation
- Compatible with any LLM streaming API
- 0.1s latency for trust metadata attachment
