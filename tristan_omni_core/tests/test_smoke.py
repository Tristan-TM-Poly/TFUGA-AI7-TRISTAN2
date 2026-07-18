from tristan_omni_core.registry.default_registry import default_registry
from tristan_omni_core.parallel.probe_runner import run_parallel_probes
from tristan_omni_core.tensor.tensorizer import tensorize, summarize_tensor
from tristan_omni_core.hgfm.mycelial import build_hgfm


def run():
    mods = default_registry('/mnt/data')
    assert len(mods) >= 10
    probes = run_parallel_probes(mods, max_workers=8)
    assert len(probes) == len(mods)
    tensor = tensorize(mods, probes)
    assert tensor['shape'][0] == len(mods)
    assert tensor['shape'][2] == 7
    summary = summarize_tensor(tensor)
    assert summary['top_capabilities']
    hgfm = build_hgfm(mods, probes)
    assert len(hgfm['nodes']) >= len(mods)
    assert len(hgfm['hyperedges']) >= len(mods)
    print('ALL TESTS PASSED')


if __name__ == '__main__':
    run()
