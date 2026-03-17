# Skill: Stream Trust Metadata

Stream trust metadata alongside AI output in real-time using AKF.

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
# Trust metadata embedded on close

# Low-level streaming API
from akf.streaming import stream_start, stream_claim, stream_end

session = stream_start(agent_id="my-agent", output_path="output.akfl")
stream_claim(session, "Revenue grew 12%", confidence=0.85)
stream_claim(session, "Cloud segment up 15%", confidence=0.92)
unit = stream_end(session)
```

## CLI

```bash
# Collect streaming .akfl lines into .akf
akf stream collect output.akfl --output report.akf
```

## Key features

- Zero-overhead streaming — metadata attaches at stream close
- Automatic `.akfl` sidecar creation
- Compatible with any LLM streaming API
- Context manager (`akf.stream()`) for simplest usage
