from omega_hqt_t.hashutil import sha256
from omega_hqt_t.models import Scenario

def test_hash_is_order_stable(): assert sha256({"b":2,"a":1})==sha256({"a":1,"b":2})
def test_scenario_hash_changes_with_seed(): assert Scenario("x",seed=1).evidence_hash!=Scenario("x",seed=2).evidence_hash
