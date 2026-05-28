from unittest.mock import patch

from fact_checker.components.guideline_parser import Constraint, parse_guidelines


class TestParseGuidelines:
    def test_parses_requirement_and_prohibition(self):
        response = (
            '[{"type": "REQUIREMENT", "text": "Defines transformers"},'
            ' {"type": "PROHIBITION", "text": "Mentions recurrence"}]'
        )
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("some guidelines text")
        assert len(constraints) == 2
        assert constraints[0].type == "REQUIREMENT"
        assert constraints[0].text == "Defines transformers"
        assert constraints[1].type == "PROHIBITION"
        assert constraints[1].text == "Mentions recurrence"

    def test_assigns_sequential_ids(self):
        response = (
            '[{"type": "REQUIREMENT", "text": "A"},'
            ' {"type": "REQUIREMENT", "text": "B"},'
            ' {"type": "PROHIBITION", "text": "C"}]'
        )
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("guidelines")
        assert [c.id for c in constraints] == [0, 1, 2]

    def test_returns_constraint_dataclass_instances(self):
        response = '[{"type": "REQUIREMENT", "text": "valid"}]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("guidelines")
        assert isinstance(constraints[0], Constraint)

    def test_filters_unknown_types(self):
        response = '[{"type": "INVALID", "text": "bad"}, {"type": "REQUIREMENT", "text": "good"}]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("guidelines")
        assert len(constraints) == 1
        assert constraints[0].text == "good"

    def test_filters_empty_text(self):
        response = '[{"type": "REQUIREMENT", "text": ""}, {"type": "REQUIREMENT", "text": "valid"}]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("guidelines")
        assert len(constraints) == 1
        assert constraints[0].text == "valid"

    def test_filters_whitespace_only_text(self):
        response = '[{"type": "REQUIREMENT", "text": "   "}, {"type": "PROHIBITION", "text": "real"}]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("guidelines")
        assert len(constraints) == 1

    def test_filters_non_dict_items(self):
        response = '["not a dict", {"type": "REQUIREMENT", "text": "valid"}]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("guidelines")
        assert len(constraints) == 1
        assert constraints[0].text == "valid"

    def test_returns_empty_on_parse_error(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="not json"):
            constraints = parse_guidelines("guidelines")
        assert constraints == []

    def test_returns_empty_on_empty_array(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="[]"):
            constraints = parse_guidelines("guidelines")
        assert constraints == []

    def test_type_normalized_to_uppercase(self):
        response = '[{"type": "requirement", "text": "something"}]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            constraints = parse_guidelines("guidelines")
        assert len(constraints) == 1
        assert constraints[0].type == "REQUIREMENT"
