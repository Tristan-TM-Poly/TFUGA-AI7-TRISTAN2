"""Ω-INTERCOMPANY-MESH-T: bounded intercompany agreement and mail packet generator."""

from .generator import default_nodes, generate_mesh, write_mesh
from .models import AgreementFamily, AgreementPacket, CompanyNode, LegalStatus, MailPacket, PacketStatus

__all__ = [
    "AgreementFamily",
    "AgreementPacket",
    "CompanyNode",
    "LegalStatus",
    "MailPacket",
    "PacketStatus",
    "default_nodes",
    "generate_mesh",
    "write_mesh",
]

__version__ = "0.1.0"
