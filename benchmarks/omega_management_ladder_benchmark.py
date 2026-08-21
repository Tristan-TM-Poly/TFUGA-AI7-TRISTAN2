from omega_management_t.ladder import ARTIFACT_CLASSES, evaluate_ladder


def run():
    levels = []
    for n in range(0, 5):
        covered = ARTIFACT_CLASSES[: min(2 ** n, len(ARTIFACT_CLASSES))]
        result = evaluate_ladder(n, covered)
        levels.append({
            "n": n,
            "target": result.target,
            "covered": len(result.covered),
            "missing_for_n_plus_1": len(result.missing),
            "next_target": result.next_target,
        })
    return levels


if __name__ == "__main__":
    for row in run():
        print(row)
