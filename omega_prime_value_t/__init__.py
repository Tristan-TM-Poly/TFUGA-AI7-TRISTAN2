"""Ω-PRIME-VALUE-T∞: OAK-safe public prime discovery and certification."""

from .campaign import PrimeCampaign, SearchPolicy
from .certificate import build_certificate, verify_certificate
from .models import CandidateStatus, PrimeCandidate, PrimeCertificate
from .primality import is_prime, is_probable_prime
from .proth import prove_proth

__all__ = [
    "CandidateStatus",
    "PrimeCampaign",
    "PrimeCandidate",
    "PrimeCertificate",
    "SearchPolicy",
    "build_certificate",
    "is_prime",
    "is_probable_prime",
    "prove_proth",
    "verify_certificate",
]

__version__ = "0.1.0"
