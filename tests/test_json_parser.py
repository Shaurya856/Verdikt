import pytest

from fact_checker.utils.json_parser import (
    LLMParseError,
    extract_json_array,
    extract_json_object,
    normalize_constraint_label,
    normalize_nli_label,
)


class TestExtractJsonArray:
    def test_plain_json(self):
        assert extract_json_array('["a", "b", "c"]') == ["a", "b", "c"]

    def test_markdown_fence_with_lang(self):
        assert extract_json_array('```json\n["a", "b"]\n```') == ["a", "b"]

    def test_markdown_fence_no_lang(self):
        assert extract_json_array('```\n["a"]\n```') == ["a"]

    def test_preamble_text(self):
        assert extract_json_array('Here are the claims: ["claim1", "claim2"]') == [
            "claim1",
            "claim2",
        ]

    def test_empty_array(self):
        assert extract_json_array("[]") == []

    def test_whitespace_around_json(self):
        assert extract_json_array('  ["x"]  ') == ["x"]

    def test_raises_on_plain_text(self):
        with pytest.raises(LLMParseError):
            extract_json_array("this is not json")

    def test_raises_on_object(self):
        with pytest.raises(LLMParseError):
            extract_json_array('{"key": "value"}')

    def test_nested_objects_inside_array(self):
        result = extract_json_array('[{"a": 1}, {"b": 2}]')
        assert result == [{"a": 1}, {"b": 2}]


class TestExtractJsonObject:
    def test_plain_json(self):
        assert extract_json_object('{"label": "SUPPORTED", "reason": "ok"}') == {
            "label": "SUPPORTED",
            "reason": "ok",
        }

    def test_markdown_fence(self):
        assert extract_json_object('```json\n{"label": "CONTRADICTED"}\n```') == {
            "label": "CONTRADICTED"
        }

    def test_preamble_text(self):
        result = extract_json_object('Result: {"label": "NOT_FOUND", "reason": "none"}')
        assert result == {"label": "NOT_FOUND", "reason": "none"}

    def test_raises_on_plain_text(self):
        with pytest.raises(LLMParseError):
            extract_json_object("not json at all")

    def test_raises_on_array(self):
        with pytest.raises(LLMParseError):
            extract_json_object('["a", "b"]')

    def test_empty_object(self):
        assert extract_json_object("{}") == {}


class TestNormalizeNliLabel:
    def test_canonical_forms(self):
        assert normalize_nli_label("SUPPORTED") == "SUPPORTED"
        assert normalize_nli_label("CONTRADICTED") == "CONTRADICTED"
        assert normalize_nli_label("NOT_FOUND") == "NOT_FOUND"

    def test_supported_aliases(self):
        assert normalize_nli_label("SUPPORT") == "SUPPORTED"
        assert normalize_nli_label("SUPPORTS") == "SUPPORTED"

    def test_contradicted_aliases(self):
        assert normalize_nli_label("CONTRADICT") == "CONTRADICTED"
        assert normalize_nli_label("CONTRADICTS") == "CONTRADICTED"
        assert normalize_nli_label("CONTRADICTION") == "CONTRADICTED"

    def test_not_found_aliases(self):
        assert normalize_nli_label("UNKNOWN") == "NOT_FOUND"
        assert normalize_nli_label("NO_INFORMATION") == "NOT_FOUND"
        assert normalize_nli_label("NOTFOUND") == "NOT_FOUND"
        assert normalize_nli_label("INSUFFICIENT") == "NOT_FOUND"

    def test_case_insensitive(self):
        assert normalize_nli_label("supported") == "SUPPORTED"
        assert normalize_nli_label("Contradicted") == "CONTRADICTED"
        assert normalize_nli_label("not_found") == "NOT_FOUND"

    def test_unknown_label_defaults_to_not_found(self):
        assert normalize_nli_label("GARBAGE") == "NOT_FOUND"
        assert normalize_nli_label("") == "NOT_FOUND"


class TestNormalizeConstraintLabel:
    def test_canonical_forms(self):
        assert normalize_constraint_label("SATISFIED") == "SATISFIED"
        assert normalize_constraint_label("VIOLATED") == "VIOLATED"
        assert normalize_constraint_label("MISSING") == "MISSING"

    def test_satisfied_aliases(self):
        assert normalize_constraint_label("SATISFY") == "SATISFIED"

    def test_violated_aliases(self):
        assert normalize_constraint_label("VIOLATION") == "VIOLATED"
        assert normalize_constraint_label("VIOLATES") == "VIOLATED"

    def test_missing_aliases(self):
        assert normalize_constraint_label("NOT_FOUND") == "MISSING"
        assert normalize_constraint_label("UNKNOWN") == "MISSING"

    def test_case_insensitive(self):
        assert normalize_constraint_label("satisfied") == "SATISFIED"
        assert normalize_constraint_label("Violated") == "VIOLATED"

    def test_unknown_label_defaults_to_missing(self):
        assert normalize_constraint_label("BLAH") == "MISSING"
        assert normalize_constraint_label("") == "MISSING"
