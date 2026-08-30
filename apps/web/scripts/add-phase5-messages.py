"""One-off: add the Phase 5 message keys to all six catalogues.

Kept in the repo rather than run and deleted, because it is the record of exactly which
strings were added at once and in which languages — useful when a reviewer sits down to
check the four draft locales (OPEN_ITEMS OI-4).

    python scripts/add-phase5-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

APPLY = {
    "en": {
        "heading": "Apply through this office",
        "notALoan": (
            "SETU does not give loans. This sends your application to the office you "
            "chose, and that office decides."
        ),
        "goingTo": "Application goes to",
        "aboutYou": "About you",
        "allOptional": "All of this is optional. You get a reference number either way.",
        "yourName": "Your name",
        "yourPhone": "Phone number",
        "phoneLast4": "We keep only the last 4 digits.",
        "yourId": "Aadhaar number",
        "idMasked": (
            "We keep only the last 4 digits. The full number is never stored, and any "
            "photo you send has it blacked out."
        ),
        "consentText": (
            "I agree that SETU may store these details in order to send my application "
            "to the office I chose."
        ),
        "submit": "Send my application",
        "afterSubmit": "You will get a reference number. Keep it — the office will ask for it.",
    },
    "hi": {
        "heading": "इस कार्यालय के माध्यम से आवेदन करें",
        "notALoan": (
            "SETU ऋण नहीं देता। यह आपका आवेदन उस कार्यालय को भेजता है जिसे आपने चुना है, "
            "और निर्णय वही कार्यालय लेता है।"
        ),
        "goingTo": "आवेदन यहाँ जाएगा",
        "aboutYou": "आपके बारे में",
        "allOptional": "यह सब वैकल्पिक है। संदर्भ संख्या आपको हर हाल में मिलेगी।",
        "yourName": "आपका नाम",
        "yourPhone": "फ़ोन नंबर",
        "phoneLast4": "हम केवल अंतिम 4 अंक रखते हैं।",
        "yourId": "आधार संख्या",
        "idMasked": (
            "हम केवल अंतिम 4 अंक रखते हैं। पूरी संख्या कभी संग्रहीत नहीं होती, और आपकी "
            "भेजी गई तस्वीर में उसे काला कर दिया जाता है।"
        ),
        "consentText": (
            "मैं सहमत हूँ कि SETU मेरा आवेदन चुने गए कार्यालय को भेजने के लिए ये विवरण "
            "संग्रहीत कर सकता है।"
        ),
        "submit": "मेरा आवेदन भेजें",
        "afterSubmit": "आपको एक संदर्भ संख्या मिलेगी। उसे सँभालकर रखें — कार्यालय वही माँगेगा।",
    },
    "mr": {
        "heading": "या कार्यालयामार्फत अर्ज करा",
        "notALoan": (
            "SETU कर्ज देत नाही. हे तुमचा अर्ज तुम्ही निवडलेल्या कार्यालयाकडे पाठवते, "
            "आणि निर्णय तेच कार्यालय घेते."
        ),
        "goingTo": "अर्ज इथे जाईल",
        "aboutYou": "तुमच्याबद्दल",
        "allOptional": "हे सर्व ऐच्छिक आहे. संदर्भ क्रमांक तुम्हाला कोणत्याही परिस्थितीत मिळेल.",
        "yourName": "तुमचे नाव",
        "yourPhone": "फोन नंबर",
        "phoneLast4": "आम्ही फक्त शेवटचे 4 अंक ठेवतो.",
        "yourId": "आधार क्रमांक",
        "idMasked": (
            "आम्ही फक्त शेवटचे 4 अंक ठेवतो. पूर्ण क्रमांक कधीही साठवला जात नाही, आणि "
            "तुम्ही पाठवलेल्या फोटोत तो काळा केला जातो."
        ),
        "consentText": (
            "मी सहमत आहे की माझा अर्ज निवडलेल्या कार्यालयाकडे पाठवण्यासाठी SETU हे तपशील "
            "साठवू शकते."
        ),
        "submit": "माझा अर्ज पाठवा",
        "afterSubmit": "तुम्हाला संदर्भ क्रमांक मिळेल. तो जपून ठेवा — कार्यालय तोच विचारेल.",
    },
    "bn": {
        "heading": "এই অফিসের মাধ্যমে আবেদন করুন",
        "notALoan": (
            "SETU ঋণ দেয় না। এটি আপনার আবেদন আপনার বেছে নেওয়া অফিসে পাঠায়, এবং সিদ্ধান্ত "
            "সেই অফিসই নেয়।"
        ),
        "goingTo": "আবেদন যাবে",
        "aboutYou": "আপনার সম্পর্কে",
        "allOptional": "এসবই ঐচ্ছিক। রেফারেন্স নম্বর আপনি যেভাবেই হোক পাবেন।",
        "yourName": "আপনার নাম",
        "yourPhone": "ফোন নম্বর",
        "phoneLast4": "আমরা শুধু শেষ ৪টি সংখ্যা রাখি।",
        "yourId": "আধার নম্বর",
        "idMasked": (
            "আমরা শুধু শেষ ৪টি সংখ্যা রাখি। পুরো নম্বর কখনও সংরক্ষণ করা হয় না, এবং আপনার "
            "পাঠানো ছবিতে সেটি কালো করে দেওয়া হয়।"
        ),
        "consentText": (
            "আমি সম্মত যে আমার আবেদন বেছে নেওয়া অফিসে পাঠানোর জন্য SETU এই তথ্য সংরক্ষণ "
            "করতে পারে।"
        ),
        "submit": "আমার আবেদন পাঠান",
        "afterSubmit": "আপনি একটি রেফারেন্স নম্বর পাবেন। সেটি রেখে দিন — অফিস সেটিই চাইবে।",
    },
    "ta": {
        "heading": "இந்த அலுவலகம் வழியாக விண்ணப்பியுங்கள்",
        "notALoan": (
            "SETU கடன் வழங்குவதில்லை. இது உங்கள் விண்ணப்பத்தை நீங்கள் தேர்ந்தெடுத்த "
            "அலுவலகத்திற்கு அனுப்புகிறது; முடிவை அந்த அலுவலகமே எடுக்கும்."
        ),
        "goingTo": "விண்ணப்பம் செல்லும் இடம்",
        "aboutYou": "உங்களைப் பற்றி",
        "allOptional": "இவை அனைத்தும் விருப்பத்தேர்வு. குறிப்பு எண் எப்படியும் கிடைக்கும்.",
        "yourName": "உங்கள் பெயர்",
        "yourPhone": "தொலைபேசி எண்",
        "phoneLast4": "கடைசி 4 இலக்கங்களை மட்டுமே வைத்திருக்கிறோம்.",
        "yourId": "ஆதார் எண்",
        "idMasked": (
            "கடைசி 4 இலக்கங்களை மட்டுமே வைத்திருக்கிறோம். முழு எண் ஒருபோதும் "
            "சேமிக்கப்படுவதில்லை; நீங்கள் அனுப்பும் படத்தில் அது கருப்பாக மறைக்கப்படுகிறது."
        ),
        "consentText": (
            "நான் தேர்ந்தெடுத்த அலுவலகத்திற்கு என் விண்ணப்பத்தை அனுப்ப SETU இந்த விவரங்களைச் "
            "சேமிக்கலாம் என ஒப்புக்கொள்கிறேன்."
        ),
        "submit": "என் விண்ணப்பத்தை அனுப்பு",
        "afterSubmit": (
            "உங்களுக்கு ஒரு குறிப்பு எண் கிடைக்கும். அதைப் பத்திரமாக வைத்திருங்கள் — "
            "அலுவலகம் அதைத்தான் கேட்கும்."
        ),
    },
    "te": {
        "heading": "ఈ కార్యాలయం ద్వారా దరఖాస్తు చేయండి",
        "notALoan": (
            "SETU రుణాలు ఇవ్వదు. ఇది మీ దరఖాస్తును మీరు ఎంచుకున్న కార్యాలయానికి పంపుతుంది, "
            "నిర్ణయం ఆ కార్యాలయమే తీసుకుంటుంది."
        ),
        "goingTo": "దరఖాస్తు వెళ్ళేది",
        "aboutYou": "మీ గురించి",
        "allOptional": "ఇవన్నీ ఐచ్ఛికం. రిఫరెన్స్ నంబర్ మీకు ఎలాగైనా వస్తుంది.",
        "yourName": "మీ పేరు",
        "yourPhone": "ఫోన్ నంబర్",
        "phoneLast4": "మేము చివరి 4 అంకెలను మాత్రమే ఉంచుతాము.",
        "yourId": "ఆధార్ నంబర్",
        "idMasked": (
            "మేము చివరి 4 అంకెలను మాత్రమే ఉంచుతాము. పూర్తి నంబర్ ఎప్పుడూ నిల్వ చేయబడదు, "
            "మీరు పంపే ఫోటోలో అది నల్లగా కప్పబడుతుంది."
        ),
        "consentText": (
            "నేను ఎంచుకున్న కార్యాలయానికి నా దరఖాస్తును పంపడానికి SETU ఈ వివరాలను నిల్వ "
            "చేయవచ్చని నేను అంగీకరిస్తున్నాను."
        ),
        "submit": "నా దరఖాస్తును పంపు",
        "afterSubmit": (
            "మీకు ఒక రిఫరెన్స్ నంబర్ వస్తుంది. దాన్ని జాగ్రత్తగా ఉంచుకోండి — కార్యాలయం "
            "దాన్నే అడుగుతుంది."
        ),
    },
}

DOCS = {
    "en": {
        "whatToBring": "What to bring",
        "yourDocuments": "Your documents",
        "outstanding": "{count} still needed",
        "allUploaded": "You have added everything on the list.",
        "takePhoto": "Take a photo",
        "replacePhoto": "Take a new photo",
        "uploading": "Sending…",
        "uploaded": "Added",
        "privacyNote": (
            "Any ID number in a photo is blacked out before the photo is saved. We keep "
            "only the last 4 digits."
        ),
        "idMaskedConfirmed": "The ID number in this photo has been blacked out.",
        "validityPractice": "Most offices ask for one issued within {months} months.",
        "validityRule": "Must be issued within {months} months.",
        "checklistUnverified": (
            "This list is our reading of what offices usually ask for. Confirm it at the "
            "branch."
        ),
    },
    "hi": {
        "whatToBring": "क्या साथ ले जाना है",
        "yourDocuments": "आपके दस्तावेज़",
        "outstanding": "{count} अभी बाकी हैं",
        "allUploaded": "सूची की सभी चीज़ें आपने जोड़ दी हैं।",
        "takePhoto": "फ़ोटो लें",
        "replacePhoto": "नई फ़ोटो लें",
        "uploading": "भेजा जा रहा है…",
        "uploaded": "जोड़ा गया",
        "privacyNote": (
            "फ़ोटो सहेजने से पहले उसमें मौजूद कोई भी पहचान संख्या काली कर दी जाती है। "
            "हम केवल अंतिम 4 अंक रखते हैं।"
        ),
        "idMaskedConfirmed": "इस फ़ोटो की पहचान संख्या काली कर दी गई है।",
        "validityPractice": "अधिकतर कार्यालय {months} महीनों के भीतर जारी हुआ दस्तावेज़ माँगते हैं।",
        "validityRule": "{months} महीनों के भीतर जारी होना आवश्यक है।",
        "checklistUnverified": (
            "यह सूची हमारी समझ के अनुसार है कि कार्यालय आमतौर पर क्या माँगते हैं। शाखा में "
            "इसकी पुष्टि कर लें।"
        ),
    },
    "mr": {
        "whatToBring": "काय सोबत न्यायचे",
        "yourDocuments": "तुमची कागदपत्रे",
        "outstanding": "{count} अजून बाकी आहेत",
        "allUploaded": "यादीतील सर्व गोष्टी तुम्ही जोडल्या आहेत.",
        "takePhoto": "फोटो काढा",
        "replacePhoto": "नवा फोटो काढा",
        "uploading": "पाठवत आहे…",
        "uploaded": "जोडले",
        "privacyNote": (
            "फोटो जतन करण्यापूर्वी त्यातील कोणताही ओळख क्रमांक काळा केला जातो. आम्ही फक्त "
            "शेवटचे 4 अंक ठेवतो."
        ),
        "idMaskedConfirmed": "या फोटोतील ओळख क्रमांक काळा केला आहे.",
        "validityPractice": "बहुतेक कार्यालये {months} महिन्यांत दिलेले कागदपत्र मागतात.",
        "validityRule": "{months} महिन्यांच्या आत दिलेले असणे आवश्यक आहे.",
        "checklistUnverified": (
            "कार्यालये सहसा काय मागतात याबद्दलची ही आमची समज आहे. शाखेत याची खात्री करा."
        ),
    },
    "bn": {
        "whatToBring": "কী সঙ্গে নেবেন",
        "yourDocuments": "আপনার নথিপত্র",
        "outstanding": "{count}টি এখনও বাকি",
        "allUploaded": "তালিকার সবকিছুই আপনি যোগ করেছেন।",
        "takePhoto": "ছবি তুলুন",
        "replacePhoto": "নতুন ছবি তুলুন",
        "uploading": "পাঠানো হচ্ছে…",
        "uploaded": "যোগ হয়েছে",
        "privacyNote": (
            "ছবি সংরক্ষণের আগে তাতে থাকা যেকোনো পরিচয় নম্বর কালো করে দেওয়া হয়। আমরা শুধু "
            "শেষ ৪টি সংখ্যা রাখি।"
        ),
        "idMaskedConfirmed": "এই ছবির পরিচয় নম্বর কালো করে দেওয়া হয়েছে।",
        "validityPractice": "বেশিরভাগ অফিস {months} মাসের মধ্যে ইস্যু করা নথি চায়।",
        "validityRule": "{months} মাসের মধ্যে ইস্যু হওয়া আবশ্যক।",
        "checklistUnverified": (
            "অফিসগুলি সাধারণত কী চায়, এটি সে বিষয়ে আমাদের বোঝাপড়া। শাখায় নিশ্চিত করে নিন।"
        ),
    },
    "ta": {
        "whatToBring": "எடுத்துச் செல்ல வேண்டியவை",
        "yourDocuments": "உங்கள் ஆவணங்கள்",
        "outstanding": "{count} இன்னும் தேவை",
        "allUploaded": "பட்டியலில் உள்ள அனைத்தையும் நீங்கள் சேர்த்துவிட்டீர்கள்.",
        "takePhoto": "படம் எடுங்கள்",
        "replacePhoto": "புதிய படம் எடுங்கள்",
        "uploading": "அனுப்புகிறது…",
        "uploaded": "சேர்க்கப்பட்டது",
        "privacyNote": (
            "படம் சேமிக்கப்படுவதற்கு முன் அதில் உள்ள எந்த அடையாள எண்ணும் கருப்பாக "
            "மறைக்கப்படுகிறது. கடைசி 4 இலக்கங்களை மட்டுமே வைத்திருக்கிறோம்."
        ),
        "idMaskedConfirmed": "இந்தப் படத்தில் உள்ள அடையாள எண் கருப்பாக மறைக்கப்பட்டுள்ளது.",
        "validityPractice": (
            "பெரும்பாலான அலுவலகங்கள் {months} மாதங்களுக்குள் வழங்கப்பட்ட ஆவணத்தைக் கேட்கின்றன."
        ),
        "validityRule": "{months} மாதங்களுக்குள் வழங்கப்பட்டிருக்க வேண்டும்.",
        "checklistUnverified": (
            "அலுவலகங்கள் பொதுவாக என்ன கேட்கின்றன என்பதைப் பற்றிய எங்கள் புரிதல் இது. "
            "கிளையில் உறுதிசெய்யுங்கள்."
        ),
    },
    "te": {
        "whatToBring": "ఏమి తీసుకెళ్ళాలి",
        "yourDocuments": "మీ పత్రాలు",
        "outstanding": "{count} ఇంకా కావాలి",
        "allUploaded": "జాబితాలోని అన్నింటినీ మీరు జోడించారు.",
        "takePhoto": "ఫోటో తీయండి",
        "replacePhoto": "కొత్త ఫోటో తీయండి",
        "uploading": "పంపుతోంది…",
        "uploaded": "జోడించబడింది",
        "privacyNote": (
            "ఫోటో సేవ్ చేయడానికి ముందు అందులోని ఏ గుర్తింపు నంబర్ అయినా నల్లగా కప్పబడుతుంది. "
            "మేము చివరి 4 అంకెలను మాత్రమే ఉంచుతాము."
        ),
        "idMaskedConfirmed": "ఈ ఫోటోలోని గుర్తింపు నంబర్ నల్లగా కప్పబడింది.",
        "validityPractice": "చాలా కార్యాలయాలు {months} నెలల్లో జారీ చేసిన పత్రాన్ని అడుగుతాయి.",
        "validityRule": "{months} నెలల్లో జారీ చేసి ఉండాలి.",
        "checklistUnverified": (
            "కార్యాలయాలు సాధారణంగా ఏమి అడుగుతాయో అనే మా అవగాహన ఇది. శాఖలో నిర్ధారించుకోండి."
        ),
    },
}

# One addition to the existing `track` block: the same disclaimer results carries, because
# a citizen looking at a status ladder is exactly who might read "Approved" as ours.
TRACK_EXTRA = {
    "en": {"indicativeOnly": "SETU does not approve loans. The office decides."},
    "hi": {"indicativeOnly": "SETU ऋण स्वीकृत नहीं करता। निर्णय कार्यालय लेता है।"},
    "mr": {"indicativeOnly": "SETU कर्ज मंजूर करत नाही. निर्णय कार्यालय घेते."},
    "bn": {"indicativeOnly": "SETU ঋণ অনুমোদন করে না। সিদ্ধান্ত অফিস নেয়।"},
    "ta": {"indicativeOnly": "SETU கடனை அனுமதிப்பதில்லை. முடிவை அலுவலகம் எடுக்கும்."},
    "te": {"indicativeOnly": "SETU రుణాలను ఆమోదించదు. నిర్ణయం కార్యాలయం తీసుకుంటుంది."},
}

PARTNERS_EXTRA = {
    "en": {"applyHere": "Apply through this office"},
    "hi": {"applyHere": "इस कार्यालय के माध्यम से आवेदन करें"},
    "mr": {"applyHere": "या कार्यालयामार्फत अर्ज करा"},
    "bn": {"applyHere": "এই অফিসের মাধ্যমে আবেদন করুন"},
    "ta": {"applyHere": "இந்த அலுவலகம் வழியாக விண்ணப்பியுங்கள்"},
    "te": {"applyHere": "ఈ కార్యాలయం ద్వారా దరఖాస్తు చేయండి"},
}


def main() -> None:
    for locale in ("en", "hi", "mr", "bn", "ta", "te"):
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["apply"] = {**data.get("apply", {}), **APPLY[locale]}
        data["docs"] = {**data.get("docs", {}), **DOCS[locale]}
        data["track"] = {**data.get("track", {}), **TRACK_EXTRA[locale]}
        data["partners"] = {**data.get("partners", {}), **PARTNERS_EXTRA[locale]}
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: apply+docs+track+partners keys written")


if __name__ == "__main__":
    main()
