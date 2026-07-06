from omega_gov_qc_t import (
    MMinusEvent,
    MMinusRegister,
    ProductCard,
    ProductFactory,
    PublicService,
    ServiceCatalog,
)


def test_public_service_friction_signals():
    service = PublicService(
        service_id="service:demo",
        name="Demo service",
        responsible_entity="organization:demo",
        required_documents=["a", "b", "c", "d"],
        forms=["form1", "form2"],
        channels=["web"],
        human_contact_required=True,
        average_delay_days=45,
    )

    signals = set(service.friction_signals())
    assert "high_document_burden" in signals
    assert "missing_review_path" in signals
    assert "long_average_delay" in signals


def test_service_catalog_report_tracks_signals():
    catalog = ServiceCatalog()
    catalog.add(
        PublicService(
            service_id="service:demo",
            name="Demo service",
            responsible_entity="organization:demo",
            channels=["web"],
            human_contact_required=True,
            appeal_or_review_path="Human review path",
        )
    )

    report = catalog.friction_report()
    assert report["service_count"] == 1
    assert report["services_with_signals"] == {}


def test_product_factory_detects_demo_ready_and_strict_review():
    factory = ProductFactory()
    factory.add(
        ProductCard(
            product_id="product:demo",
            name="Demo Product",
            mission="Create an OAK-safe demo report.",
            target_users=["municipality"],
            input_data=["open_data"],
            outputs=["markdown_report"],
            risk_level="high",
            maturity="P1",
            oak_requirements=["SourceRegistry", "OAKGate"],
        )
    )

    report = factory.portfolio_report()
    assert report["product_count"] == 1
    assert report["demo_ready"] == ["product:demo"]
    assert report["strict_review_required"] == ["product:demo"]


def test_blocked_product_cannot_mature_beyond_p1():
    product = ProductCard(
        product_id="product:blocked",
        name="Blocked Product",
        mission="Blocked demo.",
        target_users=["internal"],
        input_data=["example"],
        outputs=["none"],
        risk_level="blocked",
        maturity="P2",
        oak_requirements=["OAKGate"],
    )

    assert any("blocked products" in error for error in product.validate())


def test_m_minus_register_requires_countermeasure_for_high_severity():
    event = MMinusEvent(
        event_id="mminus:demo",
        module="omega_gov_qc_t",
        error_type="missing_source_metadata",
        description="A report claim had incomplete source metadata.",
        severity=4,
    )

    try:
        MMinusRegister().add(event)
    except ValueError as exc:
        assert "countermeasure" in str(exc)
    else:
        raise AssertionError("High severity M- event should require countermeasure")


def test_m_minus_register_tracks_tests_required():
    register = MMinusRegister()
    register.add(
        MMinusEvent(
            event_id="mminus:test_required",
            module="omega_gov_qc_t",
            error_type="missing_limitations",
            description="Output lacked limitations.",
            severity=3,
            countermeasure="Require limitations in report output.",
            test_to_add="test_report_requires_limitations",
        )
    )

    report = register.report()
    assert report["event_count"] == 1
    assert report["tests_required"] == ["mminus:test_required"]
