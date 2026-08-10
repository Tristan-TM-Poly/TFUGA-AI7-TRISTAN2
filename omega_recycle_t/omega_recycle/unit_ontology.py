from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class UnitDef:
    symbol:str
    dimension:str
    scale_to_canonical:float

_UNITS={
    "kg":UnitDef("kg","mass",1.0),
    "g":UnitDef("g","mass",1e-3),
    "t":UnitDef("t","mass",1000.0),
    "metric_tonne":UnitDef("metric_tonne","mass",1000.0),
    "kWh":UnitDef("kWh","energy",1.0),
    "MJ":UnitDef("MJ","energy",1/3.6),
}
def unit_def(symbol:str)->UnitDef:
    try:return _UNITS[symbol]
    except KeyError as exc: raise KeyError(f"unsupported unit: {symbol}") from exc
def compatible_units(a:str,b:str)->bool: return unit_def(a).dimension==unit_def(b).dimension
def convert_value(value:float, source_unit:str, target_unit:str)->float:
    s=unit_def(source_unit); t=unit_def(target_unit)
    if s.dimension!=t.dimension: raise ValueError(f"incompatible unit dimensions: {s.dimension} vs {t.dimension}")
    return value*s.scale_to_canonical/t.scale_to_canonical
