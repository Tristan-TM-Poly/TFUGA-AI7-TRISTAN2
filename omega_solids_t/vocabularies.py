from __future__ import annotations
from .worlds_0 import WORLDS_0
from .worlds_1 import WORLDS_1
from .worlds_2 import WORLDS_2
from .worlds_3 import WORLDS_3
from .vocabulary_axes import TOPOLOGIES, ORDER_CLASSES, ARCHITECTURES, DEFECT_PROFILES, PROCESS_PROFILES, ENVIRONMENT_PROFILES, MECHANISM_CATEGORIES, MECHANISM_VARIANTS, MECHANISMS
WORLDS = WORLDS_0 + WORLDS_1 + WORLDS_2 + WORLDS_3

def validate_vocabularies() -> dict[str,int]:
    groups={'worlds':WORLDS,'architectures':ARCHITECTURES,'defect_profiles':DEFECT_PROFILES,'process_profiles':PROCESS_PROFILES,'environment_profiles':ENVIRONMENT_PROFILES,'mechanisms':MECHANISMS}
    for label,records in groups.items():
        ids=[record['id'] for record in records]
        if len(ids)!=len(set(ids)): raise ValueError(f'duplicate identifiers in {label}')
    if len(WORLDS)!=64 or len(ARCHITECTURES)!=64: raise ValueError('R0.2 requires exactly 64 worlds and 64 base architectures')
    return {name:len(values) for name,values in groups.items()}

def world_by_id(world_id:str)->dict:
    return next(dict(x) for x in WORLDS if x['id']==world_id)

def mechanism_subset(world_index:int, architecture_index:int, width:int=4)->tuple[str,...]:
    if width<=0: return ()
    start=(world_index*11+architecture_index*7)%len(MECHANISMS)
    return tuple(MECHANISMS[(start+i*13)%len(MECHANISMS)]['id'] for i in range(width))
