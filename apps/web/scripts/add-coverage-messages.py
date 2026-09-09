"""One-off: the partner map page's strings, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`type.*` spells out the four partner kinds the enum stores as codes — SCA, PSB, RRB,
NBFC_MFI in `apps/api/app/models/enums.py`. The distinction is not cosmetic: a district
with banks but no State Channelising Agency cannot process the schemes that route only
through an SCA, so a citizen has to be able to tell one row from another without knowing
the acronym. Keep the expansions, and keep them the official names.

    python scripts/add-coverage-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

COVERAGE = {
    "en": {
        "title": "Find the right Channel Partner",
        "sub": "State Channelising Agencies, banks and RRBs authorised for MoSJE schemes.",
        "searchPlaceholder": "City, district or PIN code…",
        "filterState": "State",
        "allStates": "All states",
        "allIndia": "All India",
        "districtDrilldown": "District drilldown",
        "paused": "Not taking applications",
        "showOnMap": "Show {name} on the map",
        "noneHere": "No partners match. Try a different state or scheme.",
        "type": {
            "SCA": "State Channelising Agency",
            "PSB": "Public Sector Bank",
            "RRB": "Regional Rural Bank",
            "NBFC_MFI": "NBFC Microfinance Institution",
        },
    },
    "hi": {
        "title": "सही चैनल पार्टनर खोजें",
        "sub": "MoSJE योजनाओं के लिए अधिकृत राज्य चैनलाइज़िंग एजेंसियाँ, बैंक और आरआरबी।",
        "searchPlaceholder": "शहर, ज़िला या पिन कोड…",
        "filterState": "राज्य",
        "allStates": "सभी राज्य",
        "allIndia": "पूरा भारत",
        "districtDrilldown": "ज़िलेवार देखें",
        "paused": "आवेदन नहीं ले रहे",
        "showOnMap": "{name} को मानचित्र पर दिखाएँ",
        "noneHere": "कोई भागीदार नहीं मिला। दूसरा राज्य या योजना आज़माएँ।",
        "type": {
            "SCA": "राज्य चैनलाइज़िंग एजेंसी",
            "PSB": "सार्वजनिक क्षेत्र का बैंक",
            "RRB": "क्षेत्रीय ग्रामीण बैंक",
            "NBFC_MFI": "एनबीएफसी माइक्रोफाइनेंस संस्था",
        },
    },
    "mr": {
        "title": "योग्य चॅनेल भागीदार शोधा",
        "sub": "MoSJE योजनांसाठी अधिकृत राज्य चॅनेलायझिंग एजन्सी, बँका आणि आरआरबी.",
        "searchPlaceholder": "शहर, जिल्हा किंवा पिन कोड…",
        "filterState": "राज्य",
        "allStates": "सर्व राज्ये",
        "allIndia": "संपूर्ण भारत",
        "districtDrilldown": "जिल्हानिहाय पाहा",
        "paused": "अर्ज घेत नाहीत",
        "showOnMap": "{name} नकाशावर दाखवा",
        "noneHere": "कोणताही भागीदार जुळला नाही. दुसरे राज्य किंवा योजना पाहा.",
        "type": {
            "SCA": "राज्य चॅनेलायझिंग एजन्सी",
            "PSB": "सार्वजनिक क्षेत्रातील बँक",
            "RRB": "प्रादेशिक ग्रामीण बँक",
            "NBFC_MFI": "एनबीएफसी मायक्रोफायनान्स संस्था",
        },
    },
    "bn": {
        "title": "সঠিক চ্যানেল পার্টনার খুঁজুন",
        "sub": "MoSJE প্রকল্পের জন্য অনুমোদিত রাজ্য চ্যানেলাইজিং এজেন্সি, ব্যাঙ্ক ও আরআরবি।",
        "searchPlaceholder": "শহর, জেলা বা পিন কোড…",
        "filterState": "রাজ্য",
        "allStates": "সব রাজ্য",
        "allIndia": "সমগ্র ভারত",
        "districtDrilldown": "জেলাভিত্তিক দেখুন",
        "paused": "আবেদন নেওয়া হচ্ছে না",
        "showOnMap": "{name} মানচিত্রে দেখান",
        "noneHere": "কোনও অংশীদার মেলেনি। অন্য রাজ্য বা প্রকল্প দেখুন।",
        "type": {
            "SCA": "রাজ্য চ্যানেলাইজিং এজেন্সি",
            "PSB": "রাষ্ট্রায়ত্ত ব্যাঙ্ক",
            "RRB": "আঞ্চলিক গ্রামীণ ব্যাঙ্ক",
            "NBFC_MFI": "এনবিএফসি মাইক্রোফাইন্যান্স সংস্থা",
        },
    },
    "ta": {
        "title": "சரியான சேனல் பங்குதாரரைக் கண்டறியுங்கள்",
        "sub": "MoSJE திட்டங்களுக்கு அங்கீகரிக்கப்பட்ட மாநில சேனலைசிங் ஏஜென்சிகள், வங்கிகள் மற்றும் ஆர்ஆர்பிக்கள்.",
        "searchPlaceholder": "நகரம், மாவட்டம் அல்லது பின் கோடு…",
        "filterState": "மாநிலம்",
        "allStates": "அனைத்து மாநிலங்கள்",
        "allIndia": "இந்தியா முழுவதும்",
        "districtDrilldown": "மாவட்ட வாரியாகப் பார்க்க",
        "paused": "விண்ணப்பங்கள் ஏற்கப்படவில்லை",
        "showOnMap": "{name} ஐ வரைபடத்தில் காட்டு",
        "noneHere": "எந்தப் பங்குதாரரும் பொருந்தவில்லை. வேறு மாநிலம் அல்லது திட்டத்தை முயற்சிக்கவும்.",
        "type": {
            "SCA": "மாநில சேனலைசிங் ஏஜென்சி",
            "PSB": "பொதுத்துறை வங்கி",
            "RRB": "பிராந்திய கிராமிய வங்கி",
            "NBFC_MFI": "என்பிஎஃப்சி நுண்நிதி நிறுவனம்",
        },
    },
    "te": {
        "title": "సరైన ఛానెల్ భాగస్వామిని కనుగొనండి",
        "sub": "MoSJE పథకాలకు అధీకృతమైన రాష్ట్ర ఛానెలైజింగ్ ఏజెన్సీలు, బ్యాంకులు మరియు ఆర్ఆర్‌బీలు.",
        "searchPlaceholder": "నగరం, జిల్లా లేదా పిన్ కోడ్…",
        "filterState": "రాష్ట్రం",
        "allStates": "అన్ని రాష్ట్రాలు",
        "allIndia": "భారతదేశం మొత్తం",
        "districtDrilldown": "జిల్లాల వారీగా చూడండి",
        "paused": "దరఖాస్తులు స్వీకరించడం లేదు",
        "showOnMap": "{name} ను మ్యాప్‌లో చూపించు",
        "noneHere": "ఏ భాగస్వామీ సరిపోలలేదు. వేరే రాష్ట్రం లేదా పథకాన్ని ప్రయత్నించండి.",
        "type": {
            "SCA": "రాష్ట్ర ఛానెలైజింగ్ ఏజెన్సీ",
            "PSB": "ప్రభుత్వ రంగ బ్యాంకు",
            "RRB": "ప్రాంతీయ గ్రామీణ బ్యాంకు",
            "NBFC_MFI": "ఎన్‌బీఎఫ్‌సీ మైక్రోఫైనాన్స్ సంస్థ",
        },
    },
}


def main() -> None:
    for locale, block in COVERAGE.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        coverage = data.setdefault("coverage", {})
        types = {**coverage.get("type", {}), **block["type"]}
        coverage.update({**block, "type": types})

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block) - 1} coverage, +{len(types)} partner types")


if __name__ == "__main__":
    main()
