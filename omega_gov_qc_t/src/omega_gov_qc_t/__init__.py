"""TristanGovGraph Quebec prototype."""

from .dataset_health import DatasetHealthEngine, DatasetHealthReport, DatasetRecord
from .evidence import EvidenceGraph, EvidenceItem
from .gov_graph import GovEdge, GovGraph, GovNode
from .json_exporter import ExportBundle, JsonExporter
from .m_minus import MMinusEvent, MMinusRegister
from .oak_gate import GateResult, OAKGate, OAKReport
from .opendata_ingestor import IngestionResult, OpenDataIngestor
from .product_factory import ProductCard, ProductFactory
from .report_factory import GovReport, MarkdownReportFactory
from .risk import RiskRegister, RiskTensor
from .service_model import PublicService, ServiceCatalog
from .source_registry import SourceRecord, SourceRegistry

__all__ = [
    "DatasetHealthEngine",
    "DatasetHealthReport",
    "DatasetRecord",
    "EvidenceGraph",
    "EvidenceItem",
    "ExportBundle",
    "GateResult",
    "GovEdge",
    "GovGraph",
    "GovNode",
    "GovReport",
    "IngestionResult",
    "JsonExporter",
    "MMinusEvent",
    "MMinusRegister",
    "MarkdownReportFactory",
    "OAKGate",
    "OAKReport",
    "OpenDataIngestor",
    "ProductCard",
    "ProductFactory",
    "PublicService",
    "RiskRegister",
    "RiskTensor",
    "ServiceCatalog",
    "SourceRecord",
    "SourceRegistry",
]
