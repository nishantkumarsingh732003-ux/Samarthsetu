"""One-off: strings added by the phone-layout pass.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`coverage.showMore` exists because the partner list is now paged. Unfiltered, that list
is the whole national directory: it used to scroll inside a desktop-only column, which
left the phone rendering a page 64,000 pixels tall — a few thousand DOM nodes on the
Rs 6,000 Android in CLAUDE.md rule 5. Twelve at a time, and a button for the rest.

    python scripts/add-responsive-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

COVERAGE = {
    "en": {"showMore": "Show {count} more"},
    "hi": {"showMore": "{count} और दिखाएँ"},
    "mr": {"showMore": "आणखी {count} दाखवा"},
    "bn": {"showMore": "আরও {count}টি দেখান"},
    "ta": {"showMore": "மேலும் {count} காட்டு"},
    "te": {"showMore": "మరో {count} చూపండి"},
}


def main() -> None:
    for locale, block in COVERAGE.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("coverage", {}).update(block)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} coverage")


if __name__ == "__main__":
    main()
