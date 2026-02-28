# LLM Integration

How to get LLMs to output AKF format.

## System Prompt Template

Add this to your system prompt:

```
When asked to produce structured knowledge, output in AKF format:
{"v":"1.0","claims":[{"c":"<claim>","t":<0-1>,"src":"<source>","tier":<1-5>,"ai":true}]}

Trust scores: 1.0 = certain, 0.8 = high confidence, 0.5 = moderate, 0.3 = speculative
Tiers: 1=primary source, 2=analyst report, 3=news, 4=estimate, 5=inference
Always set ai:true for your claims. Add risk:"<description>" for tier 4-5 claims.
```

## One-Shot Examples

### For GPT / Claude / Gemini

**Prompt:**
```
Summarize the key financial metrics from Acme Corp's Q3 report.
Output as AKF format.
```

**Expected output:**
```json
{
  "v": "1.0",
  "agent": "gpt-4o",
  "claims": [
    {"c": "Acme Q3 revenue was $2.1B, up 8% YoY", "t": 0.95, "src": "Q3 earnings release", "tier": 1, "ai": true},
    {"c": "Operating margin improved to 22% from 19%", "t": 0.92, "src": "Q3 earnings release", "tier": 1, "ai": true},
    {"c": "Cloud segment likely to reach $1B ARR by Q4", "t": 0.65, "src": "Trend extrapolation", "tier": 5, "ai": true, "risk": "AI projection based on 3 quarters of data"}
  ]
}
```

## Output Parser — Python

```python
import json
import akf

def parse_llm_output(raw_text: str) -> akf.AKF:
    """Extract and parse AKF from LLM output."""
    # Find JSON in the response
    start = raw_text.find('{')
    end = raw_text.rfind('}') + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in LLM output")

    json_str = raw_text[start:end]
    unit = akf.loads(json_str)

    # Validate
    result = akf.validate(unit)
    if not result.valid:
        raise ValueError(f"Invalid AKF: {result.errors}")

    return unit
```

## LangChain Integration

```python
from langchain.output_parsers import BaseOutputParser
import akf

class AKFOutputParser(BaseOutputParser):
    def parse(self, text: str) -> akf.AKF:
        start = text.find('{')
        end = text.rfind('}') + 1
        return akf.loads(text[start:end])

    def get_format_instructions(self) -> str:
        return (
            'Output in AKF format: '
            '{"v":"1.0","claims":[{"c":"<claim>","t":<0-1>,"ai":true}]}'
        )
```

## Tips for Better AKF Output

1. **Include a one-shot example** in your prompt — LLMs produce valid AKF 95%+ of the time with one example
2. **Ask for tier assignments** — LLMs are good at self-assessing source quality
3. **Request risk descriptions** for speculative claims
4. **Set agent field** to identify which model generated the content
5. **Validate after parsing** — always run `akf.validate()` on LLM output
