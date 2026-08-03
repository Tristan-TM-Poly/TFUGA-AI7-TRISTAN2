from omega_hqt_t.security import safety_gate

def test_public_synthetic_content_allowed(): assert safety_gate(requested_level="public",content="synthetic regional aggregate",public_data_only=True).allowed
def test_operational_detail_refused(): assert not safety_gate(requested_level="public",content="live switching command and relay setting",public_data_only=True).allowed
