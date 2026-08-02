"""Guard against schema drift: what the models emit must validate against the
canonical JSON schema (spec/akf-v1.1.schema.json).

This is the anti-drift mechanism — if a future field is added to the models
without being added to the schema, this test fails, so the published
"standard" can never silently fall behind the implementation again.
"""

import json
import os

import pytest

jsonschema = pytest.importorskip("jsonschema")

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "spec", "akf-v1.1.schema.json"
)


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def test_schema_is_valid(schema):
    jsonschema.Draft202012Validator.check_schema(schema)


def test_maximal_stamp_validates(schema, tmp_path):
    """A stamp exercising every v1.6 field must validate against the schema."""
    from akf.stamp import stamp_file
    from akf import universal

    dep = tmp_path / "helper.py"
    dep.write_text("VALUE = 1\n")
    src = tmp_path / "data.csv"
    src.write_text("q1,42\n")
    f = tmp_path / "main.py"
    f.write_text("import helper\n")

    stamp_file(
        str(f),
        agent="claude-code",
        source="data.csv",                       # -> src_hash
        evidence=["42/42 tests passed, coverage: 85%"],  # -> metrics
        replay="pytest -q",                      # -> replay + input_hash
    )
    meta = universal.extract(str(f))             # -> meta.deps
    # sanity: the fields we're guarding are actually present
    claim = meta["claims"][0]
    assert claim.get("src_hash")
    assert any(e.get("replay") for e in claim.get("evidence", []))
    assert any(e.get("metrics") for e in claim.get("evidence", []))
    assert meta.get("meta", {}).get("deps")

    jsonschema.validate(meta, schema)


def test_bare_stamp_validates(schema, tmp_path):
    from akf.stamp import stamp_file
    from akf import universal

    f = tmp_path / "doc.md"
    f.write_text("# Doc\n")
    stamp_file(str(f), agent="claude-code")
    jsonschema.validate(universal.extract(str(f)), schema)
