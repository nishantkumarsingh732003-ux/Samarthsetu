"""One-off: the eligibility rows, benefit cards, partner cards and FAQ on the scheme page.

Kept in the repo, like `add-scheme-detail-messages.py`, as the record of which strings
were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

Two groups need a reviewer rather than a glance.

`req*` are the requirement wordings on the eligibility rows. They are filled from a rule's
own published condition — see `lib/ruleRequirement`, which negates the *blocking*
expression to get the requirement — so "up to" must mean a ceiling and "over" must mean a
floor. A translation that blurs the two states the opposite of the rule.

`faq*` answer the three questions the design drop asked. The drop also supplied answers,
about collateral and processing times, that no source in this project supports; these say
only what the rule pack and the routing data actually establish, and say "not published"
where that is the truthful answer. A translation that adds a number, a timescale or a
guarantee is a bug — there is nothing behind it.

    python scripts/add-detail-tabs-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

DETAIL = {
    "en": {
        "tabFaq": "FAQ",
        "yourValue": "Your:",
        "requiredValue": "Req:",
        "notAnswered": "Not answered",
        "yes": "Yes",
        "no": "No",
        "noRunYet": "Finish your profile and the rules will check each of these against it.",
        "reqIs": "{value}",
        "reqIsNot": "Not {value}",
        "reqUpTo": "Up to {value}",
        "reqUnder": "Under {value}",
        "reqAtLeast": "{value} or more",
        "reqOver": "Over {value}",
        "criterion": {
            "socialCategory": "Social category",
            "familyIncome": "Family income",
            "projectCost": "Project cost",
            "enterpriseType": "Enterprise type",
            "coursePurpose": "Course purpose",
            "admission": "Admission",
            "fundingShare": "Funding share",
        },
        "benefitInterest": "Interest concession",
        "benefitFunding": "Share funded",
        "acceptingApplications": "Accepting applications",
        "partnersNone": "No authorised partner in your district is taking applications right now.",
        "partnersNeedDistrict": "Add your district to your profile and the authorised partners near you will appear here.",
        "faqCollateralQ": "Is collateral required?",
        "faqCollateralA": (
            "The published rules for this scheme say nothing about collateral, so this "
            "service cannot tell you. The Channel Partner that sanctions the loan sets "
            "that condition — ask the one you apply through."
        ),
        "faqTurnaroundQ": "How long does approval take?",
        "faqTurnaroundA": (
            "The {count} authorised partners near you report an average of {days} days "
            "from submission to a decision. That is their own reported figure, not a "
            "commitment."
        ),
        "faqTurnaroundUnknown": (
            "No authorised partner near you has reported a turnaround yet, so this "
            "service has no figure to give you."
        ),
        "faqMultipleQ": "Can I apply for multiple schemes?",
        "faqMultipleA": (
            "The rule engine checks every scheme separately, and your matches list each "
            "one you qualify for. Each application is decided by the partner that "
            "receives it. Where two schemes overlap, the rules point you at the one that "
            "fits — that is the “try instead” note on your matches."
        ),
    },
    "hi": {
        "tabFaq": "सामान्य प्रश्न",
        "yourValue": "आपका:",
        "requiredValue": "आवश्यक:",
        "notAnswered": "उत्तर नहीं दिया",
        "yes": "हाँ",
        "no": "नहीं",
        "noRunYet": "अपनी प्रोफ़ाइल पूरी करें, फिर नियम इनमें से हर एक की जाँच करेंगे।",
        "reqIs": "{value}",
        "reqIsNot": "{value} नहीं",
        "reqUpTo": "{value} तक",
        "reqUnder": "{value} से कम",
        "reqAtLeast": "{value} या अधिक",
        "reqOver": "{value} से अधिक",
        "criterion": {
            "socialCategory": "सामाजिक श्रेणी",
            "familyIncome": "पारिवारिक आय",
            "projectCost": "परियोजना लागत",
            "enterpriseType": "उद्यम प्रकार",
            "coursePurpose": "पाठ्यक्रम उद्देश्य",
            "admission": "प्रवेश",
            "fundingShare": "वित्तपोषण हिस्सा",
        },
        "benefitInterest": "ब्याज में रियायत",
        "benefitFunding": "कितना हिस्सा वित्तपोषित",
        "acceptingApplications": "आवेदन ले रहे हैं",
        "partnersNone": "आपके ज़िले में अभी कोई अधिकृत भागीदार आवेदन नहीं ले रहा।",
        "partnersNeedDistrict": "अपनी प्रोफ़ाइल में ज़िला जोड़ें, फिर आपके पास के अधिकृत भागीदार यहाँ दिखेंगे।",
        "faqCollateralQ": "क्या ज़मानत ज़रूरी है?",
        "faqCollateralA": (
            "इस योजना के प्रकाशित नियमों में ज़मानत के बारे में कुछ नहीं कहा गया, इसलिए "
            "यह सेवा आपको नहीं बता सकती। यह शर्त ऋण स्वीकृत करने वाला चैनल पार्टनर तय "
            "करता है — जिससे आवेदन करें, उससे पूछें।"
        ),
        "faqTurnaroundQ": "मंज़ूरी में कितना समय लगता है?",
        "faqTurnaroundA": (
            "आपके पास के {count} अधिकृत भागीदार आवेदन से निर्णय तक औसतन {days} दिन "
            "बताते हैं। यह उनका अपना बताया आँकड़ा है, कोई वादा नहीं।"
        ),
        "faqTurnaroundUnknown": (
            "आपके पास के किसी अधिकृत भागीदार ने अभी तक समय नहीं बताया है, इसलिए इस सेवा "
            "के पास कोई आँकड़ा नहीं है।"
        ),
        "faqMultipleQ": "क्या मैं कई योजनाओं के लिए आवेदन कर सकता हूँ?",
        "faqMultipleA": (
            "नियम इंजन हर योजना की अलग-अलग जाँच करता है, और आपके मैच में हर वह योजना है "
            "जिसके आप पात्र हैं। हर आवेदन का निर्णय उसे लेने वाला भागीदार करता है। जहाँ "
            "दो योजनाएँ मिलती-जुलती हैं, नियम आपको उपयुक्त वाली की ओर भेजते हैं — यही "
            "आपके मैच पर “इसके बजाय” वाली सूचना है।"
        ),
    },
    "mr": {
        "tabFaq": "नेहमीचे प्रश्न",
        "yourValue": "तुमचे:",
        "requiredValue": "आवश्यक:",
        "notAnswered": "उत्तर दिलेले नाही",
        "yes": "होय",
        "no": "नाही",
        "noRunYet": "तुमची प्रोफाइल पूर्ण करा, मग नियम यातील प्रत्येक गोष्ट तपासतील.",
        "reqIs": "{value}",
        "reqIsNot": "{value} नाही",
        "reqUpTo": "{value} पर्यंत",
        "reqUnder": "{value} पेक्षा कमी",
        "reqAtLeast": "{value} किंवा अधिक",
        "reqOver": "{value} पेक्षा जास्त",
        "criterion": {
            "socialCategory": "सामाजिक प्रवर्ग",
            "familyIncome": "कौटुंबिक उत्पन्न",
            "projectCost": "प्रकल्प खर्च",
            "enterpriseType": "उद्यम प्रकार",
            "coursePurpose": "अभ्यासक्रम उद्देश",
            "admission": "प्रवेश",
            "fundingShare": "वित्तपुरवठा हिस्सा",
        },
        "benefitInterest": "व्याजातील सवलत",
        "benefitFunding": "किती हिस्सा वित्तपुरवठा",
        "acceptingApplications": "अर्ज स्वीकारत आहेत",
        "partnersNone": "तुमच्या जिल्ह्यात सध्या कोणताही अधिकृत भागीदार अर्ज घेत नाही.",
        "partnersNeedDistrict": "तुमच्या प्रोफाइलमध्ये जिल्हा जोडा, मग जवळचे अधिकृत भागीदार इथे दिसतील.",
        "faqCollateralQ": "तारण आवश्यक आहे का?",
        "faqCollateralA": (
            "या योजनेच्या प्रकाशित नियमांत तारणाबद्दल काहीही म्हटलेले नाही, त्यामुळे ही "
            "सेवा सांगू शकत नाही. ही अट कर्ज मंजूर करणारा चॅनेल भागीदार ठरवतो — ज्याच्या "
            "मार्फत अर्ज कराल त्याला विचारा."
        ),
        "faqTurnaroundQ": "मंजुरीला किती वेळ लागतो?",
        "faqTurnaroundA": (
            "तुमच्याजवळचे {count} अधिकृत भागीदार अर्जापासून निर्णयापर्यंत सरासरी {days} "
            "दिवस सांगतात. हा त्यांचा स्वतःचा आकडा आहे, वचन नाही."
        ),
        "faqTurnaroundUnknown": (
            "तुमच्याजवळच्या कोणत्याही अधिकृत भागीदाराने अजून वेळ कळवलेला नाही, त्यामुळे "
            "या सेवेकडे आकडा नाही."
        ),
        "faqMultipleQ": "मी अनेक योजनांसाठी अर्ज करू शकतो का?",
        "faqMultipleA": (
            "नियम इंजिन प्रत्येक योजना स्वतंत्रपणे तपासते, आणि तुम्ही पात्र असलेली "
            "प्रत्येक योजना तुमच्या जुळणीत असते. प्रत्येक अर्जाचा निर्णय तो घेणारा "
            "भागीदार घेतो. दोन योजना जुळत असतील तिथे नियम तुम्हाला योग्य त्या योजनेकडे "
            "पाठवतात — तीच तुमच्या जुळणीवरील “त्याऐवजी” सूचना."
        ),
    },
    "bn": {
        "tabFaq": "সাধারণ প্রশ্ন",
        "yourValue": "আপনার:",
        "requiredValue": "প্রয়োজন:",
        "notAnswered": "উত্তর দেওয়া হয়নি",
        "yes": "হ্যাঁ",
        "no": "না",
        "noRunYet": "আপনার প্রোফাইল সম্পূর্ণ করুন, তারপর নিয়ম এগুলির প্রতিটি যাচাই করবে।",
        "reqIs": "{value}",
        "reqIsNot": "{value} নয়",
        "reqUpTo": "{value} পর্যন্ত",
        "reqUnder": "{value}-এর কম",
        "reqAtLeast": "{value} বা বেশি",
        "reqOver": "{value}-এর বেশি",
        "criterion": {
            "socialCategory": "সামাজিক শ্রেণি",
            "familyIncome": "পারিবারিক আয়",
            "projectCost": "প্রকল্প ব্যয়",
            "enterpriseType": "উদ্যোগের ধরন",
            "coursePurpose": "পাঠ্যক্রমের উদ্দেশ্য",
            "admission": "ভর্তি",
            "fundingShare": "অর্থায়নের অংশ",
        },
        "benefitInterest": "সুদে ছাড়",
        "benefitFunding": "কত অংশ অর্থায়িত",
        "acceptingApplications": "আবেদন নেওয়া হচ্ছে",
        "partnersNone": "আপনার জেলায় এই মুহূর্তে কোনও অনুমোদিত অংশীদার আবেদন নিচ্ছে না।",
        "partnersNeedDistrict": "প্রোফাইলে আপনার জেলা যোগ করুন, তারপর কাছাকাছি অনুমোদিত অংশীদাররা এখানে দেখা যাবে।",
        "faqCollateralQ": "জামানত কি প্রয়োজন?",
        "faqCollateralA": (
            "এই প্রকল্পের প্রকাশিত নিয়মে জামানত নিয়ে কিছু বলা নেই, তাই এই পরিষেবা "
            "আপনাকে বলতে পারে না। এই শর্ত ঠিক করেন ঋণ অনুমোদনকারী চ্যানেল পার্টনার — "
            "যাঁর মাধ্যমে আবেদন করবেন তাঁকে জিজ্ঞাসা করুন।"
        ),
        "faqTurnaroundQ": "অনুমোদনে কত সময় লাগে?",
        "faqTurnaroundA": (
            "আপনার কাছাকাছি {count} জন অনুমোদিত অংশীদার আবেদন থেকে সিদ্ধান্ত পর্যন্ত গড়ে "
            "{days} দিন জানিয়েছেন। এটি তাঁদের নিজেদের জানানো হিসাব, কোনও প্রতিশ্রুতি নয়।"
        ),
        "faqTurnaroundUnknown": (
            "আপনার কাছাকাছি কোনও অনুমোদিত অংশীদার এখনও সময় জানাননি, তাই এই পরিষেবার "
            "কাছে কোনও হিসাব নেই।"
        ),
        "faqMultipleQ": "আমি কি একাধিক প্রকল্পে আবেদন করতে পারি?",
        "faqMultipleA": (
            "নিয়ম ইঞ্জিন প্রতিটি প্রকল্প আলাদাভাবে যাচাই করে, এবং আপনি যোগ্য এমন "
            "প্রতিটি প্রকল্প আপনার মিলের তালিকায় থাকে। প্রতিটি আবেদনের সিদ্ধান্ত নেন "
            "যিনি সেটি পান সেই অংশীদার। দুটি প্রকল্প মিলে গেলে নিয়ম আপনাকে উপযুক্তটির "
            "দিকে পাঠায় — সেটিই আপনার মিলে “পরিবর্তে” লেখা নির্দেশ।"
        ),
    },
    "ta": {
        "tabFaq": "அடிக்கடி கேட்கும் கேள்விகள்",
        "yourValue": "உங்களுடையது:",
        "requiredValue": "தேவை:",
        "notAnswered": "பதிலளிக்கவில்லை",
        "yes": "ஆம்",
        "no": "இல்லை",
        "noRunYet": "உங்கள் சுயவிவரத்தை நிறைவு செய்யுங்கள், பிறகு விதிகள் இவை ஒவ்வொன்றையும் சரிபார்க்கும்.",
        "reqIs": "{value}",
        "reqIsNot": "{value} அல்ல",
        "reqUpTo": "{value} வரை",
        "reqUnder": "{value}-க்கும் குறைவு",
        "reqAtLeast": "{value} அல்லது அதற்கு மேல்",
        "reqOver": "{value}-க்கும் மேல்",
        "criterion": {
            "socialCategory": "சமூகப் பிரிவு",
            "familyIncome": "குடும்ப வருமானம்",
            "projectCost": "திட்டச் செலவு",
            "enterpriseType": "தொழில் வகை",
            "coursePurpose": "படிப்பு நோக்கம்",
            "admission": "சேர்க்கை",
            "fundingShare": "நிதிப் பங்கு",
        },
        "benefitInterest": "வட்டிச் சலுகை",
        "benefitFunding": "நிதியளிக்கும் பங்கு",
        "acceptingApplications": "விண்ணப்பங்கள் ஏற்கப்படுகின்றன",
        "partnersNone": "உங்கள் மாவட்டத்தில் தற்போது எந்த அங்கீகரிக்கப்பட்ட பங்குதாரரும் விண்ணப்பங்களை ஏற்கவில்லை.",
        "partnersNeedDistrict": "உங்கள் சுயவிவரத்தில் மாவட்டத்தைச் சேர்த்தால், அருகிலுள்ள அங்கீகரிக்கப்பட்ட பங்குதாரர்கள் இங்கே தோன்றுவார்கள்.",
        "faqCollateralQ": "பிணையம் தேவையா?",
        "faqCollateralA": (
            "இத்திட்டத்தின் வெளியிடப்பட்ட விதிகளில் பிணையம் பற்றி எதுவும் இல்லை, எனவே "
            "இச்சேவை உங்களுக்குச் சொல்ல முடியாது. கடனை ஒப்புதல் அளிக்கும் சேனல் "
            "பங்குதாரரே அந்த நிபந்தனையை நிர்ணயிக்கிறார் — நீங்கள் விண்ணப்பிக்கும் "
            "பங்குதாரரிடம் கேளுங்கள்."
        ),
        "faqTurnaroundQ": "ஒப்புதலுக்கு எவ்வளவு காலம் ஆகும்?",
        "faqTurnaroundA": (
            "உங்கள் அருகிலுள்ள {count} அங்கீகரிக்கப்பட்ட பங்குதாரர்கள் விண்ணப்பத்திலிருந்து "
            "முடிவு வரை சராசரியாக {days} நாட்கள் என்கிறார்கள். இது அவர்களே தெரிவித்த "
            "எண்ணிக்கை, உறுதிமொழி அல்ல."
        ),
        "faqTurnaroundUnknown": (
            "உங்கள் அருகிலுள்ள எந்தப் பங்குதாரரும் இதுவரை காலத்தைத் தெரிவிக்கவில்லை, "
            "எனவே இச்சேவையிடம் எண்ணிக்கை இல்லை."
        ),
        "faqMultipleQ": "பல திட்டங்களுக்கு விண்ணப்பிக்கலாமா?",
        "faqMultipleA": (
            "விதி இயந்திரம் ஒவ்வொரு திட்டத்தையும் தனித்தனியாகச் சரிபார்க்கிறது, நீங்கள் "
            "தகுதி பெறும் ஒவ்வொன்றும் உங்கள் பொருத்தப் பட்டியலில் இருக்கும். ஒவ்வொரு "
            "விண்ணப்பத்தையும் அதைப் பெறும் பங்குதாரரே முடிவு செய்கிறார். இரு திட்டங்கள் "
            "ஒன்றுபடும் இடத்தில், பொருந்தும் ஒன்றை விதிகள் சுட்டிக்காட்டுகின்றன — அதுவே "
            "உங்கள் பொருத்தத்தில் உள்ள “இதற்குப் பதிலாக” குறிப்பு."
        ),
    },
    "te": {
        "tabFaq": "తరచుగా అడిగే ప్రశ్నలు",
        "yourValue": "మీది:",
        "requiredValue": "అవసరం:",
        "notAnswered": "సమాధానం ఇవ్వలేదు",
        "yes": "అవును",
        "no": "కాదు",
        "noRunYet": "మీ ప్రొఫైల్ పూర్తి చేయండి, తర్వాత నిబంధనలు వీటిలో ప్రతి ఒక్కటి తనిఖీ చేస్తాయి.",
        "reqIs": "{value}",
        "reqIsNot": "{value} కాదు",
        "reqUpTo": "{value} వరకు",
        "reqUnder": "{value} కంటే తక్కువ",
        "reqAtLeast": "{value} లేదా అంతకంటే ఎక్కువ",
        "reqOver": "{value} కంటే ఎక్కువ",
        "criterion": {
            "socialCategory": "సామాజిక వర్గం",
            "familyIncome": "కుటుంబ ఆదాయం",
            "projectCost": "ప్రాజెక్ట్ వ్యయం",
            "enterpriseType": "సంస్థ రకం",
            "coursePurpose": "కోర్సు ఉద్దేశం",
            "admission": "ప్రవేశం",
            "fundingShare": "ఆర్థిక వాటా",
        },
        "benefitInterest": "వడ్డీ రాయితీ",
        "benefitFunding": "ఆర్థిక సహాయ వాటా",
        "acceptingApplications": "దరఖాస్తులు స్వీకరిస్తున్నారు",
        "partnersNone": "మీ జిల్లాలో ప్రస్తుతం ఏ అధీకృత భాగస్వామి దరఖాస్తులు తీసుకోవడం లేదు.",
        "partnersNeedDistrict": "మీ ప్రొఫైల్‌లో జిల్లా జోడించండి, అప్పుడు దగ్గరలోని అధీకృత భాగస్వాములు ఇక్కడ కనిపిస్తారు.",
        "faqCollateralQ": "పూచీకత్తు అవసరమా?",
        "faqCollateralA": (
            "ఈ పథకం ప్రచురించిన నిబంధనల్లో పూచీకత్తు గురించి ఏమీ లేదు, కాబట్టి ఈ సేవ "
            "మీకు చెప్పలేదు. రుణం మంజూరు చేసే ఛానెల్ భాగస్వామే ఆ షరతును నిర్ణయిస్తారు — "
            "మీరు దరఖాస్తు చేసే భాగస్వామిని అడగండి."
        ),
        "faqTurnaroundQ": "ఆమోదానికి ఎంత సమయం పడుతుంది?",
        "faqTurnaroundA": (
            "మీ దగ్గరలోని {count} అధీకృత భాగస్వాములు దరఖాస్తు నుండి నిర్ణయం వరకు సగటున "
            "{days} రోజులు అని తెలిపారు. ఇది వారే తెలిపిన సంఖ్య, హామీ కాదు."
        ),
        "faqTurnaroundUnknown": (
            "మీ దగ్గరలోని ఏ అధీకృత భాగస్వామి ఇంకా సమయాన్ని తెలపలేదు, కాబట్టి ఈ సేవ వద్ద "
            "సంఖ్య లేదు."
        ),
        "faqMultipleQ": "నేను అనేక పథకాలకు దరఖాస్తు చేయవచ్చా?",
        "faqMultipleA": (
            "నిబంధనల ఇంజిన్ ప్రతి పథకాన్ని విడిగా తనిఖీ చేస్తుంది, మీరు అర్హులైన ప్రతి "
            "పథకం మీ సరిపోలికల్లో ఉంటుంది. ప్రతి దరఖాస్తుపై నిర్ణయం దాన్ని అందుకున్న "
            "భాగస్వామిదే. రెండు పథకాలు కలిసే చోట, సరిపోయే దానివైపు నిబంధనలు మిమ్మల్ని "
            "మళ్లిస్తాయి — అదే మీ సరిపోలికలపై “దీనికి బదులు” సూచన."
        ),
    },
}

# The drop labels the secondary action on a match card "View Details", not "Details".
MATCH_DETAILS = {
    "en": "View Details",
    "hi": "विवरण देखें",
    "mr": "तपशील पाहा",
    "bn": "বিবরণ দেখুন",
    "ta": "விவரங்களைப் பார்க்க",
    "te": "వివరాలు చూడండి",
}


def main() -> None:
    for locale, block in DETAIL.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        detail = data.setdefault("schemeDetail", {})
        criterion = {**detail.get("criterion", {}), **block["criterion"]}
        detail.update({**block, "criterion": criterion})

        data.setdefault("matches", {})["details"] = MATCH_DETAILS[locale]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block) - 1} schemeDetail, +{len(criterion)} criterion")


if __name__ == "__main__":
    main()
