"""__init__.py para fighters schemas"""

from .input import FighterCreateInput, FighterSearchInput, FighterUpdateInput
from .output import (
    FighterComparisonOutput,
    FighterListOutput,
    FighterOutput,
    FighterStatsOutput,
)

__all__ = [
    "FighterCreateInput",
    "FighterUpdateInput",
    "FighterSearchInput",
    "FighterOutput",
    "FighterListOutput",
    "FighterComparisonOutput",
    "FighterStatsOutput",
]
