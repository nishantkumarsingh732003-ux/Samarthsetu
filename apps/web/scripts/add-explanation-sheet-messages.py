"""One-off: the two explanation panels on the matches page, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

Three things a reviewer should weigh rather than skim.

`eyebrow` is NOT "Explainable AI", which is what the design drop put there. No AI decides
anything on this path: a deterministic, versioned rule engine does, and the whole
architecture exists so that a verdict can be replayed from a rule id (CLAUDE.md rule 1).
A badge claiming AI made the decision would undercut the one guarantee this product makes.

`disclaimer` on both panels has to keep saying that this service does not approve
anything. The panels look confident — a ring, ticks, a five-step pipeline — and the
sentence under them is what keeps that from reading as a sanction.

`differenceOver` / `differenceUnder` are two separate strings on purpose. A ceiling and a
floor fail in opposite directions and "above"/"below" is the whole content of the message;
a translation that uses one word for both tells half the citizens the wrong thing.

    python scripts/add-explanation-sheet-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

ELIGIBILITY = {
    "en": {
        "eyebrow": "Rule engine · Fully traceable",
        "title": "Why this scheme matches you",
        "profileMatch": "Profile match {pct}%",
        "passed": "Passed",
        "notMet": "Not met",
        "notChecked": "Not checked",
        "yourProfile": "Your profile",
        "requirement": "Requirement",
        "whyRecommended": "Why was this recommended?",
        "stepProfile": "Profile",
        "stepRules": "Rules",
        "stepFinancing": "Financing",
        "stepMatch": "Match",
        "stepRecommend": "Recommend",
        "disclaimer": (
            "Decided by the published scheme criteria and the answers you gave, not by a "
            "person or a model. SamarthSetu does not approve loans — the Channel Partner "
            "you apply through does."
        ),
        "openScheme": "Open scheme details",
        "calculateEmi": "Calculate EMI",
    },
    "hi": {
        "eyebrow": "नियम इंजन · पूरी तरह पारदर्शी",
        "title": "यह योजना आपसे क्यों मेल खाती है",
        "profileMatch": "प्रोफ़ाइल मिलान {pct}%",
        "passed": "पूरा हुआ",
        "notMet": "पूरा नहीं हुआ",
        "notChecked": "जाँचा नहीं गया",
        "yourProfile": "आपकी प्रोफ़ाइल",
        "requirement": "आवश्यकता",
        "whyRecommended": "यह क्यों सुझाई गई?",
        "stepProfile": "प्रोफ़ाइल",
        "stepRules": "नियम",
        "stepFinancing": "वित्त",
        "stepMatch": "मिलान",
        "stepRecommend": "सुझाव",
        "disclaimer": (
            "यह निर्णय प्रकाशित योजना शर्तों और आपके दिए उत्तरों से हुआ है, किसी व्यक्ति "
            "या मॉडल से नहीं। SamarthSetu ऋण स्वीकृत नहीं करता — जिस चैनल पार्टनर से आप "
            "आवेदन करेंगे, वह करता है।"
        ),
        "openScheme": "योजना का विवरण खोलें",
        "calculateEmi": "ईएमआई निकालें",
    },
    "mr": {
        "eyebrow": "नियम इंजिन · पूर्णपणे पारदर्शक",
        "title": "ही योजना तुमच्याशी का जुळते",
        "profileMatch": "प्रोफाइल जुळणी {pct}%",
        "passed": "पूर्ण",
        "notMet": "पूर्ण नाही",
        "notChecked": "तपासले नाही",
        "yourProfile": "तुमची प्रोफाइल",
        "requirement": "आवश्यकता",
        "whyRecommended": "ही का सुचवली गेली?",
        "stepProfile": "प्रोफाइल",
        "stepRules": "नियम",
        "stepFinancing": "वित्त",
        "stepMatch": "जुळणी",
        "stepRecommend": "शिफारस",
        "disclaimer": (
            "हा निर्णय प्रकाशित योजना निकष आणि तुम्ही दिलेल्या उत्तरांवरून झाला आहे, "
            "कोणत्या व्यक्ती किंवा मॉडेलवरून नाही. SamarthSetu कर्ज मंजूर करत नाही — "
            "ज्या चॅनेल भागीदारामार्फत तुम्ही अर्ज कराल, तो करतो."
        ),
        "openScheme": "योजनेचा तपशील उघडा",
        "calculateEmi": "ईएमआय काढा",
    },
    "bn": {
        "eyebrow": "নিয়ম ইঞ্জিন · সম্পূর্ণ স্বচ্ছ",
        "title": "এই প্রকল্পটি কেন আপনার সঙ্গে মেলে",
        "profileMatch": "প্রোফাইলের মিল {pct}%",
        "passed": "পূরণ হয়েছে",
        "notMet": "পূরণ হয়নি",
        "notChecked": "যাচাই করা হয়নি",
        "yourProfile": "আপনার প্রোফাইল",
        "requirement": "প্রয়োজন",
        "whyRecommended": "এটি কেন প্রস্তাব করা হল?",
        "stepProfile": "প্রোফাইল",
        "stepRules": "নিয়ম",
        "stepFinancing": "অর্থায়ন",
        "stepMatch": "মিল",
        "stepRecommend": "সুপারিশ",
        "disclaimer": (
            "এই সিদ্ধান্ত প্রকাশিত প্রকল্পের শর্ত ও আপনার দেওয়া উত্তর থেকে হয়েছে, কোনও "
            "ব্যক্তি বা মডেল থেকে নয়। SamarthSetu ঋণ অনুমোদন করে না — আপনি যে চ্যানেল "
            "পার্টনারের মাধ্যমে আবেদন করবেন, তিনি করেন।"
        ),
        "openScheme": "প্রকল্পের বিবরণ খুলুন",
        "calculateEmi": "ইএমআই হিসাব করুন",
    },
    "ta": {
        "eyebrow": "விதி இயந்திரம் · முழுமையாகக் கண்டறியத்தக்கது",
        "title": "இந்தத் திட்டம் ஏன் உங்களுக்குப் பொருந்துகிறது",
        "profileMatch": "சுயவிவரப் பொருத்தம் {pct}%",
        "passed": "நிறைவேறியது",
        "notMet": "நிறைவேறவில்லை",
        "notChecked": "சரிபார்க்கப்படவில்லை",
        "yourProfile": "உங்கள் சுயவிவரம்",
        "requirement": "தேவை",
        "whyRecommended": "இது ஏன் பரிந்துரைக்கப்பட்டது?",
        "stepProfile": "சுயவிவரம்",
        "stepRules": "விதிகள்",
        "stepFinancing": "நிதி",
        "stepMatch": "பொருத்தம்",
        "stepRecommend": "பரிந்துரை",
        "disclaimer": (
            "இந்த முடிவு வெளியிடப்பட்ட திட்ட நிபந்தனைகள் மற்றும் நீங்கள் அளித்த "
            "பதில்களிலிருந்து வந்தது, ஒரு நபரிடமிருந்தோ மாதிரியிலிருந்தோ அல்ல. "
            "SamarthSetu கடனை ஒப்புதல் அளிப்பதில்லை — நீங்கள் விண்ணப்பிக்கும் சேனல் "
            "பங்குதாரரே அளிக்கிறார்."
        ),
        "openScheme": "திட்ட விவரங்களைத் திற",
        "calculateEmi": "இஎம்ஐ கணக்கிடு",
    },
    "te": {
        "eyebrow": "నిబంధనల ఇంజిన్ · పూర్తిగా పారదర్శకం",
        "title": "ఈ పథకం మీకు ఎందుకు సరిపోతుంది",
        "profileMatch": "ప్రొఫైల్ సరిపోలిక {pct}%",
        "passed": "నెరవేరింది",
        "notMet": "నెరవేరలేదు",
        "notChecked": "తనిఖీ చేయలేదు",
        "yourProfile": "మీ ప్రొఫైల్",
        "requirement": "అవసరం",
        "whyRecommended": "ఇది ఎందుకు సిఫారసు చేయబడింది?",
        "stepProfile": "ప్రొఫైల్",
        "stepRules": "నిబంధనలు",
        "stepFinancing": "ఆర్థికం",
        "stepMatch": "సరిపోలిక",
        "stepRecommend": "సిఫారసు",
        "disclaimer": (
            "ఈ నిర్ణయం ప్రచురించిన పథక నిబంధనలు మరియు మీరు ఇచ్చిన సమాధానాల నుండి "
            "వచ్చింది, ఒక వ్యక్తి లేదా మోడల్ నుండి కాదు. SamarthSetu రుణాలను ఆమోదించదు — "
            "మీరు దరఖాస్తు చేసే ఛానెల్ భాగస్వామి ఆమోదిస్తారు."
        ),
        "openScheme": "పథకం వివరాలు తెరవండి",
        "calculateEmi": "ఈఎంఐ లెక్కించండి",
    },
}

WHY_NOT = {
    "en": {
        "title": "Why isn't this scheme recommended?",
        "yourValue": "Your {criterion}",
        "schemeLimit": "Scheme limit",
        "differenceOver": "Difference: {amount} — your {criterion} is above what this scheme supports.",
        "differenceUnder": "Difference: {amount} — your {criterion} is below what this scheme supports.",
        "criteriaNotMet": "Criteria not met",
        "yourProfile": "Your:",
        "requirement": "Requirement:",
        "tryAlternatives": "Try these alternatives",
        "disclaimer": "Checked against the published rules for this scheme. Change an answer and the rules run again.",
        "readTheRules": "Read the rules",
        "updateProfile": "Update my answers",
    },
    "hi": {
        "title": "यह योजना क्यों नहीं सुझाई गई?",
        "yourValue": "आपकी {criterion}",
        "schemeLimit": "योजना की सीमा",
        "differenceOver": "अंतर: {amount} — आपकी {criterion} इस योजना की सीमा से अधिक है।",
        "differenceUnder": "अंतर: {amount} — आपकी {criterion} इस योजना की सीमा से कम है।",
        "criteriaNotMet": "जो शर्तें पूरी नहीं हुईं",
        "yourProfile": "आपका:",
        "requirement": "आवश्यक:",
        "tryAlternatives": "ये विकल्प देखें",
        "disclaimer": "इस योजना के प्रकाशित नियमों से जाँचा गया। उत्तर बदलिए और नियम फिर से चलेंगे।",
        "readTheRules": "नियम पढ़ें",
        "updateProfile": "मेरे उत्तर बदलें",
    },
    "mr": {
        "title": "ही योजना का सुचवली गेली नाही?",
        "yourValue": "तुमचा {criterion}",
        "schemeLimit": "योजनेची मर्यादा",
        "differenceOver": "फरक: {amount} — तुमचा {criterion} या योजनेच्या मर्यादेपेक्षा जास्त आहे.",
        "differenceUnder": "फरक: {amount} — तुमचा {criterion} या योजनेच्या मर्यादेपेक्षा कमी आहे.",
        "criteriaNotMet": "पूर्ण न झालेले निकष",
        "yourProfile": "तुमचे:",
        "requirement": "आवश्यक:",
        "tryAlternatives": "हे पर्याय पाहा",
        "disclaimer": "या योजनेच्या प्रकाशित नियमांनुसार तपासले. उत्तर बदला, नियम पुन्हा चालतील.",
        "readTheRules": "नियम वाचा",
        "updateProfile": "माझी उत्तरे बदला",
    },
    "bn": {
        "title": "এই প্রকল্পটি কেন প্রস্তাব করা হয়নি?",
        "yourValue": "আপনার {criterion}",
        "schemeLimit": "প্রকল্পের সীমা",
        "differenceOver": "পার্থক্য: {amount} — আপনার {criterion} এই প্রকল্পের সীমার চেয়ে বেশি।",
        "differenceUnder": "পার্থক্য: {amount} — আপনার {criterion} এই প্রকল্পের সীমার চেয়ে কম।",
        "criteriaNotMet": "যে শর্তগুলি পূরণ হয়নি",
        "yourProfile": "আপনার:",
        "requirement": "প্রয়োজন:",
        "tryAlternatives": "এই বিকল্পগুলি দেখুন",
        "disclaimer": "এই প্রকল্পের প্রকাশিত নিয়ম অনুযায়ী যাচাই করা হয়েছে। উত্তর বদলালে নিয়ম আবার চলবে।",
        "readTheRules": "নিয়ম পড়ুন",
        "updateProfile": "আমার উত্তর বদলান",
    },
    "ta": {
        "title": "இந்தத் திட்டம் ஏன் பரிந்துரைக்கப்படவில்லை?",
        "yourValue": "உங்கள் {criterion}",
        "schemeLimit": "திட்ட வரம்பு",
        "differenceOver": "வேறுபாடு: {amount} — உங்கள் {criterion} இத்திட்டத்தின் வரம்பை விட அதிகம்.",
        "differenceUnder": "வேறுபாடு: {amount} — உங்கள் {criterion} இத்திட்டத்தின் வரம்பை விடக் குறைவு.",
        "criteriaNotMet": "நிறைவேறாத நிபந்தனைகள்",
        "yourProfile": "உங்களுடையது:",
        "requirement": "தேவை:",
        "tryAlternatives": "இந்த மாற்றுகளைப் பாருங்கள்",
        "disclaimer": "இத்திட்டத்தின் வெளியிடப்பட்ட விதிகளுடன் சரிபார்க்கப்பட்டது. ஒரு பதிலை மாற்றினால் விதிகள் மீண்டும் இயங்கும்.",
        "readTheRules": "விதிகளைப் படிக்க",
        "updateProfile": "என் பதில்களை மாற்று",
    },
    "te": {
        "title": "ఈ పథకం ఎందుకు సిఫారసు చేయబడలేదు?",
        "yourValue": "మీ {criterion}",
        "schemeLimit": "పథకం పరిమితి",
        "differenceOver": "తేడా: {amount} — మీ {criterion} ఈ పథకం పరిమితి కంటే ఎక్కువ.",
        "differenceUnder": "తేడా: {amount} — మీ {criterion} ఈ పథకం పరిమితి కంటే తక్కువ.",
        "criteriaNotMet": "నెరవేరని నిబంధనలు",
        "yourProfile": "మీది:",
        "requirement": "అవసరం:",
        "tryAlternatives": "ఈ ప్రత్యామ్నాయాలను చూడండి",
        "disclaimer": "ఈ పథకం ప్రచురించిన నిబంధనలతో తనిఖీ చేయబడింది. సమాధానం మార్చితే నిబంధనలు మళ్లీ నడుస్తాయి.",
        "readTheRules": "నిబంధనలు చదవండి",
        "updateProfile": "నా సమాధానాలు మార్చండి",
    },
}

# Both panels need a name for their ✕ button. An icon alone announces nothing, and there
# was no shared "close" string — `Modal` took its label from each caller.
CLOSE = {
    "en": "Close",
    "hi": "बंद करें",
    "mr": "बंद करा",
    "bn": "বন্ধ করুন",
    "ta": "மூடு",
    "te": "మూసివేయండి",
}


def main() -> None:
    for locale in ELIGIBILITY:
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        data.setdefault("eligibilitySheet", {}).update(ELIGIBILITY[locale])
        data.setdefault("whyNotSheet", {}).update(WHY_NOT[locale])
        data.setdefault("common", {})["close"] = CLOSE[locale]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"{locale}: +{len(ELIGIBILITY[locale])} eligibilitySheet, "
            f"+{len(WHY_NOT[locale])} whyNotSheet, +1 common"
        )


if __name__ == "__main__":
    main()
