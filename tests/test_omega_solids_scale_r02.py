import hashlib,tracemalloc
from omega_solids_t.campaign import default_campaign_spec
from omega_solids_t.oak import evaluate_candidate
def test_stream_100k_without_materializing_cartesian_product():
    spec=default_campaign_spec(); tracemalloc.start(); digest=hashlib.sha256(); count=0
    for candidate in spec.iter_candidates(0,100000):
        digest.update(candidate.candidate_id.encode())
        if count%1000==0: digest.update(candidate.fingerprint.encode())
        count+=1
    _current,peak=tracemalloc.get_traced_memory(); tracemalloc.stop(); assert count==100000 and len(digest.hexdigest())==64; assert peak<64*1024*1024
def test_partition_boundaries_no_gap_no_overlap():
    partitions=default_campaign_spec().plan(7777)['partitions']; assert partitions[0]['start']==0 and partitions[-1]['stop']==524288; assert all(a['stop']==b['start'] for a,b in zip(partitions,partitions[1:]))
def test_deterministic_sparse_validation_across_space():
    spec=default_campaign_spec(); indices=[0,1,17,65535,131071,262143,393215,524287]; first=[(i,spec.candidate_at(i).fingerprint,evaluate_candidate(spec.candidate_at(i)).fingerprint) for i in indices]; second=[(i,spec.candidate_at(i).fingerprint,evaluate_candidate(spec.candidate_at(i)).fingerprint) for i in indices]; assert first==second
