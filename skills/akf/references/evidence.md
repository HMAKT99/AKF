# Evidence classification

`akf stamp --evidence "<text>"` classifies the text with regex patterns (`python/akf/stamp.py`). The class sets how much `akf check` trusts the stamp.

| Class | Text that matches (examples) | Clears the OK threshold alone |
|-------|------------------------------|------------------|
| `test_pass` | `42/42 tests passed`, `all tests pass`, `pytest ... passed` | yes |
| `ci_pass` | `CI green`, `CI pass`, `build passed`, `pipeline passed` | yes |
| `human_review` | `reviewed by @user`, `approved by ...`, `code review done` | yes |
| `type_check` | `mypy: 0 errors`, `type check clean` | no (weak signal) |
| `lint_clean` | `lint clean`, `ruff 0`, `0 lint errors` | no (weak signal) |
| none | `looks good`, `generated from spec`, `refactored` | no, stamp stays `LOW` |

Partial passes (`40/42 tests passed`) and coverage under 30% score as weak evidence. A `--replay` recipe lifts any evidence to the strong tier.

## Rules

- Write the evidence as what you saw, with numbers where you have them.
- Do not paraphrase toward a stronger class. `"tests should pass"` is not an observation.
- Stamp with no `--evidence` when you verified nothing.
- Add `--replay "<command>"` when someone can re-run the check; it turns a claim into something the next agent can falsify.
