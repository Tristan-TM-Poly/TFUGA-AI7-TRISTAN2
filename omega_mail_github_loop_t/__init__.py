"""Ω-MAIL-GITHUB-LOOP-T public API."""
from .command_parser import CommandParseError, parse_command
from .convergence import ConvergenceResult, evaluate_convergence, progress_score
from .engine import DryRunResult, dry_run_email
from .models import AuthorityLevel, GitAction, IterationMetrics, LoopCase, LoopDecision, LoopPolicy, LoopState, MailCommand
from .workflow import PlannedGitHubObjects, create_case, plan

__all__ = [
    "AuthorityLevel", "CommandParseError", "ConvergenceResult", "DryRunResult", "GitAction",
    "IterationMetrics", "LoopCase", "LoopDecision", "LoopPolicy", "LoopState", "MailCommand",
    "PlannedGitHubObjects", "create_case", "dry_run_email", "evaluate_convergence", "parse_command",
    "plan", "progress_score",
]

__version__ = "0.1.0"
