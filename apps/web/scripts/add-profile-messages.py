"""One-off: the profile page's six section cards, the DBT card, and the display settings.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

TWO STRINGS THAT ARE DELIBERATELY NOT WHAT THE DESIGN DROP SAYS.

`dbtStatus` is "Not checked", never "Not verified" and never "Verified". Nothing in this
product checks Aadhaar-DBT seeding — there is no NPCI mapper behind it — so a status in
any language that implies a lookup happened is inventing a government record. A citizen
wrongly told their account is seeded discovers it when a subsidy silently fails to arrive,
months later.

`dbtOpen` is "Check DBT status", not the drop's "One-tap DBT check". The button opens an
explainer that validates an IFSC on the device and hands the citizen the official NPCI
page; "one-tap check" promises a result the button cannot produce.

    python scripts/add-profile-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

PROFILE = {
    "en": {
        "completionLabel": "Profile completion",
        "edit": "Edit",
        "editSection": "Edit {section}",
        "sectionPersonal": "Personal information",
        "sectionSocial": "Social category",
        "sectionIncome": "Income",
        "sectionEnterprise": "Enterprise",
        "sectionNeed": "Financial need",
        "sectionLocation": "Location",
        "dbtEyebrow": "Direct benefit transfer",
        "dbtTitle": "Is your bank account Aadhaar-DBT linked?",
        "dbtBody": (
            "A subsidy or grant only lands in a DBT-seeded account. SamarthSetu cannot "
            "check your seeding status — only NPCI and your bank can — so this opens "
            "what to check and where."
        ),
        "dbtStatus": "Not checked",
        "dbtOpen": "Check DBT status",
        "incomeNote": "This is the figure the income ceiling is tested against — nothing else on this page is.",
    },
    "hi": {
        "completionLabel": "प्रोफ़ाइल पूर्णता",
        "edit": "बदलें",
        "editSection": "{section} बदलें",
        "sectionPersonal": "व्यक्तिगत जानकारी",
        "sectionSocial": "सामाजिक श्रेणी",
        "sectionIncome": "आय",
        "sectionEnterprise": "उद्यम",
        "sectionNeed": "पैसे की ज़रूरत",
        "sectionLocation": "स्थान",
        "dbtEyebrow": "सीधा लाभ हस्तांतरण",
        "dbtTitle": "क्या आपका बैंक खाता आधार-DBT से जुड़ा है?",
        "dbtBody": (
            "सब्सिडी या अनुदान केवल DBT-सीडेड खाते में ही आता है। SamarthSetu आपकी "
            "सीडिंग स्थिति नहीं जाँच सकता — यह केवल NPCI और आपका बैंक कर सकते हैं — "
            "इसलिए यहाँ बताया गया है कि क्या और कहाँ जाँचें।"
        ),
        "dbtStatus": "जाँचा नहीं गया",
        "dbtOpen": "DBT स्थिति देखें",
        "incomeNote": "योजनाओं की आय सीमा इसी आँकड़े पर जाँची जाती है — इस पेज पर और कुछ नहीं।",
    },
    "mr": {
        "completionLabel": "प्रोफाइल पूर्णता",
        "edit": "बदला",
        "editSection": "{section} बदला",
        "sectionPersonal": "वैयक्तिक माहिती",
        "sectionSocial": "सामाजिक प्रवर्ग",
        "sectionIncome": "उत्पन्न",
        "sectionEnterprise": "उद्योग",
        "sectionNeed": "पैशाची गरज",
        "sectionLocation": "ठिकाण",
        "dbtEyebrow": "थेट लाभ हस्तांतरण",
        "dbtTitle": "तुमचे बँक खाते आधार-DBT ला जोडलेले आहे का?",
        "dbtBody": (
            "अनुदान किंवा सबसिडी फक्त DBT-सीडेड खात्यातच जमा होते. SamarthSetu तुमची "
            "सीडिंग स्थिती तपासू शकत नाही — ते फक्त NPCI आणि तुमची बँक करू शकते — "
            "म्हणून इथे काय आणि कुठे तपासायचे ते दिले आहे."
        ),
        "dbtStatus": "तपासले नाही",
        "dbtOpen": "DBT स्थिती पाहा",
        "incomeNote": "योजनांची उत्पन्न मर्यादा याच आकड्यावर तपासली जाते — या पानावर दुसरे काहीही नाही.",
    },
    "bn": {
        "completionLabel": "প্রোফাইল সম্পূর্ণতা",
        "edit": "বদলান",
        "editSection": "{section} বদলান",
        "sectionPersonal": "ব্যক্তিগত তথ্য",
        "sectionSocial": "সামাজিক শ্রেণি",
        "sectionIncome": "আয়",
        "sectionEnterprise": "উদ্যোগ",
        "sectionNeed": "টাকার প্রয়োজন",
        "sectionLocation": "অবস্থান",
        "dbtEyebrow": "সরাসরি সুবিধা হস্তান্তর",
        "dbtTitle": "আপনার ব্যাঙ্ক অ্যাকাউন্ট কি আধার-DBT যুক্ত?",
        "dbtBody": (
            "ভর্তুকি বা অনুদান কেবল DBT-সিডেড অ্যাকাউন্টেই পৌঁছয়। SamarthSetu আপনার "
            "সিডিং অবস্থা যাচাই করতে পারে না — কেবল NPCI ও আপনার ব্যাঙ্ক পারে — তাই "
            "এখানে কী এবং কোথায় দেখতে হবে তা দেওয়া আছে।"
        ),
        "dbtStatus": "যাচাই করা হয়নি",
        "dbtOpen": "DBT অবস্থা দেখুন",
        "incomeNote": "প্রকল্পের আয়সীমা এই সংখ্যাটির উপরেই যাচাই হয় — এই পাতার আর কিছুর উপরে নয়।",
    },
    "ta": {
        "completionLabel": "சுயவிவரம் நிறைவு",
        "edit": "மாற்று",
        "editSection": "{section} மாற்று",
        "sectionPersonal": "தனிப்பட்ட தகவல்",
        "sectionSocial": "சமூகப் பிரிவு",
        "sectionIncome": "வருமானம்",
        "sectionEnterprise": "தொழில்",
        "sectionNeed": "பணத் தேவை",
        "sectionLocation": "இடம்",
        "dbtEyebrow": "நேரடி பயன் பரிமாற்றம்",
        "dbtTitle": "உங்கள் வங்கிக் கணக்கு ஆதார்-DBT இணைக்கப்பட்டதா?",
        "dbtBody": (
            "மானியமோ உதவித்தொகையோ DBT இணைக்கப்பட்ட கணக்கில் மட்டுமே வந்து சேரும். "
            "உங்கள் இணைப்பு நிலையை SamarthSetu சரிபார்க்க முடியாது — NPCI-யும் உங்கள் "
            "வங்கியும் மட்டுமே முடியும் — எனவே எதை எங்கே பார்ப்பது என்பது இங்கே."
        ),
        "dbtStatus": "சரிபார்க்கப்படவில்லை",
        "dbtOpen": "DBT நிலையைப் பாருங்கள்",
        "incomeNote": "திட்டங்களின் வருமான வரம்பு இந்த எண்ணின் மீதே சரிபார்க்கப்படுகிறது — இந்தப் பக்கத்தில் வேறு எதுவும் அல்ல.",
    },
    "te": {
        "completionLabel": "ప్రొఫైల్ పూర్తి",
        "edit": "మార్చండి",
        "editSection": "{section} మార్చండి",
        "sectionPersonal": "వ్యక్తిగత సమాచారం",
        "sectionSocial": "సామాజిక వర్గం",
        "sectionIncome": "ఆదాయం",
        "sectionEnterprise": "వ్యాపారం",
        "sectionNeed": "డబ్బు అవసరం",
        "sectionLocation": "ప్రదేశం",
        "dbtEyebrow": "ప్రత్యక్ష ప్రయోజన బదిలీ",
        "dbtTitle": "మీ బ్యాంకు ఖాతా ఆధార్-DBT తో అనుసంధానమైందా?",
        "dbtBody": (
            "సబ్సిడీ లేదా గ్రాంట్ DBT-సీడెడ్ ఖాతాలోకే చేరుతుంది. మీ సీడింగ్ స్థితిని "
            "SamarthSetu తనిఖీ చేయలేదు — NPCI మరియు మీ బ్యాంకు మాత్రమే చేయగలవు — "
            "కాబట్టి ఏమి, ఎక్కడ చూడాలో ఇక్కడ ఉంది."
        ),
        "dbtStatus": "తనిఖీ చేయలేదు",
        "dbtOpen": "DBT స్థితి చూడండి",
        "incomeNote": "పథకాల ఆదాయ పరిమితి ఈ సంఖ్యపైనే తనిఖీ చేయబడుతుంది — ఈ పేజీలో మరేదీ కాదు.",
    },
}

DISPLAY = {
    "en": {
        "title": "Accessibility and language",
        "sub": "These change every screen, and they stay on this device.",
        "language": "Language",
        "languageHint": "Six languages, each written in its own script.",
        "textSize": "Text size",
        "textSizeHint": "Larger text everywhere in the app.",
        "textSize_sm": "Smaller text",
        "textSize_base": "Normal text",
        "textSize_lg": "Larger text",
        "contrast": "High contrast",
        "contrastHint": "Stronger edges and darker labels, for daylight.",
        "contrastOn": "On",
        "contrastOff": "Off",
    },
    "hi": {
        "title": "सुगमता और भाषा",
        "sub": "ये हर स्क्रीन बदलते हैं और इसी डिवाइस पर रहते हैं।",
        "language": "भाषा",
        "languageHint": "छह भाषाएँ, हर एक अपनी लिपि में।",
        "textSize": "अक्षरों का आकार",
        "textSizeHint": "पूरे ऐप में बड़े अक्षर।",
        "textSize_sm": "छोटे अक्षर",
        "textSize_base": "सामान्य अक्षर",
        "textSize_lg": "बड़े अक्षर",
        "contrast": "अधिक कंट्रास्ट",
        "contrastHint": "गहरी लकीरें और गहरे लेबल, धूप में पढ़ने के लिए।",
        "contrastOn": "चालू",
        "contrastOff": "बंद",
    },
    "mr": {
        "title": "सुलभता आणि भाषा",
        "sub": "हे प्रत्येक स्क्रीन बदलतात आणि याच उपकरणावर राहतात.",
        "language": "भाषा",
        "languageHint": "सहा भाषा, प्रत्येक तिच्या स्वतःच्या लिपीत.",
        "textSize": "अक्षरांचा आकार",
        "textSizeHint": "संपूर्ण अ‍ॅपमध्ये मोठी अक्षरे.",
        "textSize_sm": "लहान अक्षरे",
        "textSize_base": "सामान्य अक्षरे",
        "textSize_lg": "मोठी अक्षरे",
        "contrast": "जास्त कॉन्ट्रास्ट",
        "contrastHint": "ठळक कडा आणि गडद लेबल, उन्हात वाचण्यासाठी.",
        "contrastOn": "चालू",
        "contrastOff": "बंद",
    },
    "bn": {
        "title": "সুগমতা ও ভাষা",
        "sub": "এগুলি প্রতিটি স্ক্রিন বদলায় এবং এই ডিভাইসেই থাকে।",
        "language": "ভাষা",
        "languageHint": "ছয়টি ভাষা, প্রতিটি নিজের লিপিতে লেখা।",
        "textSize": "লেখার আকার",
        "textSizeHint": "পুরো অ্যাপ জুড়ে বড় লেখা।",
        "textSize_sm": "ছোট লেখা",
        "textSize_base": "সাধারণ লেখা",
        "textSize_lg": "বড় লেখা",
        "contrast": "বেশি কনট্রাস্ট",
        "contrastHint": "গাঢ় সীমারেখা ও গাঢ় লেবেল, রোদে পড়ার জন্য।",
        "contrastOn": "চালু",
        "contrastOff": "বন্ধ",
    },
    "ta": {
        "title": "அணுகல் மற்றும் மொழி",
        "sub": "இவை ஒவ்வொரு திரையையும் மாற்றும், இந்தச் சாதனத்தில் மட்டும் இருக்கும்.",
        "language": "மொழி",
        "languageHint": "ஆறு மொழிகள், ஒவ்வொன்றும் அதன் சொந்த எழுத்தில்.",
        "textSize": "எழுத்து அளவு",
        "textSizeHint": "செயலி முழுவதும் பெரிய எழுத்து.",
        "textSize_sm": "சிறிய எழுத்து",
        "textSize_base": "வழக்கமான எழுத்து",
        "textSize_lg": "பெரிய எழுத்து",
        "contrast": "அதிக மாறுபாடு",
        "contrastHint": "தடிமனான விளிம்புகள், அடர்ந்த லேபிள்கள் — வெயிலில் படிக்க.",
        "contrastOn": "இயக்கத்தில்",
        "contrastOff": "நிறுத்தம்",
    },
    "te": {
        "title": "అందుబాటు మరియు భాష",
        "sub": "ఇవి ప్రతి స్క్రీన్‌ను మారుస్తాయి, ఈ పరికరంలోనే ఉంటాయి.",
        "language": "భాష",
        "languageHint": "ఆరు భాషలు, ప్రతి ఒక్కటి దాని సొంత లిపిలో.",
        "textSize": "అక్షరాల పరిమాణం",
        "textSizeHint": "యాప్ అంతటా పెద్ద అక్షరాలు.",
        "textSize_sm": "చిన్న అక్షరాలు",
        "textSize_base": "సాధారణ అక్షరాలు",
        "textSize_lg": "పెద్ద అక్షరాలు",
        "contrast": "అధిక కాంట్రాస్ట్",
        "contrastHint": "బలమైన అంచులు, ముదురు లేబుళ్లు — ఎండలో చదవడానికి.",
        "contrastOn": "ఆన్",
        "contrastOff": "ఆఫ్",
    },
}


# The two panels that used to close the page — the verbatim `engine_profile` dump and the
# consent note with Sign out — were cut from the profile on request. Sign out was never
# only here (`nav.signOut` in the sidebar is the control people actually use), and the
# transparency guarantee lives on in the match explanations, which name the rule ids that
# decided each verdict. These keys have no reader left.
REMOVED = [
    "engineTitle",
    "engineBody",
    "engineEmpty",
    "consentTitle",
    "consentBody",
    "signOut",
]

# `onboarding.engineNote` sent the citizen to "your profile page" to see which answers the
# rules read. With that panel gone the sentence was a promise about a screen that no longer
# shows it, so it now points at the match explanation, which does.
ENGINE_NOTE = {
    "en": (
        "Only the answers marked as read by the rules can change a verdict. "
        "Every match names the rules that decided it."
    ),
    "hi": (
        "केवल वही जवाब फ़ैसला बदल सकते हैं जिन्हें नियम पढ़ते हैं। "
        "हर मैच बताता है कि कौन-से नियमों ने फ़ैसला किया।"
    ),
    "mr": (
        "फक्त नियम वाचत असलेलीच उत्तरे निकाल बदलू शकतात. "
        "प्रत्येक जुळणी कोणत्या नियमांनी निर्णय घेतला ते सांगते."
    ),
    "bn": (
        "কেবল যে উত্তরগুলি নিয়ম পড়ে সেগুলিই সিদ্ধান্ত বদলাতে পারে। "
        "প্রতিটি মিল জানায় কোন নিয়ম সিদ্ধান্ত নিয়েছে।"
    ),
    "ta": (
        "விதிகள் படிக்கும் பதில்கள் மட்டுமே முடிவை மாற்ற முடியும். "
        "ஒவ்வொரு பொருத்தமும் எந்த விதிகள் முடிவு செய்தன என்பதைச் சொல்கிறது."
    ),
    "te": (
        "నియమాలు చదివే సమాధానాలు మాత్రమే నిర్ణయాన్ని మార్చగలవు. "
        "ప్రతి సరిపోలిక ఏ నియమాలు నిర్ణయించాయో చెబుతుంది."
    ),
}


def main() -> None:
    for locale in PROFILE:
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        profile = data.setdefault("profilePage", {})
        profile.update(PROFILE[locale])
        dropped = [key for key in REMOVED if profile.pop(key, None) is not None]

        data.setdefault("display", {}).update(DISPLAY[locale])
        data.setdefault("onboarding", {})["engineNote"] = ENGINE_NOTE[locale]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"{locale}: +{len(PROFILE[locale])} profilePage, -{len(dropped)}, "
            f"+{len(DISPLAY[locale])} display"
        )


if __name__ == "__main__":
    main()
