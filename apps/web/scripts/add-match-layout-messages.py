"""One-off: the strings the matches page needs, drawn to the SamarthSetu design drop.

Kept in the repo, like `add-fit-messages.py`, as the record of which strings were added
together and in which languages — useful when a reviewer sits down to check the four
draft locales (OPEN_ITEMS OI-4, OI-33).

Two of these deserve a reviewer's attention rather than a glance:

  profileMatchNote  the disclaimer that lets the score band be as large as it is. The
                    number orders the list; it is not the eligibility verdict and it is
                    not a prediction of what a Channel Partner will decide. A translation
                    that softens it into "your chances" is a bug, not a preference.

  criteria.*        the short labels the card shows in place of the engine sentence. They
                    must read as "this criterion is satisfied", never as "this criterion
                    is approved". The engine sentence is still on the row, in `title`.

    python scripts/add-match-layout-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

MATCHES = {
    "en": {
        "title": "Your Scheme Matches",
        "sub": "We found schemes that closely match your profile.",
        "compareSchemes": "Compare schemes",
        "profileMatchEyebrow": "Your profile match",
        "profileMatchLabel": "Profile match: {pct} percent",
        "profileMatchNote": (
            "This score shows how closely your profile matches the available scheme "
            "criteria. Final eligibility is subject to official verification."
        ),
        "bandHigh": "High Match",
        "bandGood": "Good Match",
        "bandPartial": "Partial Match",
        "profileMatchPct": "{pct}% Profile Match",
        "potentialFinancing": "Potential financing",
        "perYear": "{min}–{max}% p.a.",
        "perYearFlat": "{rate}% p.a.",
        "upToYears": "Up to {years} years",
        "upToMonths": "Up to {count} months",
        "viewEligibility": "View Eligibility",
        "details": "Details",
        "whyNotThis": "Why not this scheme?",
        "someCriteria": (
            "Some criteria may not fit your profile. "
            "Tap “Why not this scheme?” for details."
        ),
        "criteria": {
            "socialCategory": "Social category supported",
            "familyIncome": "Family income supported",
            "projectCost": "Project cost supported",
            "enterpriseType": "Enterprise type supported",
            "coursePurpose": "Course purpose supported",
            "admission": "Admission confirmed",
            "fundingShare": "Funding share supported",
        },
    },
    "hi": {
        "title": "आपकी मैच हुई योजनाएँ",
        "sub": "हमें ऐसी योजनाएँ मिलीं जो आपकी प्रोफ़ाइल से क़रीब से मेल खाती हैं।",
        "compareSchemes": "योजनाओं की तुलना करें",
        "profileMatchEyebrow": "आपकी प्रोफ़ाइल का मिलान",
        "profileMatchLabel": "प्रोफ़ाइल मिलान: {pct} प्रतिशत",
        "profileMatchNote": (
            "यह अंक दिखाता है कि आपकी प्रोफ़ाइल उपलब्ध योजनाओं की शर्तों से कितनी मेल "
            "खाती है। अंतिम पात्रता आधिकारिक सत्यापन के अधीन है।"
        ),
        "bandHigh": "उच्च मिलान",
        "bandGood": "अच्छा मिलान",
        "bandPartial": "आंशिक मिलान",
        "profileMatchPct": "{pct}% प्रोफ़ाइल मिलान",
        "potentialFinancing": "संभावित वित्तपोषण",
        "perYear": "{min}–{max}% प्रति वर्ष",
        "perYearFlat": "{rate}% प्रति वर्ष",
        "upToYears": "{years} साल तक",
        "upToMonths": "{count} महीने तक",
        "viewEligibility": "पात्रता देखें",
        "details": "विवरण",
        "whyNotThis": "यह योजना क्यों नहीं?",
        "someCriteria": (
            "कुछ शर्तें आपकी प्रोफ़ाइल से मेल नहीं खा सकतीं। "
            "विवरण के लिए “यह योजना क्यों नहीं?” दबाएँ।"
        ),
        "criteria": {
            "socialCategory": "सामाजिक श्रेणी उपयुक्त",
            "familyIncome": "पारिवारिक आय उपयुक्त",
            "projectCost": "परियोजना लागत उपयुक्त",
            "enterpriseType": "उद्यम प्रकार उपयुक्त",
            "coursePurpose": "पाठ्यक्रम उद्देश्य उपयुक्त",
            "admission": "प्रवेश की पुष्टि",
            "fundingShare": "वित्तपोषण हिस्सा उपयुक्त",
        },
    },
    "mr": {
        "title": "तुमच्याशी जुळणाऱ्या योजना",
        "sub": "तुमच्या प्रोफाइलशी जवळून जुळणाऱ्या योजना आम्हाला मिळाल्या.",
        "compareSchemes": "योजनांची तुलना करा",
        "profileMatchEyebrow": "तुमच्या प्रोफाइलचे जुळणे",
        "profileMatchLabel": "प्रोफाइल जुळणी: {pct} टक्के",
        "profileMatchNote": (
            "हा गुण दाखवतो की तुमची प्रोफाइल उपलब्ध योजनांच्या निकषांशी किती जुळते. "
            "अंतिम पात्रता अधिकृत पडताळणीच्या अधीन आहे."
        ),
        "bandHigh": "उच्च जुळणी",
        "bandGood": "चांगली जुळणी",
        "bandPartial": "अंशतः जुळणी",
        "profileMatchPct": "{pct}% प्रोफाइल जुळणी",
        "potentialFinancing": "संभाव्य वित्तपुरवठा",
        "perYear": "{min}–{max}% प्रतिवर्ष",
        "perYearFlat": "{rate}% प्रतिवर्ष",
        "upToYears": "{years} वर्षांपर्यंत",
        "upToMonths": "{count} महिन्यांपर्यंत",
        "viewEligibility": "पात्रता पाहा",
        "details": "तपशील",
        "whyNotThis": "ही योजना का नाही?",
        "someCriteria": (
            "काही निकष तुमच्या प्रोफाइलशी जुळणार नाहीत. "
            "तपशिलासाठी “ही योजना का नाही?” दाबा."
        ),
        "criteria": {
            "socialCategory": "सामाजिक प्रवर्ग योग्य",
            "familyIncome": "कौटुंबिक उत्पन्न योग्य",
            "projectCost": "प्रकल्प खर्च योग्य",
            "enterpriseType": "उद्यम प्रकार योग्य",
            "coursePurpose": "अभ्यासक्रम उद्देश योग्य",
            "admission": "प्रवेश निश्चित",
            "fundingShare": "वित्तपुरवठा हिस्सा योग्य",
        },
    },
    "bn": {
        "title": "আপনার সঙ্গে মেলা প্রকল্প",
        "sub": "আপনার প্রোফাইলের সঙ্গে ঘনিষ্ঠভাবে মেলে এমন প্রকল্প আমরা পেয়েছি।",
        "compareSchemes": "প্রকল্পগুলি তুলনা করুন",
        "profileMatchEyebrow": "আপনার প্রোফাইলের মিল",
        "profileMatchLabel": "প্রোফাইলের মিল: {pct} শতাংশ",
        "profileMatchNote": (
            "এই স্কোর দেখায় আপনার প্রোফাইল উপলব্ধ প্রকল্পের শর্তের সঙ্গে কতটা মেলে। "
            "চূড়ান্ত যোগ্যতা সরকারি যাচাইয়ের উপর নির্ভরশীল।"
        ),
        "bandHigh": "উচ্চ মিল",
        "bandGood": "ভালো মিল",
        "bandPartial": "আংশিক মিল",
        "profileMatchPct": "{pct}% প্রোফাইলের মিল",
        "potentialFinancing": "সম্ভাব্য অর্থায়ন",
        "perYear": "{min}–{max}% বার্ষিক",
        "perYearFlat": "{rate}% বার্ষিক",
        "upToYears": "{years} বছর পর্যন্ত",
        "upToMonths": "{count} মাস পর্যন্ত",
        "viewEligibility": "যোগ্যতা দেখুন",
        "details": "বিবরণ",
        "whyNotThis": "এই প্রকল্পটি কেন নয়?",
        "someCriteria": (
            "কিছু শর্ত আপনার প্রোফাইলের সঙ্গে না-ও মিলতে পারে। "
            "বিস্তারিত জানতে “এই প্রকল্পটি কেন নয়?” চাপুন।"
        ),
        "criteria": {
            "socialCategory": "সামাজিক শ্রেণি উপযুক্ত",
            "familyIncome": "পারিবারিক আয় উপযুক্ত",
            "projectCost": "প্রকল্প ব্যয় উপযুক্ত",
            "enterpriseType": "উদ্যোগের ধরন উপযুক্ত",
            "coursePurpose": "পাঠ্যক্রমের উদ্দেশ্য উপযুক্ত",
            "admission": "ভর্তি নিশ্চিত",
            "fundingShare": "অর্থায়নের অংশ উপযুক্ত",
        },
    },
    "ta": {
        "title": "உங்களுக்குப் பொருந்தும் திட்டங்கள்",
        "sub": "உங்கள் சுயவிவரத்துடன் நெருக்கமாகப் பொருந்தும் திட்டங்களைக் கண்டறிந்துள்ளோம்.",
        "compareSchemes": "திட்டங்களை ஒப்பிடுக",
        "profileMatchEyebrow": "உங்கள் சுயவிவரப் பொருத்தம்",
        "profileMatchLabel": "சுயவிவரப் பொருத்தம்: {pct} சதவீதம்",
        "profileMatchNote": (
            "கிடைக்கும் திட்டங்களின் நிபந்தனைகளுடன் உங்கள் சுயவிவரம் எவ்வளவு "
            "பொருந்துகிறது என்பதை இந்த மதிப்பெண் காட்டுகிறது. இறுதித் தகுதி அரசு "
            "சரிபார்ப்புக்கு உட்பட்டது."
        ),
        "bandHigh": "உயர் பொருத்தம்",
        "bandGood": "நல்ல பொருத்தம்",
        "bandPartial": "பகுதிப் பொருத்தம்",
        "profileMatchPct": "{pct}% சுயவிவரப் பொருத்தம்",
        "potentialFinancing": "சாத்தியமான நிதியுதவி",
        "perYear": "{min}–{max}% ஆண்டுக்கு",
        "perYearFlat": "{rate}% ஆண்டுக்கு",
        "upToYears": "{years} ஆண்டுகள் வரை",
        "upToMonths": "{count} மாதங்கள் வரை",
        "viewEligibility": "தகுதியைப் பார்க்க",
        "details": "விவரங்கள்",
        "whyNotThis": "இந்தத் திட்டம் ஏன் இல்லை?",
        "someCriteria": (
            "சில நிபந்தனைகள் உங்கள் சுயவிவரத்துடன் பொருந்தாமல் இருக்கலாம். "
            "விவரங்களுக்கு “இந்தத் திட்டம் ஏன் இல்லை?” என்பதைத் தட்டவும்."
        ),
        "criteria": {
            "socialCategory": "சமூகப் பிரிவு பொருந்துகிறது",
            "familyIncome": "குடும்ப வருமானம் பொருந்துகிறது",
            "projectCost": "திட்டச் செலவு பொருந்துகிறது",
            "enterpriseType": "தொழில் வகை பொருந்துகிறது",
            "coursePurpose": "படிப்பு நோக்கம் பொருந்துகிறது",
            "admission": "சேர்க்கை உறுதி",
            "fundingShare": "நிதிப் பங்கு பொருந்துகிறது",
        },
    },
    "te": {
        "title": "మీకు సరిపోయే పథకాలు",
        "sub": "మీ ప్రొఫైల్‌కు దగ్గరగా సరిపోయే పథకాలను మేము కనుగొన్నాము.",
        "compareSchemes": "పథకాలను పోల్చండి",
        "profileMatchEyebrow": "మీ ప్రొఫైల్ సరిపోలిక",
        "profileMatchLabel": "ప్రొఫైల్ సరిపోలిక: {pct} శాతం",
        "profileMatchNote": (
            "అందుబాటులో ఉన్న పథకాల నిబంధనలతో మీ ప్రొఫైల్ ఎంతవరకు సరిపోతుందో ఈ స్కోరు "
            "చూపుతుంది. తుది అర్హత అధికారిక ధ్రువీకరణపై ఆధారపడి ఉంటుంది."
        ),
        "bandHigh": "అధిక సరిపోలిక",
        "bandGood": "మంచి సరిపోలిక",
        "bandPartial": "పాక్షిక సరిపోలిక",
        "profileMatchPct": "{pct}% ప్రొఫైల్ సరిపోలిక",
        "potentialFinancing": "సంభావ్య ఆర్థిక సహాయం",
        "perYear": "{min}–{max}% సంవత్సరానికి",
        "perYearFlat": "{rate}% సంవత్సరానికి",
        "upToYears": "{years} సంవత్సరాల వరకు",
        "upToMonths": "{count} నెలల వరకు",
        "viewEligibility": "అర్హత చూడండి",
        "details": "వివరాలు",
        "whyNotThis": "ఈ పథకం ఎందుకు కాదు?",
        "someCriteria": (
            "కొన్ని నిబంధనలు మీ ప్రొఫైల్‌కు సరిపోకపోవచ్చు. "
            "వివరాల కోసం “ఈ పథకం ఎందుకు కాదు?” నొక్కండి."
        ),
        "criteria": {
            "socialCategory": "సామాజిక వర్గం సరిపోతుంది",
            "familyIncome": "కుటుంబ ఆదాయం సరిపోతుంది",
            "projectCost": "ప్రాజెక్ట్ వ్యయం సరిపోతుంది",
            "enterpriseType": "సంస్థ రకం సరిపోతుంది",
            "coursePurpose": "కోర్సు ఉద్దేశం సరిపోతుంది",
            "admission": "ప్రవేశం ధృవీకరించబడింది",
            "fundingShare": "ఆర్థిక వాటా సరిపోతుంది",
        },
    },
}

# The drop prints the rupee sign, not "Rs". This is the only place the app renders an
# amount, so changing it here changes it everywhere at once — which is the point: a page
# reading "₹9,00,000" beside another reading "Rs 9,00,000" is worse than either.
# Engine-generated sentences keep whatever the rule pack says; those are provenance text.
RUPEES = {
    "en": "₹{amount}",
    "hi": "₹{amount}",
    "mr": "₹{amount}",
    "bn": "₹{amount}",
    "ta": "₹{amount}",
    "te": "₹{amount}",
}

# What the redesign stopped rendering. `rank` was a "#2" in the corner — the list is
# already in rank order and the one position worth naming carries the best-match chip.
# The rest were headings and labels the drop replaced. A key no screen reads is a key a
# reviewer has to go looking for, so they go out with the change that stopped using them
# — from all six catalogues at once, or parity breaks.
REMOVED = [
    "rank",
    "seeDetail",
    "whyMatched",
    "whyBlocked",
    "whyRanked",
    "indicativeAmount",
    "unverifiedFigures",
]


def main() -> None:
    for locale, block in MATCHES.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        matches = data.setdefault("matches", {})
        criteria = {**matches.get("criteria", {}), **block["criteria"]}
        matches.update({**block, "criteria": criteria})
        dropped = [key for key in REMOVED if matches.pop(key, None) is not None]

        data.setdefault("common", {})["rupees"] = RUPEES[locale]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"{locale}: {len(block) - 1} keys + {len(criteria)} criteria, "
            f"-{len(dropped)} removed"
        )


if __name__ == "__main__":
    main()
