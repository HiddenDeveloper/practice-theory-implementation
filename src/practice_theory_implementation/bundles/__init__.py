"""The bundle catalog plus the engagement bundle, loaded from the file substrate.

BUNDLES holds the switchable practice bundles the server can list and switch to.
ENGAGEMENT_BUNDLE is the standing arrangement — the bundle flagged
`engagement: true` in its file — inherited into every practice projection. Both
come from `substrate_loader` reading `substrate/`; a missing engagement bundle
is a hard (but clearly-reported) error, since somatic mode requires exactly one.
"""

from __future__ import annotations

from practice_theory_implementation.substrate_loader import loaded
from practice_theory_implementation.types import Bundle

_loaded = loaded()
BUNDLES: dict[str, Bundle] = _loaded.bundles

if _loaded.engagement_bundle is None:
    raise RuntimeError(
        "substrate has no engagement bundle (need exactly one file with "
        f"`engagement: true`); loader errors: {_loaded.errors}"
    )

ENGAGEMENT_BUNDLE: Bundle = _loaded.engagement_bundle
