"""Tests for the TOML format handler."""

import pytest

from akf.formats.toml_format import TOMLHandler


@pytest.fixture
def handler() -> TOMLHandler:
    return TOMLHandler()


@pytest.fixture
def tmp_toml(tmp_path):
    def _make(content: str, name: str = "test.toml") -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _make


class TestTOMLHandlerAttributes:
    def test_format_name(self, handler: TOMLHandler) -> None:
        assert handler.FORMAT_NAME == "TOML"

    def test_extensions(self, handler: TOMLHandler) -> None:
        assert ".toml" in handler.EXTENSIONS

    def test_mode(self, handler: TOMLHandler) -> None:
        assert handler.MODE == "embedded"

    def test_mechanism(self, handler: TOMLHandler) -> None:
        assert handler.MECHANISM == "[_akf] table"


class TestEmbedExtract:
    def test_round_trip(self, handler: TOMLHandler, tmp_toml) -> None:
        filepath = tmp_toml('[package]\nname = "my-project"\nversion = "1.0.0"\n')
        metadata = {"akf": "1.0", "overall_trust": 0.9, "claims": []}

        handler.embed(filepath, metadata)
        extracted = handler.extract(filepath)

        assert extracted is not None
        assert extracted["akf"] == "1.0"
        assert abs(extracted["overall_trust"] - 0.9) < 1e-9

    def test_original_content_preserved(self, handler: TOMLHandler, tmp_toml) -> None:
        content = '[package]\nname = "my-project"\nversion = "0.1.0"\n'
        filepath = tmp_toml(content)
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, encoding="utf-8") as f:
            result = f.read()

        assert 'name = "my-project"' in result
        assert 'version = "0.1.0"' in result

    def test_is_enriched_after_embed(self, handler: TOMLHandler, tmp_toml) -> None:
        filepath = tmp_toml("[tool.ruff]\nline-length = 88\n")
        assert not handler.is_enriched(filepath)
        handler.embed(filepath, {"akf": "1.0", "claims": []})
        assert handler.is_enriched(filepath)

    def test_re_embed_replaces_existing(self, handler: TOMLHandler, tmp_toml) -> None:
        filepath = tmp_toml("[settings]\ndebug = true\n")
        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.5, "claims": []})
        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.9, "claims": []})

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        assert content.count("[_akf]") == 1

    def test_extract_returns_none_if_not_enriched(self, handler: TOMLHandler, tmp_toml) -> None:
        filepath = tmp_toml("[package]\nname = \"plain\"\n")
        assert handler.extract(filepath) is None

    def test_is_enriched_false_on_plain_file(self, handler: TOMLHandler, tmp_toml) -> None:
        filepath = tmp_toml("[tool]\nname = \"x\"\n")
        assert not handler.is_enriched(filepath)

    def test_pyproject_toml_style(self, handler: TOMLHandler, tmp_toml) -> None:
        content = (
            '[build-system]\n'
            'requires = ["setuptools"]\n'
            'build-backend = "setuptools.build_meta"\n'
            '\n'
            '[project]\n'
            'name = "mylib"\n'
            'version = "0.1.0"\n'
        )
        filepath = tmp_toml(content, name="pyproject.toml")
        metadata = {"akf": "1.0", "claims": [], "classification": "public"}

        handler.embed(filepath, metadata)
        extracted = handler.extract(filepath)

        assert extracted is not None
        assert extracted["classification"] == "public"

        with open(filepath, encoding="utf-8") as f:
            result = f.read()
        assert 'name = "mylib"' in result

    def test_string_value_with_special_chars(self, handler: TOMLHandler, tmp_toml) -> None:
        filepath = tmp_toml("[x]\na = 1\n")
        metadata = {"akf": "1.0", "label": 'say "hello"', "claims": []}
        handler.embed(filepath, metadata)
        extracted = handler.extract(filepath)
        assert extracted is not None
        assert extracted["label"] == 'say "hello"'
