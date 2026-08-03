"""Conservative adapters from existing Foundry dictionaries."""
from __future__ import annotations


def signatures_from_creation_dna(records: list[dict]) -> dict[str,dict]:
    output={}
    for record in records:
        name=str(record.get("name") or record.get("id") or "").strip()
        if not name: continue
        capabilities=record.get("capabilities",[]); needs=record.get("needs",[])
        outputs={x for cap in capabilities for x in cap.get("output_types",[])}
        inputs={x for need in needs for x in need.get("input_types",[])}
        evidence=record.get("evidence",[])
        output[name]={"outputs":sorted(outputs),"inputs":sorted(inputs),"domains":record.get("domains",[]),
                      "evidence":sum(float(x.get("strength",0)) for x in evidence)/(len(evidence) or 1),
                      "risk":max((float(x) for x in record.get("risks",{}).values()),default=0.0),
                      "cost":1.0+0.1*len(record.get("interfaces",[])),"provenance":record.get("paths",[])}
    return output
