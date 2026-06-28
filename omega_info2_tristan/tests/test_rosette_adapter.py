from omega_info2 import OAKStatus, RosetteClaim, RosetteExtraction, SourceSpan, rosette_to_info_object


def test_rosette_adapter_preserves_span_provenance_and_uncertainty():
    extraction = RosetteExtraction(
        document_id="doc001",
        source="papers/doc001.pdf",
        title="Example PDF",
        authors=["A. Researcher"],
        language="en",
        claims=[
            RosetteClaim(
                text="The proposed method should be benchmarked before canonization.",
                domain="rosette_pdf",
                span=SourceSpan(page=3, bbox=(0.1, 0.2, 0.8, 0.9), method="pdf_text_layer", confidence=0.82),
            )
        ],
        concepts=["benchmark", "canonization"],
        tables=[{"id": "table:1"}],
        figures=[{"id": "figure:1"}],
    )
    obj = rosette_to_info_object(extraction)
    assert obj.id == "info2_rosette_doc001"
    assert obj.claims[0].oak_status == OAKStatus.PARSED
    assert obj.claims[0].source_id == "doc001:p3"
    assert obj.provenance.transformations[-1].tool == "pdf_text_layer"
    assert obj.oak.residue
