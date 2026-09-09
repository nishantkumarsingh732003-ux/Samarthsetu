"""One-off: the comparison table's new rows, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`projectLimit` and `maxLoan` are two different ceilings and must stay two different
phrases. NSFDC will fund a unit costing up to Rs 1,40,000 but advances at most
Rs 1,25,000 against it — see the header comment in `packages/rules/schemes/micro_finance.yaml`.
A translation that collapses them into one idea overstates what a citizen can borrow,
which is the exact misreading that file was written to prevent.

    python scripts/add-compare-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

COMPARE = {
    "en": {
        "title": "Compare Schemes",
        "sub": "Select up to 3 schemes to compare side-by-side.",
        "pick": "Select schemes",
        "feature": "Feature",
        "bestFit": "Best fit",
        "profileMatch": "Profile match",
        "projectLimit": "Project limit",
        "maxLoan": "Maximum loan",
        "categories": "Eligible categories",
        "open": "View",
    },
    "hi": {
        "title": "योजनाओं की तुलना",
        "sub": "साथ-साथ तुलना के लिए 3 तक योजनाएँ चुनें।",
        "pick": "योजनाएँ चुनें",
        "feature": "विशेषता",
        "bestFit": "सबसे उपयुक्त",
        "profileMatch": "प्रोफ़ाइल मिलान",
        "projectLimit": "परियोजना सीमा",
        "maxLoan": "अधिकतम ऋण",
        "categories": "पात्र श्रेणियाँ",
        "open": "देखें",
    },
    "mr": {
        "title": "योजनांची तुलना",
        "sub": "शेजारी-शेजारी तुलनेसाठी ३ पर्यंत योजना निवडा.",
        "pick": "योजना निवडा",
        "feature": "वैशिष्ट्य",
        "bestFit": "सर्वात योग्य",
        "profileMatch": "प्रोफाइल जुळणी",
        "projectLimit": "प्रकल्प मर्यादा",
        "maxLoan": "कमाल कर्ज",
        "categories": "पात्र प्रवर्ग",
        "open": "पाहा",
    },
    "bn": {
        "title": "প্রকল্পের তুলনা",
        "sub": "পাশাপাশি তুলনার জন্য ৩টি পর্যন্ত প্রকল্প বেছে নিন।",
        "pick": "প্রকল্প বেছে নিন",
        "feature": "বৈশিষ্ট্য",
        "bestFit": "সবচেয়ে উপযুক্ত",
        "profileMatch": "প্রোফাইলের মিল",
        "projectLimit": "প্রকল্পের সীমা",
        "maxLoan": "সর্বোচ্চ ঋণ",
        "categories": "যোগ্য শ্রেণি",
        "open": "দেখুন",
    },
    "ta": {
        "title": "திட்டங்களை ஒப்பிடுக",
        "sub": "அருகருகே ஒப்பிட 3 திட்டங்கள் வரை தேர்ந்தெடுங்கள்.",
        "pick": "திட்டங்களைத் தேர்ந்தெடுக்க",
        "feature": "அம்சம்",
        "bestFit": "மிகப் பொருத்தமானது",
        "profileMatch": "சுயவிவரப் பொருத்தம்",
        "projectLimit": "திட்ட வரம்பு",
        "maxLoan": "அதிகபட்சக் கடன்",
        "categories": "தகுதியான பிரிவுகள்",
        "open": "பார்க்க",
    },
    "te": {
        "title": "పథకాల పోలిక",
        "sub": "పక్కపక్కన పోల్చడానికి 3 వరకు పథకాలను ఎంచుకోండి.",
        "pick": "పథకాలను ఎంచుకోండి",
        "feature": "లక్షణం",
        "bestFit": "అత్యంత సరిపోయేది",
        "profileMatch": "ప్రొఫైల్ సరిపోలిక",
        "projectLimit": "ప్రాజెక్ట్ పరిమితి",
        "maxLoan": "గరిష్ఠ రుణం",
        "categories": "అర్హతగల వర్గాలు",
        "open": "చూడండి",
    },
}

# Two rows were labelled with a word the rest of the app does not use for them. The stat
# tiles on the scheme page say "Tenure" and "Interest rate"; the comparison said
# "Repayment" and "Interest". Same figure, two names, and a citizen comparing the two
# screens has to work out that they are the same thing.
ALIGNED = {
    "en": {"tenure": "Tenure", "interest": "Interest rate"},
    "hi": {"tenure": "अवधि", "interest": "ब्याज दर"},
    "mr": {"tenure": "मुदत", "interest": "व्याजदर"},
    "bn": {"tenure": "মেয়াদ", "interest": "সুদের হার"},
    "ta": {"tenure": "காலம்", "interest": "வட்டி விகிதம்"},
    "te": {"tenure": "కాలం", "interest": "వడ్డీ రేటు"},
}

# `maxProject` was the old name for what is now `projectLimit`, and `rules` counted rules
# in a row the redesign dropped. Out of all six at once, or parity breaks.
REMOVED = ["maxProject", "rules"]


def main() -> None:
    for locale, block in COMPARE.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        compare = data.setdefault("compare", {})
        compare.update({**block, **ALIGNED[locale]})
        dropped = [key for key in REMOVED if compare.pop(key, None) is not None]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} compare, -{len(dropped)}")


if __name__ == "__main__":
    main()
