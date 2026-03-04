# Producing AKF — Quick Start for Any Language

AKF is just JSON. Here's how to produce valid AKF in any language.

## Python

```python
import akf
unit = akf.create("Revenue $4.2B", confidence=0.98, source="SEC")
unit.save("output.akf")
```

## TypeScript / JavaScript

```typescript
import { create } from 'akf';
const unit = create("Revenue $4.2B", { confidence: 0.98, source: "SEC" });
fs.writeFileSync("output.akf", JSON.stringify(unit));
```

## Go

```go
akf := map[string]interface{}{
    "v": "1.0",
    "claims": []map[string]interface{}{
        {"c": "Revenue $4.2B", "t": 0.98, "src": "SEC"},
    },
}
json.NewEncoder(f).Encode(akf)
```

## Rust

```rust
let akf = serde_json::json!({
    "v": "1.0",
    "claims": [{"c": "Revenue $4.2B", "t": 0.98, "src": "SEC"}]
});
std::fs::write("output.akf", akf.to_string())?;
```

## Java

```java
var akf = new JSONObject()
    .put("v", "1.0")
    .put("claims", new JSONArray()
        .put(new JSONObject().put("c", "Revenue $4.2B").put("t", 0.98).put("src", "SEC")));
Files.writeString(Path.of("output.akf"), akf.toString());
```

## C# / .NET

```csharp
var akf = new { v = "1.0", claims = new[] {
    new { c = "Revenue $4.2B", t = 0.98, src = "SEC" }
}};
File.WriteAllText("output.akf", JsonSerializer.Serialize(akf));
```

## Ruby

```ruby
require 'json'
akf = { v: "1.0", claims: [{ c: "Revenue $4.2B", t: 0.98, src: "SEC" }] }
File.write("output.akf", JSON.generate(akf))
```

## Shell / curl

```bash
echo '{"v":"1.0","claims":[{"c":"Revenue $4.2B","t":0.98,"src":"SEC"}]}' > output.akf
```

## Minimum Valid AKF

```json
{"v":"1.0","claims":[{"c":"Your claim here","t":0.5}]}
```

That's it. Two required fields per claim (`c` for content, `t` for trust 0-1), one required field on the envelope (`v` for version). Everything else is optional.
