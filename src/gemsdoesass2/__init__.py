"""Auditable, fail-closed utilities for GEMS GeoTIFF research experiments.

Nothing in this package submits files to DrivenData or represents a local result as
an organizer-confirmed leaderboard score.
"""

from .metric import ALPHA, BETA, KERNEL_RADIUS_M, dti_components

__all__ = ["ALPHA", "BETA", "KERNEL_RADIUS_M", "dti_components"]
