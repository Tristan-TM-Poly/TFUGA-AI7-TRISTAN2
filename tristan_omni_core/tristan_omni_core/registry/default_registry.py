from __future__ import annotations
from pathlib import Path
from typing import List
from tristan_omni_core.core.models import ModuleManifest


def default_registry(scan_root: str = "/mnt/data") -> List[ModuleManifest]:
    root = Path(scan_root)
    specs = [
        ("ait_manager_max", "AIT Manager MAX", "AIT_GeminiChatGPTClaudeTristanManager_MAX_v0_2", "AIT", ["multi_model", "consensus", "oak_panel", "debate"]),
        ("autogovernance", "AIT-TRISTAN-INF AutoGovernance", "AIT_TRISTAN_INF_AutoGovernance_DecisionEngine_v0_1", "governance", ["decision", "risk_gate", "memory", "autonomy"]),
        ("legalops_qc", "LegalOps Companies CAN/QC", "AIT_TRISTAN_LegalOps_Companies_CAN_QC_v0_1", "legalops", ["compliance", "evidence", "risk", "templates"]),
        ("official_publishing", "OfficialPublishingManager", "AIT_OfficialPublishingManager_v0_1", "publishing", ["publication_packet", "metadata", "approval_gate"]),
        ("quebec_services", "Québec Public Services Infrastructure", "AIT_Quebec_PublicServices_InfrastructureManager_v0_1", "public_services", ["routing", "sources", "infrastructure"]),
        ("omni_spectroscopy", "OmniSpectroscopy Analytical Physics", "AIT_OmniSpectroscopyAnalyticalPhysics_v0_1", "science", ["spectroscopy", "calibration", "peaks", "uncertainty"]),
        ("tristan_math", "Tristan Mathematics Algorithms Canon", "TRISTAN_Mathematics_Algorithms_Canon_v0_1", "math", ["LOG", "EXP", "CVCD", "HGFM", "prime_tensor", "FTPCI"]),
        ("omni_physics_max", "OmniPhysics MAX", "AIT_OmniPhysicsSimulator_OmniAnalyticPhysics_MAX_v0_2", "physics", ["simulation", "analytic", "residuals", "conservation", "units"]),
        ("omnimedia_max", "OmniMedia YouTube MAX OAK-Safe", "AIT_OmniMediaScienceStudio_YouTubeManager_MAX_OAKSAFE_v0_2", "media", ["script", "storyboard", "youtube_packet", "policy_gate"]),
        ("omniscience", "Tristan Sciences OmniScience Canon", "TRISTAN_Sciences_OmniScience_Canon_v0_1", "omniscience", ["taxonomy", "router", "science_domains", "oak"]),
        ("omni_fusion", "AIT Tristan Omni Monorepo Fusion", "AIT_TRISTAN_OMNI_MONOREPO_FUSION_v0_1", "fusion", ["monorepo", "manifest", "reports", "tests"]),
        ("total_reanalysis", "Tristan Total Reanalysis OAK", "TRISTAN_TOTAL_REANALYSIS_OAK_v0_1", "analysis", ["roadmap", "negative_memory", "architecture", "oak"]),
    ]
    out = []
    for module_id, name, dirname, family, caps in specs:
        path = root / dirname
        testability = 0.80 if (path / "tests" / "test_smoke.py").exists() else 0.55
        out.append(ModuleManifest(
            id=module_id, name=name, path=str(path), family=family, capabilities=caps,
            oak_status="prototype_or_report_present" if path.exists() else "missing",
            risk=0.35 if family in {"math", "AIT", "analysis", "fusion"} else 0.55,
            utility=0.88, fertility=0.90, verifiability=testability, compression=0.78,
            complexity=0.55, metadata={"exists": path.exists(), "dirname": dirname},
        ))
    return out
