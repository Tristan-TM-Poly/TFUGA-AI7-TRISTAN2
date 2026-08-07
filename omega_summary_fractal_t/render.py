from __future__ import annotations

import json
from pathlib import Path
from .models import SummaryBundle, SummaryNode
AUDIENCE_HINTS={"tristan":"Architecture, preuves, dette de cristallisation et prochaines actions.","developer":"Code, fichiers, tests, contrats et points d'intégration.","scientist":"Hypothèses observables, preuves, limites et reproductibilité.","investor":"État de réalisation et preuves techniques; aucune traction n'est inférée.","client":"Capacités observables; aucun bénéfice non démontré n'est inventé.","ip":"Provenance structurelle; le statut brevet/secret/publication exige IPGate.","contributor":"Où se trouve le code, ce qui est testé et les lacunes prioritaires.","oak":"Séparation stricte entre documenté, implémenté, testé et validé."}


def _system_table(nodes:list[SummaryNode])->str:
    systems=[n for n in nodes if n.kind=="system"]
    if not systems:return "_Aucun système visible à cette profondeur ou pour ce focus._"
    lines=["| Système | Statut | Code | Tests | Docs | Schéma | Résumé |","|---|---|---:|---:|---:|---:|---|"]
    for n in systems:
        m=n.metrics; summary=n.one_line.replace("|","\\|"); lines.append(f"| `{n.path}` | {n.status} | {m.get('code_files',0)} | {m.get('tests',0)} | {m.get('documents',0)} | {m.get('schemas',0)} | {summary} |")
    return "\n".join(lines)


def render_markdown(bundle:SummaryBundle)->str:
    h=bundle.health; oak=h.get("oak",{}); lines=[f"# Ω-SUMMARY-FRACTAL — {bundle.root}","",f"- **Profondeur :** D{bundle.depth}",f"- **Audience :** `{bundle.audience}` — {AUDIENCE_HINTS[bundle.audience]}",f"- **Focus :** `{bundle.focus or 'corpus local'}`",f"- **Empreinte :** `{bundle.cache_fingerprint}`",f"- **Généré :** {bundle.generated_at}","","## Résumé structurel","",_system_table(bundle.nodes),"","## Santé du corpus","",f"- systèmes détectés : **{h.get('systems',0)}**",f"- ratio implémenté : **{h.get('implemented_ratio',0):.1%}**",f"- ratio testé : **{h.get('tested_ratio',0):.1%}**",f"- ratio documenté : **{h.get('documented_ratio',0):.1%}**",f"- ratio avec schéma : **{h.get('schema_backed_ratio',0):.1%}**","","## OAK","",f"- **Vérité :** {oak.get('truth','')}",f"- **Produit :** {oak.get('product','')}",f"- **IP :** {oak.get('ip','')}",f"- **Revenu :** {oak.get('revenue','')}",f"- **Risque :** {oak.get('risk','')}",""]
    if bundle.depth>=3:
        lines += ["## Lacunes prioritaires",""]; lines += [f"- P{g['priority']} `{g['system']}` — **{g['kind']}**: {g['action']}" for g in bundle.gaps[:100]] or ["_Aucune lacune structurelle détectée par les règles actuelles._"]; lines.append("")
    if bundle.depth>=4:
        lines += ["## Candidats de déduplication",""]; lines += [f"- `{x['left']}` ↔ `{x['right']}` — similarité {x['similarity']:.2f}; revue humaine requise." for x in bundle.duplicate_candidates[:50]] or ["_Aucun quasi-doublon au-dessus du seuil heuristique._"]; lines.append("")
    if bundle.depth>=5:
        lines += ["## Artefacts observés",""]; by_kind={}
        for n in bundle.nodes:
            if n.kind not in {"repository","system"}: by_kind.setdefault(n.kind,[]).append(n)
        for kind in sorted(by_kind): lines.append(f"### {kind}"); lines += [f"- `{n.path}` — {n.one_line}" for n in by_kind[kind][:200]]; lines.append("")
    lines += ["## Limite épistémique","","Ce document résume des artefacts Git observables. La présence de code, de tests ou de documentation ne constitue pas à elle seule une validation scientifique, commerciale, juridique ou de sécurité.",""]
    return "\n".join(lines)


def write_bundle(bundle:SummaryBundle, output_dir:str|Path)->dict[str,Path]:
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);stem=f"summary_d{bundle.depth}_{bundle.audience}";jp=out/f"{stem}.json";mp=out/f"{stem}.md";jp.write_text(json.dumps(bundle.to_dict(),indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8");mp.write_text(render_markdown(bundle),encoding="utf-8");return {"json":jp,"markdown":mp}


def write_operational_views(bundle:SummaryBundle, output_dir:str|Path)->dict[str,Path]:
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);summary=out/"SUMMARY.md";summary.write_text(render_markdown(bundle),encoding="utf-8");status=out/"STATUS.md";status.write_text("# STATUS\n\n"+_system_table(bundle.nodes)+"\n\nStatus are inferred only from observable repository artifacts.\n",encoding="utf-8");oak=out/"OAK_REPORT.md";oak.write_text("# OAK REPORT\n\n"+f"Fingerprint: `{bundle.cache_fingerprint}`\n\n## Boundary\n\nStructural evidence only. No scientific validity, novelty, patentability, safety, market traction, or causal truth is inferred.\n\n## Dashboard\n\n"+f"```json\n{json.dumps(bundle.health,indent=2,ensure_ascii=False,sort_keys=True)}\n```\n",encoding="utf-8");actions=out/"NEXT_ACTIONS.md";al=["# NEXT ACTIONS",""]+[f"- [ ] P{g['priority']} `{g['system']}` — {g['action']}" for g in bundle.gaps[:100]];al += [] if bundle.gaps else ["- [ ] Run deeper semantic/OAK review; structural checks found no immediate gaps."];actions.write_text("\n".join(al)+"\n",encoding="utf-8");index=out/"SUMMARY_INDEX.json";index.write_text(json.dumps({"schema_version":bundle.schema_version,"fingerprint":bundle.cache_fingerprint,"depth":bundle.depth,"audience":bundle.audience,"focus":bundle.focus,"artifacts":["SUMMARY.md","STATUS.md","OAK_REPORT.md","NEXT_ACTIONS.md"]},indent=2,sort_keys=True)+"\n",encoding="utf-8");return {"summary":summary,"status":status,"oak":oak,"actions":actions,"index":index}
