"""One-off: the application status header and progress rail, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`stageDone` / `stageNow` / `stagePending` sit under the dots on the rail and are the only
thing distinguishing a stage the office has completed from one nobody has started. They
must stay three clearly different words: a citizen reading "in progress" where the truth
is "not started" will wait instead of chasing.

    python scripts/add-status-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

TRACK = {
    "en": {
        "statusTitle": "Application status",
        "timelineTitle": "Progress timeline",
        "scheme": "Scheme",
        "partner": "Partner",
        "created": "Submitted",
        "stageDone": "Completed",
        "stageNow": "In progress",
        "stagePending": "Not started",
    },
    "hi": {
        "statusTitle": "आवेदन की स्थिति",
        "timelineTitle": "प्रगति की समयरेखा",
        "scheme": "योजना",
        "partner": "भागीदार",
        "created": "जमा किया",
        "stageDone": "पूरा",
        "stageNow": "चल रहा है",
        "stagePending": "शुरू नहीं हुआ",
    },
    "mr": {
        "statusTitle": "अर्जाची स्थिती",
        "timelineTitle": "प्रगतीची कालरेषा",
        "scheme": "योजना",
        "partner": "भागीदार",
        "created": "सादर केले",
        "stageDone": "पूर्ण",
        "stageNow": "सुरू आहे",
        "stagePending": "सुरू झालेले नाही",
    },
    "bn": {
        "statusTitle": "আবেদনের অবস্থা",
        "timelineTitle": "অগ্রগতির সময়রেখা",
        "scheme": "প্রকল্প",
        "partner": "অংশীদার",
        "created": "জমা দেওয়া হয়েছে",
        "stageDone": "সম্পূর্ণ",
        "stageNow": "চলছে",
        "stagePending": "শুরু হয়নি",
    },
    "ta": {
        "statusTitle": "விண்ணப்ப நிலை",
        "timelineTitle": "முன்னேற்ற காலவரிசை",
        "scheme": "திட்டம்",
        "partner": "பங்குதாரர்",
        "created": "சமர்ப்பித்தது",
        "stageDone": "முடிந்தது",
        "stageNow": "நடந்து கொண்டிருக்கிறது",
        "stagePending": "தொடங்கவில்லை",
    },
    "te": {
        "statusTitle": "దరఖాస్తు స్థితి",
        "timelineTitle": "పురోగతి కాలరేఖ",
        "scheme": "పథకం",
        "partner": "భాగస్వామి",
        "created": "సమర్పించారు",
        "stageDone": "పూర్తి",
        "stageNow": "జరుగుతోంది",
        "stagePending": "ప్రారంభం కాలేదు",
    },
}

BACK = {
    "en": "All applications",
    "hi": "सभी आवेदन",
    "mr": "सर्व अर्ज",
    "bn": "সব আবেদন",
    "ta": "அனைத்து விண்ணப்பங்கள்",
    "te": "అన్ని దరఖాస్తులు",
}


def main() -> None:
    for locale, block in TRACK.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        data.setdefault("track", {}).update(block)
        data.setdefault("myApplications", {})["backToAll"] = BACK[locale]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} track, +1 myApplications")


if __name__ == "__main__":
    main()
