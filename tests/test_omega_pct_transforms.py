import pytest
from omega_pct_t.transforms import haar_decompose, haar_reconstruct, residual_multiscale_score

@pytest.mark.parametrize("data", [[1,2,3,4], [1,2,3,4,5], [0.0]*16, [(-1)**i*i for i in range(17)]])
def test_haar_roundtrip(data):
    levels = haar_decompose(data)
    rebuilt = haar_reconstruct(levels, len(data))
    assert rebuilt == pytest.approx(data)


def test_residual_score_zero_for_equal_inputs():
    report = residual_multiscale_score([1,2,3,4], [1,2,3,4])
    assert report["l2"] == 0
    assert report["max_abs"] == 0
