from osdata.sources.registry import default_sources


def run():
    sources = default_sources()
    assert len(sources) >= 8
    ids = {s.id for s in sources}
    assert 'openalex' in ids
    assert 'huggingface_datasets' in ids
    assert 'worldbank' in ids
    assert all(s.base_url for s in sources)
    assert all(s.license_hint for s in sources)
    print('ALL TESTS PASSED')


if __name__ == '__main__':
    run()
