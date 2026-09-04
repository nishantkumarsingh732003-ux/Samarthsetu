"""Two labels the first pass got wrong, in all six catalogues.

Both were caught by looking at a rendered screenshot rather than by any check, which is
the argument for looking at the thing:

- `matches.unverifiedFigures` — a scheme whose published figures could not all be sourced
  was wearing the "what is still missing" chip, which reads as *your* information being
  incomplete. It is the scheme's provenance that is incomplete, not the citizen's answers,
  and telling an applicant they are missing something when they are not is the worse of
  the two errors.

- `matches.fundingShare` — the maximum share of a project a scheme funds was labelled
  "why it ranks here", which belongs to the fit breakdown. 90% is a term, not a ranking.

    python scripts/add_account_messages_fixes.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

ADDITIONS = {
    "en": {
        "unverifiedFigures": "Some figures unverified",
        "fundingShare": "Share funded",
    },
    "hi": {
        "unverifiedFigures": "कुछ आँकड़े असत्यापित",
        "fundingShare": "कितना हिस्सा वित्तपोषित",
    },
    "mr": {
        "unverifiedFigures": "काही आकडे असत्यापित",
        "fundingShare": "किती हिस्सा वित्तपुरवठा",
    },
    "bn": {
        "unverifiedFigures": "কিছু সংখ্যা অযাচাই",
        "fundingShare": "কত অংশে অর্থায়ন",
    },
    "ta": {
        "unverifiedFigures": "சில எண்கள் சரிபார்க்கப்படவில்லை",
        "fundingShare": "எவ்வளவு பங்கு நிதியளிப்பு",
    },
    "te": {
        "unverifiedFigures": "కొన్ని సంఖ్యలు ధృవీకరించలేదు",
        "fundingShare": "ఎంత భాగం నిధులు",
    },
}

if __name__ == "__main__":
    for locale, additions in ADDITIONS.items():
        path = MESSAGES / f"{locale}.json"
        catalogue = json.loads(path.read_text(encoding="utf-8"))
        catalogue.setdefault("matches", {}).update(additions)
        path.write_text(
            json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"label fixes merged into {len(ADDITIONS)} catalogues")
