from __future__ import annotations

from dataclasses import asdict, dataclass, field

FIGURE_STATUSES = [
    "FIGURE_EXTRACTED",
    "AXES_DETECTED",
    "CURVES_DIGITIZED",
    "CAPTION_LINKED",
    "EQUATION_LINKED",
    "REPRODUCED_SYNTHETICALLY",
    "REPRODUCED_WITH_DATA",
    "MISSING_DATA",
    "FAILED_REPRODUCTION",
]


@dataclass
class FigureReproductionPlan:
    figure_id: str
    caption: str = ""
    axes: dict[str, str] = field(default_factory=dict)
    linked_claims: list[str] = field(default_factory=list)
    linked_equations: list[str] = field(default_factory=list)
    reproduction_status: str = "MISSING_DATA"
    oak_warning: str = "original data unavailable"

    def to_dict(self) -> dict:
        return asdict(self)


def plan_figure_reproduction(caption: str, figure_id: str = "F1") -> FigureReproductionPlan:
    low = caption.lower()
    axes = {}
    if "noise" in low:
        axes["x"] = "noise level"
    if "error" in low:
        axes["y"] = "error"
    status = "CAPTION_LINKED" if caption else "MISSING_DATA"
    warning = "requires axes/data extraction" if caption else "original figure/caption unavailable"
    return FigureReproductionPlan(
        figure_id=figure_id,
        caption=caption,
        axes=axes,
        reproduction_status=status,
        oak_warning=warning,
    )
