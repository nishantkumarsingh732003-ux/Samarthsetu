"""One-off: add the scheme fit-score labels to all six catalogues.

Kept in the repo, like `add-phase5-messages.py`, as the record of which strings were
added together and in which languages — useful when a reviewer sits down to check the
four draft locales (OPEN_ITEMS OI-4, OI-33).

    python scripts/add-fit-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

# The heading sits under `results`; the component labels under `results.fit` so the
# component key maps straight to a message key.
FIT = {
    "en": {
        "fitHeading": "Why this ranking?",
        "fit": {
            "purpose_fit": "Funds what you need",
            "amount_fit": "Amount fits the scheme",
            "category_fit": "You meet the rules",
            "cost_of_credit": "Cost of the loan",
            "information": "How much we know",
        },
    },
    "hi": {
        "fitHeading": "यह क्रम क्यों?",
        "fit": {
            "purpose_fit": "आपकी ज़रूरत के लिए है",
            "amount_fit": "राशि योजना में फिट है",
            "category_fit": "आप नियम पूरे करते हैं",
            "cost_of_credit": "ऋण की लागत",
            "information": "हमें कितना पता है",
        },
    },
    "mr": {
        "fitHeading": "हा क्रम का?",
        "fit": {
            "purpose_fit": "तुमच्या गरजेसाठी आहे",
            "amount_fit": "रक्कम योजनेत बसते",
            "category_fit": "तुम्ही नियम पूर्ण करता",
            "cost_of_credit": "कर्जाचा खर्च",
            "information": "आम्हाला किती माहिती आहे",
        },
    },
    "bn": {
        "fitHeading": "এই ক্রম কেন?",
        "fit": {
            "purpose_fit": "আপনার প্রয়োজনের জন্য",
            "amount_fit": "পরিমাণ প্রকল্পে মানায়",
            "category_fit": "আপনি নিয়ম পূরণ করেন",
            "cost_of_credit": "ঋণের খরচ",
            "information": "আমরা কতটা জানি",
        },
    },
    "ta": {
        "fitHeading": "இந்த வரிசை ஏன்?",
        "fit": {
            "purpose_fit": "உங்கள் தேவைக்கு ஏற்றது",
            "amount_fit": "தொகை திட்டத்திற்கு பொருந்தும்",
            "category_fit": "நீங்கள் விதிகளை பூர்த்தி செய்கிறீர்கள்",
            "cost_of_credit": "கடனின் செலவு",
            "information": "எங்களுக்கு எவ்வளவு தெரியும்",
        },
    },
    "te": {
        "fitHeading": "ఈ క్రమం ఎందుకు?",
        "fit": {
            "purpose_fit": "మీ అవసరానికి తగినది",
            "amount_fit": "మొత్తం పథకానికి సరిపోతుంది",
            "category_fit": "మీరు నిబంధనలు పూర్తి చేస్తారు",
            "cost_of_credit": "రుణ ఖర్చు",
            "information": "మాకు ఎంత తెలుసు",
        },
    },
}


def main() -> None:
    for locale, block in FIT.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        results = data.setdefault("results", {})
        results["fitHeading"] = block["fitHeading"]
        results["fit"] = {**results.get("fit", {}), **block["fit"]}
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: fitHeading + {len(block['fit'])} component labels")


if __name__ == "__main__":
    main()
