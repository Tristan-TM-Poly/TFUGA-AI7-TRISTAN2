from omega_federated_intent_fabric_t import (
    AuthorityLevel,
    FederatedIntentCompiler,
    IntentClosureCompiler,
    IntentKind,
    RelationHint,
    RelationKind,
    SourceEnvelope,
    SourceKind,
)


def _source(source_id, *, claims=(), intents=(), residuals=(), prohibitions=()):
    return SourceEnvelope.build(
        source_kind=SourceKind.GITHUB,
        source_id=source_id,
        fingerprint=f"sha:{source_id}",
        observed_at="2026-08-20T17:45:00Z",
        authority=AuthorityLevel.READ,
        provenance=(f"fixture:{source_id}",),
        claims=claims,
        explicit_intents=intents,
        residuals=residuals,
        prohibitions=prohibitions,
    )


def _compile_with_relation(first, second, kind):
    compiler = FederatedIntentCompiler()
    initial = compiler.compile([first, second])
    ids = tuple(item.intent_id for item in initial.intents if item.kind == IntentKind.EXPLICIT)
    assert len(ids) == 2
    hint = RelationHint.build(kind=kind, intent_ids=ids, evidence_refs=("fixture:relation",))
    return compiler.compile([first, second], relation_hints=(hint,))


def test_exact_cross_source_duplicate_becomes_eigen_intent_without_deleting_provenance():
    receipt = FederatedIntentCompiler().compile(
        [
            _source("repo-a", intents=("Reuse existing intent compiler",)),
            _source("repo-b", intents=("Reuse existing intent compiler",)),
        ]
    )
    closure = IntentClosureCompiler().compile(receipt)

    assert len(closure.eigen_intents) == 1
    eigen = closure.eigen_intents[0]
    assert eigen.family == IntentKind.EXPLICIT.value
    assert eigen.canonical_text == "Reuse existing intent compiler"
    assert len(eigen.member_intent_ids) == 2
    assert len(eigen.source_envelope_ids) == 2
    assert eigen.compression_gain == 1
    assert eigen.action_authorized is False


def test_similar_but_nonidentical_intents_are_not_declared_eigen_equivalent():
    receipt = FederatedIntentCompiler().compile(
        [
            _source("repo-a", intents=("Reuse existing intent compiler",)),
            _source("repo-b", intents=("Reuse the existing intent compiler",)),
        ]
    )
    closure = IntentClosureCompiler().compile(receipt)

    assert closure.eigen_intents == ()


def test_evidenced_conflict_creates_proposed_closure_intent_only():
    receipt = _compile_with_relation(
        _source("repo-a", intents=("Keep adapter separate",)),
        _source("repo-b", intents=("Merge adapter into core",)),
        RelationKind.CONFLICT,
    )
    closure = IntentClosureCompiler().compile(receipt)

    assert len(closure.derived_intents) == 1
    derived = closure.derived_intents[0]
    assert derived.kind == IntentKind.DERIVED
    assert derived.status == "PROPOSED"
    assert derived.action_authorized is False
    assert derived.text.startswith("Resolve evidenced cross-source conflict:")
    assert any(item.kind == RelationKind.CONFLICT.value for item in closure.obligations)


def test_exact_minimal_unlock_set_can_cover_residual_and_relation_with_one_intent():
    first = _source("repo-a", intents=("Repair closure blocker",), residuals=("closure blocker remains",))
    second = _source("repo-b", intents=("Preserve current behavior",))
    compiler = FederatedIntentCompiler()
    initial = compiler.compile([first, second])
    residual = next(item for item in initial.intents if item.kind == IntentKind.RESIDUAL)
    explicit_second = next(
        item
        for item in initial.intents
        if item.kind == IntentKind.EXPLICIT and "Preserve current behavior" in item.text
    )
    hint = RelationHint.build(
        kind=RelationKind.CONFLICT,
        intent_ids=(residual.intent_id, explicit_second.intent_id),
        evidence_refs=("fixture:conflict",),
    )
    receipt = compiler.compile([first, second], relation_hints=(hint,))
    closure = IntentClosureCompiler().compile(receipt)

    assert closure.unlock_set.selection_method == "exact_enumeration"
    assert closure.unlock_set.exact_minimality_proven is True
    assert closure.unlock_set.uncovered_obligation_ids == ()
    assert closure.unlock_set.selected_intent_ids == (residual.intent_id,)
    assert len(closure.unlock_set.covered_obligation_ids) == 2


def test_negative_intent_is_constraint_not_unlock_candidate():
    receipt = FederatedIntentCompiler().compile(
        [_source("repo-a", prohibitions=("Do not merge without exact-head qualification",))]
    )
    closure = IntentClosureCompiler().compile(receipt)

    negative = next(item for item in receipt.intents if item.kind == IntentKind.NEGATIVE)
    assert negative.intent_id not in closure.unlock_set.selected_intent_ids
    assert closure.action_authorized is False
    assert closure.unlock_set.action_authorized is False


def test_claim_requires_both_verification_and_counter_obligations():
    receipt = FederatedIntentCompiler().compile(
        [_source("repo-a", claims=("candidate improves verified closure",))]
    )
    closure = IntentClosureCompiler().compile(receipt)

    kinds = {item.kind for item in closure.obligations}
    assert IntentKind.VERIFICATION.value in kinds
    assert IntentKind.COUNTER.value in kinds
    assert len(closure.unlock_set.selected_intent_ids) == 2
    assert closure.unlock_set.exact_minimality_proven is True


def test_large_frontier_falls_back_without_claiming_minimum():
    claims = tuple(f"claim {index}" for index in range(10))
    receipt = FederatedIntentCompiler().compile([_source("repo-a", claims=claims)])
    closure = IntentClosureCompiler(max_exact_candidates=5).compile(receipt)

    assert len(closure.obligations) == 20
    assert closure.unlock_set.selection_method == "deterministic_greedy"
    assert closure.unlock_set.exact_minimality_proven is False
    assert closure.unlock_set.uncovered_obligation_ids == ()


def test_closure_receipt_and_next_seed_are_deterministic_and_authority_safe():
    receipt = FederatedIntentCompiler().compile(
        [
            _source("repo-b", claims=("shared claim",)),
            _source("repo-a", claims=("shared claim",)),
        ]
    )
    compiler = IntentClosureCompiler()
    first = compiler.compile(receipt)
    second = compiler.compile(receipt)

    assert first.receipt_sha256 == second.receipt_sha256
    seed = compiler.next_intent_seed(first)
    assert seed["authority"]["execution_authorized"] is False
    assert seed["authority"]["merge_authorized"] is False
    assert seed["authority"]["publish_authorized"] is False
