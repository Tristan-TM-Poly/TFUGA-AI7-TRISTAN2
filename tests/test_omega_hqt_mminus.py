from omega_hqt_t.mminus import NegativeMemoryRegistry

def test_negative_memory_registry():
    r=NegativeMemoryRegistry(); item=r.record(context='storm storage simulation',expected='large gain',observed='small gain',causes=('model mismatch',),anti_rules=('benchmark against baseline',))
    assert item.memory_id in r.records; assert r.applicable('storage model')[0].memory_id==item.memory_id
