import json

from omega_software_truth import Contract, ExampleCase, OAKValidator, SoftwareState, probe_mutant


def add_positive(a: int, b: int) -> int:
    return a + b


def broken_add(a: int, b: int) -> int:
    return a - b


def test_oak_validator_promotes_passing_function_to_local_demonstration():
    contract = Contract(
        name="positive_integer_addition",
        input_predicates={
            "two_ints": lambda args, kwargs: len(args) == 2 and all(isinstance(x, int) for x in args),
            "non_negative": lambda args, kwargs: all(x >= 0 for x in args),
        },
        output_predicates={"int_output": lambda output: isinstance(output, int), "non_negative_output": lambda output: output >= 0},
    )
    state = SoftwareState(
        name="add_positive",
        target=add_positive,
        contract=contract,
        examples=(
            ExampleCase("zero", args=(0, 0), expected=0),
            ExampleCase("simple", args=(2, 3), expected=5),
        ),
    )

    report = OAKValidator().validate(state)

    assert report.passed is True
    assert report.verdict.startswith("D:")
    assert report.failed_cases == 0


def test_oak_validator_records_residue_for_wrong_expected_output():
    contract = Contract(
        name="integer_addition",
        input_predicates={"two_ints": lambda args, kwargs: len(args) == 2 and all(isinstance(x, int) for x in args)},
        output_predicates={"int_output": lambda output: isinstance(output, int)},
    )
    state = SoftwareState(
        name="add_positive_wrong_expectation",
        target=add_positive,
        contract=contract,
        examples=(ExampleCase("wrong", args=(2, 3), expected=6),),
    )

    report = OAKValidator().validate(state)

    assert report.passed is False
    assert report.failed_cases == 1
    assert "Expected 6, got 5" in report.residues[0]


def test_mutation_probe_kills_broken_addition():
    contract = Contract(
        name="addition_contract",
        input_predicates={"two_ints": lambda args, kwargs: len(args) == 2 and all(isinstance(x, int) for x in args)},
        output_predicates={"int_output": lambda output: isinstance(output, int)},
    )
    state = SoftwareState(
        name="add_positive",
        target=add_positive,
        contract=contract,
        examples=(ExampleCase("simple", args=(2, 3), expected=5),),
    )

    mutation = probe_mutant(state, "minus_instead_of_plus", broken_add)

    assert mutation.killed is True
    assert mutation.report.passed is False


def test_oak_report_json_export_is_machine_readable():
    contract = Contract(
        name="addition_contract",
        input_predicates={"two_ints": lambda args, kwargs: len(args) == 2 and all(isinstance(x, int) for x in args)},
        output_predicates={"int_output": lambda output: isinstance(output, int)},
    )
    state = SoftwareState(
        name="add_positive",
        target=add_positive,
        contract=contract,
        examples=(ExampleCase("simple", args=(2, 3), expected=5),),
    )

    report = OAKValidator().validate(state)
    payload = json.loads(report.to_json())

    assert payload["state_name"] == "add_positive"
    assert payload["passed"] is True
    assert payload["case_results"][0]["name"] == "simple"
    assert payload["case_results"][0]["output_repr"] == "5"
