"""KNN-based missing-data imputation."""

from .KNNImputer import (
    ImputationSummary,
    KNNDataImputer,
)

__version__ = "1.0.0"

__all__ = [
    "KNNDataImputer",
    "ImputationSummary",
]