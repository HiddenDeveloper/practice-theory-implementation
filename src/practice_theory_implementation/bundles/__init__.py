"""The bundle catalog plus the engagement bundle.

BUNDLES holds the practice bundles the server can list and switch to.
ENGAGEMENT_BUNDLE is the standing arrangement — separate slot because it is
not a practice and cannot be switched to; it is inherited into every practice
projection by the server at startup.

The catalog is mutable. The seed catalog is built from the imported modules
below; Practice Management can add bundles at runtime via `pm_create_bundle`,
and the overlay (data/substrate.db) is loaded into the catalog at startup so
runtime additions survive restarts.
"""

from __future__ import annotations

from practice_theory_implementation.bundles.activities_management import (
    ACTIVITIES_MANAGEMENT,
)
from practice_theory_implementation.bundles.calendar_stewardship import (
    CALENDAR_STEWARDSHIP,
)
from practice_theory_implementation.bundles.judge import JUDGE
from practice_theory_implementation.bundles.practice_management import (
    PRACTICE_MANAGEMENT,
)
from practice_theory_implementation.bundles.reflection import REFLECTION
from practice_theory_implementation.bundles.smoother import SMOOTHER
from practice_theory_implementation.bundles.user_focused_engagement import (
    USER_FOCUSED_ENGAGEMENT,
)
from practice_theory_implementation.types import Bundle

BUNDLES: dict[str, Bundle] = {
    # somatic
    ACTIVITIES_MANAGEMENT.id: ACTIVITIES_MANAGEMENT,
    CALENDAR_STEWARDSHIP.id: CALENDAR_STEWARDSHIP,
    REFLECTION.id: REFLECTION,
    PRACTICE_MANAGEMENT.id: PRACTICE_MANAGEMENT,
    # autonomic
    JUDGE.id: JUDGE,
    SMOOTHER.id: SMOOTHER,
}

ENGAGEMENT_BUNDLE: Bundle = USER_FOCUSED_ENGAGEMENT
