"""One-off: the document tiles' statuses and upload labels, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`statusPassed` MUST NOT BE TRANSLATED AS "VERIFIED". What the API does is an automated
check — it detects the document type and blacks out any ID number before storing — and it
reports PASSED. Nobody has confirmed that a caste certificate is genuine. A green
"Verified" against one, in any language, is a claim this product cannot make and the
single worst thing this page could say. "Checks passed" is what actually happened, and
every translation here says that and not more.

    python scripts/add-documents-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

DOCUMENTS = {
    "en": {
        "title": "My documents",
        "sub": "Upload the documents your application needs.",
        "pickApplication": "Application",
        "noApplication": "Nothing to upload against yet",
        "startFromMatches": "See your matches",
        "notDisplayed": "Contents are never shown here, only the check result.",
        "statusPassed": "Checks passed",
        "statusPending": "Checking",
        "statusWarning": "Needs a look",
        "statusFailed": "Not accepted",
        "statusMissing": "Not uploaded",
        "upload": "Upload",
        "update": "Replace",
    },
    "hi": {
        "title": "मेरे दस्तावेज़",
        "sub": "आपके आवेदन के लिए ज़रूरी दस्तावेज़ भेजें।",
        "pickApplication": "आवेदन",
        "noApplication": "अभी जोड़ने के लिए कोई आवेदन नहीं",
        "startFromMatches": "अपने मैच देखें",
        "notDisplayed": "यहाँ सामग्री कभी नहीं दिखती, केवल जाँच का परिणाम।",
        "statusPassed": "जाँच पूरी हुई",
        "statusPending": "जाँच हो रही है",
        "statusWarning": "एक बार देख लें",
        "statusFailed": "स्वीकार नहीं हुआ",
        "statusMissing": "नहीं भेजा",
        "upload": "भेजें",
        "update": "बदलें",
    },
    "mr": {
        "title": "माझी कागदपत्रे",
        "sub": "तुमच्या अर्जासाठी आवश्यक कागदपत्रे पाठवा.",
        "pickApplication": "अर्ज",
        "noApplication": "अजून जोडण्यासाठी कोणताही अर्ज नाही",
        "startFromMatches": "तुमच्या जुळणी पाहा",
        "notDisplayed": "इथे मजकूर कधीच दिसत नाही, फक्त तपासणीचा निकाल.",
        "statusPassed": "तपासणी पूर्ण",
        "statusPending": "तपासणी सुरू आहे",
        "statusWarning": "एकदा पाहा",
        "statusFailed": "स्वीकारले नाही",
        "statusMissing": "पाठवले नाही",
        "upload": "पाठवा",
        "update": "बदला",
    },
    "bn": {
        "title": "আমার নথিপত্র",
        "sub": "আপনার আবেদনের জন্য প্রয়োজনীয় নথি পাঠান।",
        "pickApplication": "আবেদন",
        "noApplication": "এখনও যুক্ত করার মতো কোনও আবেদন নেই",
        "startFromMatches": "আপনার মিল দেখুন",
        "notDisplayed": "এখানে বিষয়বস্তু কখনও দেখানো হয় না, কেবল যাচাইয়ের ফল।",
        "statusPassed": "যাচাই সম্পন্ন",
        "statusPending": "যাচাই চলছে",
        "statusWarning": "একবার দেখুন",
        "statusFailed": "গ্রহণ করা হয়নি",
        "statusMissing": "পাঠানো হয়নি",
        "upload": "পাঠান",
        "update": "বদলান",
    },
    "ta": {
        "title": "எனது ஆவணங்கள்",
        "sub": "உங்கள் விண்ணப்பத்திற்குத் தேவையான ஆவணங்களை அனுப்புங்கள்.",
        "pickApplication": "விண்ணப்பம்",
        "noApplication": "இணைக்க இதுவரை விண்ணப்பம் எதுவும் இல்லை",
        "startFromMatches": "உங்கள் பொருத்தங்களைப் பாருங்கள்",
        "notDisplayed": "உள்ளடக்கம் இங்கே ஒருபோதும் காட்டப்படாது, சரிபார்ப்பு முடிவு மட்டுமே.",
        "statusPassed": "சரிபார்ப்பு முடிந்தது",
        "statusPending": "சரிபார்க்கப்படுகிறது",
        "statusWarning": "ஒருமுறை பாருங்கள்",
        "statusFailed": "ஏற்கப்படவில்லை",
        "statusMissing": "அனுப்பப்படவில்லை",
        "upload": "அனுப்பு",
        "update": "மாற்று",
    },
    "te": {
        "title": "నా పత్రాలు",
        "sub": "మీ దరఖాస్తుకు అవసరమైన పత్రాలను పంపండి.",
        "pickApplication": "దరఖాస్తు",
        "noApplication": "జోడించడానికి ఇంకా దరఖాస్తు ఏదీ లేదు",
        "startFromMatches": "మీ సరిపోలికలు చూడండి",
        "notDisplayed": "ఇక్కడ విషయం ఎప్పుడూ చూపబడదు, తనిఖీ ఫలితం మాత్రమే.",
        "statusPassed": "తనిఖీ పూర్తయింది",
        "statusPending": "తనిఖీ జరుగుతోంది",
        "statusWarning": "ఒకసారి చూడండి",
        "statusFailed": "ఆమోదించలేదు",
        "statusMissing": "పంపలేదు",
        "upload": "పంపండి",
        "update": "మార్చండి",
    },
}

# The page no longer picks a *scheme* to read a checklist against — it works off the
# citizen's own application, whose required documents the API already returns.
REMOVED = ["forScheme", "pickScheme", "why", "issuedBy", "validity", "digest"]


def main() -> None:
    for locale, block in DOCUMENTS.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        documents = data.setdefault("myDocuments", {})
        documents.update(block)
        dropped = [key for key in REMOVED if documents.pop(key, None) is not None]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} myDocuments, -{len(dropped)}")


if __name__ == "__main__":
    main()
