import unittest

from omega_value_os import (
    ChannelProfile,
    ContentAsset,
    EntitlementEvent,
    EntitlementEventType,
    EntitlementLedger,
    compile_projections,
    route_channels,
)


class PaidAccountEntitlementTests(unittest.TestCase):
    def test_unverified_event_cannot_grant_access(self):
        ledger = EntitlementLedger()
        event = EntitlementEvent(
            event_id="evt_1",
            account_id="acct_1",
            capability="pro_lab",
            event_type=EntitlementEventType.GRANT,
            provider="stripe",
            verified=False,
            evidence_ref="webhook:evt_1",
        )
        with self.assertRaises(PermissionError):
            ledger.apply(event)
        self.assertNotIn("pro_lab", ledger.capabilities_for("acct_1"))

    def test_verified_events_are_idempotent(self):
        ledger = EntitlementLedger()
        event = EntitlementEvent(
            event_id="evt_2",
            account_id="acct_1",
            capability="pro_lab",
            event_type=EntitlementEventType.GRANT,
            provider="stripe",
            verified=True,
            evidence_ref="webhook:evt_2",
        )
        self.assertTrue(ledger.apply(event))
        self.assertFalse(ledger.apply(event))
        self.assertEqual(ledger.capabilities_for("acct_1"), frozenset({"pro_lab"}))
        self.assertEqual(len(ledger.audit_log()), 1)

    def test_verified_revoke_removes_capability(self):
        ledger = EntitlementLedger()
        ledger.apply(
            EntitlementEvent(
                "evt_g", "acct_1", "pro_lab", EntitlementEventType.GRANT,
                "stripe", True, "webhook:evt_g"
            )
        )
        ledger.apply(
            EntitlementEvent(
                "evt_r", "acct_1", "pro_lab", EntitlementEventType.REVOKE,
                "stripe", True, "webhook:evt_r"
            )
        )
        self.assertEqual(ledger.capabilities_for("acct_1"), frozenset())


class MediaCompilerTests(unittest.TestCase):
    def test_derived_media_requires_source_provenance(self):
        asset = ContentAsset(asset_id="a1", title="orphan", source_refs=())
        with self.assertRaises(ValueError):
            compile_projections(asset, ["youtube"], ["video"], ["fr"])

    def test_projection_preserves_source_version_and_requires_review(self):
        asset = ContentAsset(
            asset_id="a1",
            title="source",
            source_refs=("research-note:42",),
            version=3,
        )
        projection = compile_projections(
            asset, ["youtube"], ["short"], ["fr"]
        )[0]
        self.assertEqual(projection.source_asset_id, "a1")
        self.assertEqual(projection.source_version, 3)
        self.assertTrue(projection.requires_review)

    def test_router_can_penalize_platform_dependency(self):
        owned = ChannelProfile("site", 0.7, 0.9, 0.5, 0.9, 0.2, 0.1, 0.1)
        dependent = ChannelProfile("platform", 0.9, 0.9, 0.5, 0.9, 0.2, 0.9, 0.1)
        ranked = route_channels([dependent, owned])
        self.assertEqual(ranked[0].name, "site")


if __name__ == "__main__":
    unittest.main()
