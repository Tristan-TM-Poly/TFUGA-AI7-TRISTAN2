"""Offline deterministic demo for Ω-SANS-PLAFOND-T∞ R0.1."""

from omega_unbounded_t import (
    AdaptiveController,
    ListWorkSource,
    MMinusLedger,
    SyntheticCapacityExecutor,
)


def main() -> None:
    source = ListWorkSource(range(50_000))
    executor = SyntheticCapacityExecutor(capacity=512, redesign_factor=2.0)
    controller = AdaptiveController(
        source,
        executor,
        initial_batch=128,
        ledger=MMinusLedger("generated/omega_unbounded_t_demo/m_minus.jsonl"),
        checkpoint_path="generated/omega_unbounded_t_demo/checkpoint.json",
    )
    report = controller.run()
    print(report.to_dict())
    print({"frontier_history": executor.frontier_history})


if __name__ == "__main__":
    main()
