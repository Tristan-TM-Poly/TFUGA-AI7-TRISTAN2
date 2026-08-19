#!/usr/bin/env python3
"""Generate a citizen friction map for ServiceGraph-QC examples."""

from __future__ import annotations

import sys
from pathlib import Path
from oak_service_meter import parse_simple_yaml


ACTION_RULES = {
    "authentification": "offrir accompagnement, récupération simple et alternative comptoir/téléphone",
    "statut": "ajouter un suivi où-est-ma-demande avec étape, blocage, délai et recours",
    "paiement": "prévoir paiement web, téléphone, comptoir et option non-carte si nécessaire",
    "rendez-vous": "exposer disponibilités, listes d'attente, rappels et escalade humaine",
    "données incohérentes": "créer une procédure de correction rapide et journalisée",
    "documents": "réduire les pièces demandées, préremplir et éviter les preuves redondantes",
    "délai": "publier délais réels et seuils d'escalade",
    "langage": "réécrire en français clair avec exemples et checklist",
    "numérique": "maintenir canaux alternatifs et assistance numérique",
    "accessibilité": "tester WCAG, lecteur d'écran, faible littératie et contraintes mobiles",
}


def recommend_action(point: str) -> str:
    p = point.lower()
    for key, action in ACTION_RULES.items():
        if key in p:
            return action
    return "cartographier la cause racine, tester avec citoyens et employés, puis ajouter une règle M⁻"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python servicegraph_qc/friction_map.py <service.yaml>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    data = parse_simple_yaml(path)
    service = data.get("service_name", "unknown")
    print(f"# FrictionMap — {service}")
    print()
    print(f"Besoin public: {data.get('public_need', 'non spécifié')}")
    print()

    segments = data.get("citizen_segments", [])
    if segments:
        print("## Segments citoyens à tester")
        for segment in segments:
            print(f"- {segment}")
        print()

    channels = data.get("channels", [])
    if channels:
        print("## Canaux disponibles")
        for channel in channels:
            print(f"- {channel}")
        print()

    frictions = data.get("friction_points", [])
    print("## Points de friction et actions")
    if not frictions:
        print("- aucune friction documentée; risque de cécité opérationnelle")
    for idx, point in enumerate(frictions, start=1):
        print(f"{idx}. {point}")
        print(f"   action: {recommend_action(str(point))}")

    print()
    print("## Contrôle OAK")
    print("- vérifier que les actions ne diminuent pas sécurité, équité, confidentialité ou recours humain")
    print("- tester avant généralisation")
    print("- inscrire les échecs en mémoire négative M⁻")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
