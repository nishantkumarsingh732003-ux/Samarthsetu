"""Engine and rule-pack versioning.

ENGINE_VERSION is stamped onto every `match_runs` row and every application, so any
past decision can be replayed against the exact rules that produced it.

Bump it whenever a scheme YAML changes. `tests/test_versioning.py` pins the content
hash of the rule files and fails until both the version and the pinned digest are
updated together — you cannot quietly change eligibility policy.
"""

ENGINE_VERSION = "2.2.0"

# sha256 of the schemes/ directory, truncated. Update alongside ENGINE_VERSION.
PINNED_RULES_DIGEST = "545b833da4e8f55d"
