from verdikt.components.aggregator import aggregate_constraint, aggregate_nli


class TestAggregateNli:
    def test_all_supported(self):
        assert aggregate_nli(["SUPPORTED", "SUPPORTED"]) == "SUPPORTED"

    def test_all_not_found(self):
        assert aggregate_nli(["NOT_FOUND", "NOT_FOUND"]) == "NOT_FOUND"

    def test_contradicted_beats_supported(self):
        assert aggregate_nli(["SUPPORTED", "CONTRADICTED"]) == "CONTRADICTED"

    def test_contradicted_beats_everything(self):
        assert aggregate_nli(["SUPPORTED", "CONTRADICTED", "NOT_FOUND"]) == "CONTRADICTED"

    def test_one_supported_among_not_found(self):
        assert aggregate_nli(["NOT_FOUND", "SUPPORTED", "NOT_FOUND"]) == "SUPPORTED"

    def test_empty_defaults_to_not_found(self):
        assert aggregate_nli([]) == "NOT_FOUND"

    def test_single_contradicted(self):
        assert aggregate_nli(["CONTRADICTED"]) == "CONTRADICTED"

    def test_single_not_found(self):
        assert aggregate_nli(["NOT_FOUND"]) == "NOT_FOUND"


class TestAggregateConstraint:
    # REQUIREMENT tests
    def test_requirement_satisfied_if_any_chunk_satisfies(self):
        assert aggregate_constraint(["MISSING", "SATISFIED", "MISSING"], "REQUIREMENT") == "SATISFIED"

    def test_requirement_missing_if_no_chunk_satisfies(self):
        assert aggregate_constraint(["MISSING", "MISSING"], "REQUIREMENT") == "MISSING"

    def test_requirement_empty_is_missing(self):
        assert aggregate_constraint([], "REQUIREMENT") == "MISSING"

    def test_requirement_single_satisfied(self):
        assert aggregate_constraint(["SATISFIED"], "REQUIREMENT") == "SATISFIED"

    # PROHIBITION tests
    def test_prohibition_violated_if_any_chunk_violated(self):
        assert aggregate_constraint(["SATISFIED", "VIOLATED", "MISSING"], "PROHIBITION") == "VIOLATED"

    def test_prohibition_satisfied_if_no_violation(self):
        assert aggregate_constraint(["SATISFIED", "MISSING"], "PROHIBITION") == "SATISFIED"

    def test_prohibition_empty_is_satisfied(self):
        assert aggregate_constraint([], "PROHIBITION") == "SATISFIED"

    def test_prohibition_single_violated(self):
        assert aggregate_constraint(["VIOLATED"], "PROHIBITION") == "VIOLATED"
