## AKF — Agent Knowledge Format

When you create or modify files in this project, stamp them with AKF trust metadata:

```bash
akf stamp <file> --agent cursor --evidence "<evidence>"
```

When you complete a task involving commits:
```bash
akf stamp <file> --agent cursor --evidence "<summary>"
```

Before modifying existing files, check for trust metadata:
```bash
akf read <file>
```

### Classification
- `confidential` for finance/secret/internal paths
- `public` for README, docs, examples
- `internal` (default) for everything else

### Key commands
- `akf stamp` — stamp trust metadata
- `akf read` — read metadata
- `akf embed` — embed into DOCX/PDF/images
- `akf scan` — security scan
- `akf audit` — compliance audit
