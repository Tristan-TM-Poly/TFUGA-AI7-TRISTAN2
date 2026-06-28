# Ω-ROI-OAK — Traduire les gains mathématiques en ROI

Ω-ROI-OAK convertit les métriques scientifiques de Ω-DE-TensorProd∞ en indicateurs de décision financière : ROI, ROAK, NPV, payback, risque attendu et statut go/no-go.

## Principe

```text
résidu réduit + latence réduite + stabilité accrue
→ économies, revenus, pertes évitées, CAPEX différé
→ risque ajusté
→ décision OAK financière
```

Forme canonique :

```text
ROAK = (verified_value - total_cost - expected_risk_loss) / total_cost
```

Contrairement à une promesse de profit, ROAK est un critère de sélection :

| ROAK | Décision |
|---:|---|
| < 0 | no-go / M⁻ |
| 0–1 | recherche seulement |
| 1–4.5 | pilote |
| > 4.5 | candidat déploiement |

## API centrale

```python
from omega_vtp_t import FinancialCase, ValueComponent, CostComponent, RiskComponent

case = FinancialCase(
    name="verified_savings",
    values=(ValueComponent("savings", 1_000_000, 0.8, verified=True),),
    costs=(CostComponent("deployment", 200_000),),
    risks=(RiskComponent("operational_risk", 0.05, 500_000),),
)

report = case.evaluate(years=3)
print(report.roak, report.decision)
```

## Templates de marché

### Datacenter PUE

```python
from omega_vtp_t import datacenter_pue_case

case = datacenter_pue_case(
    total_power_mw=20,
    current_pue=1.25,
    target_pue=1.08,
    electricity_cost_per_kwh=0.07,
    deployment_cost=250_000,
    verification_probability=0.8,
)
```

### Batteries / BESS

```python
from omega_vtp_t import battery_revaluation_case

case = battery_revaluation_case(
    acquisition_cost=1_500_000,
    recondition_cost=350_000,
    estimated_revalued_asset=4_200_000,
    validation_probability=0.55,
    safety_risk_loss=3_000_000,
)
```

### Finance / HFT risk engine

```python
from omega_vtp_t import hft_risk_engine_case

case = hft_risk_engine_case(
    daily_volume=50_000_000,
    edge_bps=2.0,
    trading_days=250,
    fill_probability=0.15,
    infrastructure_cost=1_000_000,
    tail_loss=5_000_000,
    compliance_cost=250_000,
)
```

## Règle OAK financière

Aucun scénario n'est traité comme garanti. Chaque cas doit déclarer :

```text
value components
cost components
risk components
verification probability
verified vs unverified value
risk-adjusted decision
```

## Décisions possibles

```text
deploy
pilot
research_only
no_go_m_minus
```

## Phrase canonique

```text
Le framework transforme un résidu mathématique en ligne comptable seulement si la valeur est vérifiée, les coûts sont inclus et le risque est soustrait.
```

## Démo

```bash
python examples/roi_oak_demo.py
python -m unittest discover -s tests
```
