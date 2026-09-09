"""One-off: the repayment-plan document's strings, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`planDisclaimer` is the one that must not be softened in translation. This document
carries a ministry name across the top and will be taken into a branch; it has to say on
its own face that the figures are an estimate and that nothing here approves a loan. A
translation that reads as a sanction letter is a serious problem, not a wording choice.

    python scripts/add-calculator-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

CALCULATOR = {
    "en": {
        "title": "Plan Your Repayment",
        "sub": "Understand your estimated repayment before applying.",
        "chartTitle": "Principal vs interest per year",
        "download": "Download repayment plan",
        "planTitle": "Repayment plan · Illustrative EMI schedule",
        "planOrgLine": "MoSJE · Government of India · Illustrative estimate",
        "planScheme": "Scheme: {scheme}",
        "colParameter": "Parameter",
        "colValue": "Value",
        "colPrincipalPaid": "Principal paid",
        "colInterestPaid": "Interest paid",
        "colTotalPaid": "Total paid",
        "planDisclaimer": (
            "An estimate from published rates, not an offer. SamarthSetu does not approve "
            "loans — the Channel Partner that sanctions yours sets the actual terms."
        ),
        "generatedAt": "Generated {when}",
    },
    "hi": {
        "title": "अपनी चुकौती की योजना बनाएँ",
        "sub": "आवेदन से पहले अनुमानित चुकौती समझ लें।",
        "chartTitle": "हर साल मूलधन बनाम ब्याज",
        "download": "चुकौती योजना डाउनलोड करें",
        "planTitle": "चुकौती योजना · उदाहरण के लिए ईएमआई अनुसूची",
        "planOrgLine": "सामाजिक न्याय मंत्रालय · भारत सरकार · अनुमानित गणना",
        "planScheme": "योजना: {scheme}",
        "colParameter": "मद",
        "colValue": "मान",
        "colPrincipalPaid": "चुकाया गया मूलधन",
        "colInterestPaid": "चुकाया गया ब्याज",
        "colTotalPaid": "कुल चुकाया",
        "planDisclaimer": (
            "यह प्रकाशित दरों से किया गया अनुमान है, कोई प्रस्ताव नहीं। SamarthSetu ऋण "
            "स्वीकृत नहीं करता — आपका ऋण स्वीकृत करने वाला चैनल पार्टनर वास्तविक शर्तें "
            "तय करता है।"
        ),
        "generatedAt": "{when} को तैयार",
    },
    "mr": {
        "title": "तुमच्या परतफेडीचे नियोजन करा",
        "sub": "अर्ज करण्यापूर्वी अंदाजित परतफेड समजून घ्या.",
        "chartTitle": "दरवर्षी मुद्दल विरुद्ध व्याज",
        "download": "परतफेड योजना डाउनलोड करा",
        "planTitle": "परतफेड योजना · उदाहरणादाखल ईएमआय वेळापत्रक",
        "planOrgLine": "सामाजिक न्याय मंत्रालय · भारत सरकार · अंदाजित गणना",
        "planScheme": "योजना: {scheme}",
        "colParameter": "बाब",
        "colValue": "मूल्य",
        "colPrincipalPaid": "भरलेले मुद्दल",
        "colInterestPaid": "भरलेले व्याज",
        "colTotalPaid": "एकूण भरले",
        "planDisclaimer": (
            "हा प्रकाशित दरांवरून केलेला अंदाज आहे, प्रस्ताव नाही. SamarthSetu कर्ज मंजूर "
            "करत नाही — तुमचे कर्ज मंजूर करणारा चॅनेल भागीदार प्रत्यक्ष अटी ठरवतो."
        ),
        "generatedAt": "{when} रोजी तयार",
    },
    "bn": {
        "title": "আপনার পরিশোধের পরিকল্পনা করুন",
        "sub": "আবেদনের আগে আনুমানিক পরিশোধ বুঝে নিন।",
        "chartTitle": "প্রতি বছর আসল বনাম সুদ",
        "download": "পরিশোধ পরিকল্পনা ডাউনলোড করুন",
        "planTitle": "পরিশোধ পরিকল্পনা · উদাহরণস্বরূপ ইএমআই সূচি",
        "planOrgLine": "সামাজিক ন্যায় মন্ত্রক · ভারত সরকার · আনুমানিক হিসাব",
        "planScheme": "প্রকল্প: {scheme}",
        "colParameter": "বিষয়",
        "colValue": "মান",
        "colPrincipalPaid": "পরিশোধিত আসল",
        "colInterestPaid": "পরিশোধিত সুদ",
        "colTotalPaid": "মোট পরিশোধ",
        "planDisclaimer": (
            "এটি প্রকাশিত হার থেকে করা একটি অনুমান, কোনও প্রস্তাব নয়। SamarthSetu ঋণ "
            "অনুমোদন করে না — যে চ্যানেল পার্টনার আপনার ঋণ মঞ্জুর করবেন, তিনিই প্রকৃত "
            "শর্ত ঠিক করেন।"
        ),
        "generatedAt": "{when}-এ তৈরি",
    },
    "ta": {
        "title": "உங்கள் திருப்பிச் செலுத்தலைத் திட்டமிடுங்கள்",
        "sub": "விண்ணப்பிக்கும் முன் மதிப்பிடப்பட்ட திருப்பிச் செலுத்தலைப் புரிந்துகொள்ளுங்கள்.",
        "chartTitle": "ஆண்டுதோறும் அசல் மற்றும் வட்டி",
        "download": "திருப்பிச் செலுத்தும் திட்டத்தைப் பதிவிறக்கு",
        "planTitle": "திருப்பிச் செலுத்தும் திட்டம் · எடுத்துக்காட்டு இஎம்ஐ அட்டவணை",
        "planOrgLine": "சமூக நீதி அமைச்சகம் · இந்திய அரசு · மதிப்பீட்டுக் கணக்கு",
        "planScheme": "திட்டம்: {scheme}",
        "colParameter": "விவரம்",
        "colValue": "மதிப்பு",
        "colPrincipalPaid": "செலுத்திய அசல்",
        "colInterestPaid": "செலுத்திய வட்டி",
        "colTotalPaid": "மொத்தம் செலுத்தியது",
        "planDisclaimer": (
            "இது வெளியிடப்பட்ட விகிதங்களிலிருந்து செய்யப்பட்ட மதிப்பீடு, ஒரு சலுகை அல்ல. "
            "SamarthSetu கடனை ஒப்புதல் அளிப்பதில்லை — உங்கள் கடனை ஒப்புதல் அளிக்கும் சேனல் "
            "பங்குதாரரே உண்மையான நிபந்தனைகளை நிர்ணயிக்கிறார்."
        ),
        "generatedAt": "{when} அன்று உருவாக்கப்பட்டது",
    },
    "te": {
        "title": "మీ తిరిగి చెల్లింపును ప్రణాళిక చేసుకోండి",
        "sub": "దరఖాస్తు చేసే ముందు అంచనా తిరిగి చెల్లింపును అర్థం చేసుకోండి.",
        "chartTitle": "ఏటా అసలు మరియు వడ్డీ",
        "download": "తిరిగి చెల్లింపు ప్రణాళికను డౌన్‌లోడ్ చేయండి",
        "planTitle": "తిరిగి చెల్లింపు ప్రణాళిక · ఉదాహరణ ఈఎంఐ షెడ్యూల్",
        "planOrgLine": "సామాజిక న్యాయ మంత్రిత్వ శాఖ · భారత ప్రభుత్వం · అంచనా లెక్క",
        "planScheme": "పథకం: {scheme}",
        "colParameter": "అంశం",
        "colValue": "విలువ",
        "colPrincipalPaid": "చెల్లించిన అసలు",
        "colInterestPaid": "చెల్లించిన వడ్డీ",
        "colTotalPaid": "మొత్తం చెల్లించినది",
        "planDisclaimer": (
            "ఇది ప్రచురించిన రేట్ల నుండి చేసిన అంచనా, ఆఫర్ కాదు. SamarthSetu రుణాలను "
            "ఆమోదించదు — మీ రుణాన్ని మంజూరు చేసే ఛానెల్ భాగస్వామి వాస్తవ షరతులను "
            "నిర్ణయిస్తారు."
        ),
        "generatedAt": "{when}న రూపొందించబడింది",
    },
}

# `print` was the label on the old header button. The control is now the download at the
# foot of the page, and the string it used has no reader left.
REMOVED = ["print"]


def main() -> None:
    for locale, block in CALCULATOR.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        calculator = data.setdefault("calculator", {})
        calculator.update(block)
        dropped = [key for key in REMOVED if calculator.pop(key, None) is not None]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} calculator, -{len(dropped)}")


if __name__ == "__main__":
    main()
