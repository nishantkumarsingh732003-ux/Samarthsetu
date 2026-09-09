"""One-off: the application draft, the WhatsApp share and the DBT helper, in six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

Two blocks need a reviewer rather than a glance.

`dbtCheck.cannotCheck` must keep saying that this service cannot check DBT seeding. There
is no NPCI mapper behind this product. A translation that reads as "we have checked" would
tell a citizen their subsidy will arrive when nobody has verified that it will, and they
would find out months later when it did not.

`applicationDraft.sheetDisclaimer` and `summaryHeading` travel: the first is printed on a
document carrying a ministry name, the second is pasted into WhatsApp and forwarded. Both
have to keep saying this is a draft the citizen prepared and not an application anyone has
accepted.

    python scripts/add-application-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

DRAFT = {
    "en": {
        "heroTitle": "Your application is almost ready",
        "heroSub": "Review and submit for the best-matched scheme.",
        "eyebrow": "Pre-filled application draft",
        "noSchemeYet": "No scheme matched yet",
        "profileMatch": "{pct}% profile match",
        "applicant": "Applicant",
        "category": "Category",
        "income": "Annual income",
        "enterprise": "Enterprise",
        "enterpriseType": "Enterprise type",
        "projectCost": "Project cost",
        "loanRequired": "Loan required",
        "location": "Location",
        "preferredScheme": "Preferred scheme",
        "preferredPartner": "Preferred partner",
        "dbtCheck": "Aadhaar-DBT check",
        "shareWhatsApp": "Share on WhatsApp",
        "downloadPdf": "Download PDF",
        "submit": "Submit application",
        "done": "Complete",
        "percentDone": "{pct}% answered",
        "noVerdictYet": "Not checked yet",
        "afterSubmitting": "Listed after you submit",
        "outstanding": "{count} outstanding",
        "notReady": "Finish the steps above",
        "step": {
            "profile": "Profile",
            "eligibility": "Eligibility",
            "documents": "Documents",
            "draft": "Application draft",
        },
        "sectionApplicant": "Applicant details",
        "sectionEnterprise": "Enterprise",
        "sectionFinancing": "Financing",
        "sheetTitle": "Application draft · Prepared for review",
        "sheetOrgLine": "MoSJE · Government of India · Draft, not an application",
        "sheetReference": "Application ID: {reference}",
        "sheetScheme": "Scheme: {scheme}",
        "sheetDisclaimer": (
            "Prepared by the applicant for review. This is not a submitted application "
            "and SamarthSetu does not approve loans — the Channel Partner decides."
        ),
        "summaryHeading": "SamarthSetu · Application summary",
        "generatedAt": "Generated {when}",
    },
    "hi": {
        "heroTitle": "आपका आवेदन लगभग तैयार है",
        "heroSub": "सबसे उपयुक्त योजना के लिए जाँचें और जमा करें।",
        "eyebrow": "पहले से भरा आवेदन प्रारूप",
        "noSchemeYet": "अभी कोई योजना नहीं मिली",
        "profileMatch": "{pct}% प्रोफ़ाइल मिलान",
        "applicant": "आवेदक",
        "category": "श्रेणी",
        "income": "वार्षिक आय",
        "enterprise": "उद्यम",
        "enterpriseType": "उद्यम का प्रकार",
        "projectCost": "परियोजना लागत",
        "loanRequired": "आवश्यक ऋण",
        "location": "स्थान",
        "preferredScheme": "पसंदीदा योजना",
        "preferredPartner": "पसंदीदा भागीदार",
        "dbtCheck": "आधार-डीबीटी जाँच",
        "shareWhatsApp": "व्हाट्सऐप पर भेजें",
        "downloadPdf": "पीडीएफ़ डाउनलोड करें",
        "submit": "आवेदन जमा करें",
        "done": "पूरा",
        "percentDone": "{pct}% भरा",
        "noVerdictYet": "अभी जाँचा नहीं गया",
        "afterSubmitting": "जमा करने के बाद दिखेगा",
        "outstanding": "{count} बाकी",
        "notReady": "ऊपर के चरण पूरे करें",
        "step": {
            "profile": "प्रोफ़ाइल",
            "eligibility": "पात्रता",
            "documents": "दस्तावेज़",
            "draft": "आवेदन प्रारूप",
        },
        "sectionApplicant": "आवेदक का विवरण",
        "sectionEnterprise": "उद्यम",
        "sectionFinancing": "वित्त",
        "sheetTitle": "आवेदन प्रारूप · जाँच के लिए तैयार",
        "sheetOrgLine": "सामाजिक न्याय मंत्रालय · भारत सरकार · प्रारूप, आवेदन नहीं",
        "sheetReference": "आवेदन आईडी: {reference}",
        "sheetScheme": "योजना: {scheme}",
        "sheetDisclaimer": (
            "आवेदक द्वारा जाँच के लिए तैयार किया गया। यह जमा किया गया आवेदन नहीं है और "
            "SamarthSetu ऋण स्वीकृत नहीं करता — निर्णय चैनल पार्टनर लेता है।"
        ),
        "summaryHeading": "SamarthSetu · आवेदन सारांश",
        "generatedAt": "{when} को तैयार",
    },
    "mr": {
        "heroTitle": "तुमचा अर्ज जवळपास तयार आहे",
        "heroSub": "सर्वात योग्य योजनेसाठी तपासा आणि सादर करा.",
        "eyebrow": "आधीच भरलेला अर्ज मसुदा",
        "noSchemeYet": "अजून कोणतीही योजना जुळली नाही",
        "profileMatch": "{pct}% प्रोफाइल जुळणी",
        "applicant": "अर्जदार",
        "category": "प्रवर्ग",
        "income": "वार्षिक उत्पन्न",
        "enterprise": "उद्यम",
        "enterpriseType": "उद्यमाचा प्रकार",
        "projectCost": "प्रकल्प खर्च",
        "loanRequired": "आवश्यक कर्ज",
        "location": "ठिकाण",
        "preferredScheme": "पसंतीची योजना",
        "preferredPartner": "पसंतीचा भागीदार",
        "dbtCheck": "आधार-डीबीटी तपासणी",
        "shareWhatsApp": "व्हॉट्सॲपवर पाठवा",
        "downloadPdf": "पीडीएफ डाउनलोड करा",
        "submit": "अर्ज सादर करा",
        "done": "पूर्ण",
        "percentDone": "{pct}% भरले",
        "noVerdictYet": "अजून तपासले नाही",
        "afterSubmitting": "सादर केल्यावर दिसेल",
        "outstanding": "{count} बाकी",
        "notReady": "वरील टप्पे पूर्ण करा",
        "step": {
            "profile": "प्रोफाइल",
            "eligibility": "पात्रता",
            "documents": "कागदपत्रे",
            "draft": "अर्ज मसुदा",
        },
        "sectionApplicant": "अर्जदाराचा तपशील",
        "sectionEnterprise": "उद्यम",
        "sectionFinancing": "वित्त",
        "sheetTitle": "अर्ज मसुदा · तपासणीसाठी तयार",
        "sheetOrgLine": "सामाजिक न्याय मंत्रालय · भारत सरकार · मसुदा, अर्ज नाही",
        "sheetReference": "अर्ज आयडी: {reference}",
        "sheetScheme": "योजना: {scheme}",
        "sheetDisclaimer": (
            "अर्जदाराने तपासणीसाठी तयार केलेला. हा सादर केलेला अर्ज नाही आणि SamarthSetu "
            "कर्ज मंजूर करत नाही — निर्णय चॅनेल भागीदार घेतो."
        ),
        "summaryHeading": "SamarthSetu · अर्ज सारांश",
        "generatedAt": "{when} रोजी तयार",
    },
    "bn": {
        "heroTitle": "আপনার আবেদন প্রায় প্রস্তুত",
        "heroSub": "সবচেয়ে উপযুক্ত প্রকল্পের জন্য দেখে নিয়ে জমা দিন।",
        "eyebrow": "আগে থেকে ভরা আবেদন খসড়া",
        "noSchemeYet": "এখনও কোনও প্রকল্প মেলেনি",
        "profileMatch": "{pct}% প্রোফাইলের মিল",
        "applicant": "আবেদনকারী",
        "category": "শ্রেণি",
        "income": "বার্ষিক আয়",
        "enterprise": "উদ্যোগ",
        "enterpriseType": "উদ্যোগের ধরন",
        "projectCost": "প্রকল্প ব্যয়",
        "loanRequired": "প্রয়োজনীয় ঋণ",
        "location": "অবস্থান",
        "preferredScheme": "পছন্দের প্রকল্প",
        "preferredPartner": "পছন্দের অংশীদার",
        "dbtCheck": "আধার-ডিবিটি যাচাই",
        "shareWhatsApp": "হোয়াটসঅ্যাপে পাঠান",
        "downloadPdf": "পিডিএফ ডাউনলোড করুন",
        "submit": "আবেদন জমা দিন",
        "done": "সম্পূর্ণ",
        "percentDone": "{pct}% ভরা হয়েছে",
        "noVerdictYet": "এখনও যাচাই হয়নি",
        "afterSubmitting": "জমা দেওয়ার পরে দেখা যাবে",
        "outstanding": "{count} বাকি",
        "notReady": "উপরের ধাপগুলি শেষ করুন",
        "step": {
            "profile": "প্রোফাইল",
            "eligibility": "যোগ্যতা",
            "documents": "নথিপত্র",
            "draft": "আবেদন খসড়া",
        },
        "sectionApplicant": "আবেদনকারীর বিবরণ",
        "sectionEnterprise": "উদ্যোগ",
        "sectionFinancing": "অর্থায়ন",
        "sheetTitle": "আবেদন খসড়া · পর্যালোচনার জন্য প্রস্তুত",
        "sheetOrgLine": "সামাজিক ন্যায় মন্ত্রক · ভারত সরকার · খসড়া, আবেদন নয়",
        "sheetReference": "আবেদন আইডি: {reference}",
        "sheetScheme": "প্রকল্প: {scheme}",
        "sheetDisclaimer": (
            "আবেদনকারী পর্যালোচনার জন্য তৈরি করেছেন। এটি জমা দেওয়া আবেদন নয় এবং "
            "SamarthSetu ঋণ অনুমোদন করে না — সিদ্ধান্ত নেন চ্যানেল পার্টনার।"
        ),
        "summaryHeading": "SamarthSetu · আবেদন সারসংক্ষেপ",
        "generatedAt": "{when}-এ তৈরি",
    },
    "ta": {
        "heroTitle": "உங்கள் விண்ணப்பம் கிட்டத்தட்ட தயார்",
        "heroSub": "மிகப் பொருத்தமான திட்டத்திற்கு சரிபார்த்து சமர்ப்பியுங்கள்.",
        "eyebrow": "முன்கூட்டியே நிரப்பப்பட்ட விண்ணப்ப வரைவு",
        "noSchemeYet": "இதுவரை எந்தத் திட்டமும் பொருந்தவில்லை",
        "profileMatch": "{pct}% சுயவிவரப் பொருத்தம்",
        "applicant": "விண்ணப்பதாரர்",
        "category": "பிரிவு",
        "income": "ஆண்டு வருமானம்",
        "enterprise": "நிறுவனம்",
        "enterpriseType": "நிறுவன வகை",
        "projectCost": "திட்டச் செலவு",
        "loanRequired": "தேவையான கடன்",
        "location": "இடம்",
        "preferredScheme": "விரும்பிய திட்டம்",
        "preferredPartner": "விரும்பிய பங்குதாரர்",
        "dbtCheck": "ஆதார்-டிபிடி சரிபார்ப்பு",
        "shareWhatsApp": "வாட்ஸ்அப்பில் பகிர",
        "downloadPdf": "பிடிஎஃப் பதிவிறக்கு",
        "submit": "விண்ணப்பத்தைச் சமர்ப்பி",
        "done": "முடிந்தது",
        "percentDone": "{pct}% நிரப்பப்பட்டது",
        "noVerdictYet": "இதுவரை சரிபார்க்கப்படவில்லை",
        "afterSubmitting": "சமர்ப்பித்த பிறகு தோன்றும்",
        "outstanding": "{count} நிலுவையில்",
        "notReady": "மேலே உள்ள படிகளை முடியுங்கள்",
        "step": {
            "profile": "சுயவிவரம்",
            "eligibility": "தகுதி",
            "documents": "ஆவணங்கள்",
            "draft": "விண்ணப்ப வரைவு",
        },
        "sectionApplicant": "விண்ணப்பதாரர் விவரங்கள்",
        "sectionEnterprise": "நிறுவனம்",
        "sectionFinancing": "நிதி",
        "sheetTitle": "விண்ணப்ப வரைவு · பரிசீலனைக்குத் தயார்",
        "sheetOrgLine": "சமூக நீதி அமைச்சகம் · இந்திய அரசு · வரைவு, விண்ணப்பம் அல்ல",
        "sheetReference": "விண்ணப்ப ஐடி: {reference}",
        "sheetScheme": "திட்டம்: {scheme}",
        "sheetDisclaimer": (
            "விண்ணப்பதாரரால் பரிசீலனைக்காகத் தயாரிக்கப்பட்டது. இது சமர்ப்பிக்கப்பட்ட "
            "விண்ணப்பம் அல்ல; SamarthSetu கடனை ஒப்புதல் அளிப்பதில்லை — சேனல் பங்குதாரரே "
            "முடிவு செய்கிறார்."
        ),
        "summaryHeading": "SamarthSetu · விண்ணப்பச் சுருக்கம்",
        "generatedAt": "{when} அன்று உருவாக்கப்பட்டது",
    },
    "te": {
        "heroTitle": "మీ దరఖాస్తు దాదాపు సిద్ధంగా ఉంది",
        "heroSub": "అత్యంత సరిపోయే పథకానికి సమీక్షించి సమర్పించండి.",
        "eyebrow": "ముందుగా నింపిన దరఖాస్తు ముసాయిదా",
        "noSchemeYet": "ఇప్పటివరకు ఏ పథకమూ సరిపోలలేదు",
        "profileMatch": "{pct}% ప్రొఫైల్ సరిపోలిక",
        "applicant": "దరఖాస్తుదారు",
        "category": "వర్గం",
        "income": "వార్షిక ఆదాయం",
        "enterprise": "సంస్థ",
        "enterpriseType": "సంస్థ రకం",
        "projectCost": "ప్రాజెక్ట్ వ్యయం",
        "loanRequired": "అవసరమైన రుణం",
        "location": "ప్రాంతం",
        "preferredScheme": "ఇష్టపడిన పథకం",
        "preferredPartner": "ఇష్టపడిన భాగస్వామి",
        "dbtCheck": "ఆధార్-డీబీటీ తనిఖీ",
        "shareWhatsApp": "వాట్సాప్‌లో పంచుకోండి",
        "downloadPdf": "పీడీఎఫ్ డౌన్‌లోడ్ చేయండి",
        "submit": "దరఖాస్తు సమర్పించండి",
        "done": "పూర్తి",
        "percentDone": "{pct}% నింపారు",
        "noVerdictYet": "ఇంకా తనిఖీ చేయలేదు",
        "afterSubmitting": "సమర్పించిన తర్వాత కనిపిస్తుంది",
        "outstanding": "{count} మిగిలి ఉన్నాయి",
        "notReady": "పైన ఉన్న దశలు పూర్తి చేయండి",
        "step": {
            "profile": "ప్రొఫైల్",
            "eligibility": "అర్హత",
            "documents": "పత్రాలు",
            "draft": "దరఖాస్తు ముసాయిదా",
        },
        "sectionApplicant": "దరఖాస్తుదారు వివరాలు",
        "sectionEnterprise": "సంస్థ",
        "sectionFinancing": "ఆర్థికం",
        "sheetTitle": "దరఖాస్తు ముసాయిదా · సమీక్ష కోసం సిద్ధం",
        "sheetOrgLine": "సామాజిక న్యాయ మంత్రిత్వ శాఖ · భారత ప్రభుత్వం · ముసాయిదా, దరఖాస్తు కాదు",
        "sheetReference": "దరఖాస్తు ఐడీ: {reference}",
        "sheetScheme": "పథకం: {scheme}",
        "sheetDisclaimer": (
            "దరఖాస్తుదారు సమీక్ష కోసం సిద్ధం చేశారు. ఇది సమర్పించిన దరఖాస్తు కాదు, "
            "SamarthSetu రుణాలను ఆమోదించదు — ఛానెల్ భాగస్వామి నిర్ణయిస్తారు."
        ),
        "summaryHeading": "SamarthSetu · దరఖాస్తు సారాంశం",
        "generatedAt": "{when}న రూపొందించబడింది",
    },
}

WHATSAPP = {
    "en": {
        "chip": "WhatsApp",
        "title": "Send application summary",
        "body": "Share this summary with your Channel Partner or family for a quick handoff at the counter.",
        "phoneLabel": "Recipient's phone (optional)",
        "phoneHint": "Leave blank to pick the recipient inside WhatsApp.",
        "messageLabel": "Message",
        "copy": "Copy",
        "copied": "Copied",
        "open": "Open in WhatsApp",
        "attachHint": "WhatsApp carries the text only. Download the PDF first and attach it there if you need it.",
    },
    "hi": {
        "chip": "व्हाट्सऐप",
        "title": "आवेदन सारांश भेजें",
        "body": "काउंटर पर तेज़ी से बात बनाने के लिए यह सारांश अपने चैनल पार्टनर या परिवार को भेजें।",
        "phoneLabel": "प्राप्तकर्ता का फ़ोन (वैकल्पिक)",
        "phoneHint": "खाली छोड़ें तो व्हाट्सऐप में ही प्राप्तकर्ता चुन सकते हैं।",
        "messageLabel": "संदेश",
        "copy": "कॉपी",
        "copied": "कॉपी हो गया",
        "open": "व्हाट्सऐप में खोलें",
        "attachHint": "व्हाट्सऐप केवल टेक्स्ट ले जाता है। ज़रूरत हो तो पहले पीडीएफ़ डाउनलोड कर वहाँ जोड़ें।",
    },
    "mr": {
        "chip": "व्हॉट्सॲप",
        "title": "अर्ज सारांश पाठवा",
        "body": "काउंटरवर पटकन देवाणघेवाण होण्यासाठी हा सारांश तुमच्या चॅनेल भागीदाराला किंवा कुटुंबाला पाठवा.",
        "phoneLabel": "प्राप्तकर्त्याचा फोन (ऐच्छिक)",
        "phoneHint": "रिकामे ठेवल्यास व्हॉट्सॲपमध्येच प्राप्तकर्ता निवडता येईल.",
        "messageLabel": "संदेश",
        "copy": "कॉपी",
        "copied": "कॉपी झाले",
        "open": "व्हॉट्सॲपमध्ये उघडा",
        "attachHint": "व्हॉट्सॲप फक्त मजकूर नेतो. गरज असल्यास आधी पीडीएफ डाउनलोड करून तिथे जोडा.",
    },
    "bn": {
        "chip": "হোয়াটসঅ্যাপ",
        "title": "আবেদনের সারসংক্ষেপ পাঠান",
        "body": "কাউন্টারে দ্রুত কাজ সারতে এই সারসংক্ষেপ আপনার চ্যানেল পার্টনার বা পরিবারকে পাঠান।",
        "phoneLabel": "প্রাপকের ফোন (ঐচ্ছিক)",
        "phoneHint": "খালি রাখলে হোয়াটসঅ্যাপেই প্রাপক বেছে নিতে পারবেন।",
        "messageLabel": "বার্তা",
        "copy": "কপি",
        "copied": "কপি হয়েছে",
        "open": "হোয়াটসঅ্যাপে খুলুন",
        "attachHint": "হোয়াটসঅ্যাপ কেবল লেখা নেয়। দরকার হলে আগে পিডিএফ ডাউনলোড করে সেখানে যুক্ত করুন।",
    },
    "ta": {
        "chip": "வாட்ஸ்அப்",
        "title": "விண்ணப்பச் சுருக்கத்தை அனுப்பு",
        "body": "கவுன்டரில் விரைவாகக் கையளிக்க இந்தச் சுருக்கத்தை உங்கள் சேனல் பங்குதாரருக்கோ குடும்பத்துக்கோ அனுப்புங்கள்.",
        "phoneLabel": "பெறுநரின் தொலைபேசி (விருப்பம்)",
        "phoneHint": "காலியாக விட்டால் வாட்ஸ்அப்பிலேயே பெறுநரைத் தேர்ந்தெடுக்கலாம்.",
        "messageLabel": "செய்தி",
        "copy": "நகலெடு",
        "copied": "நகலெடுக்கப்பட்டது",
        "open": "வாட்ஸ்அப்பில் திற",
        "attachHint": "வாட்ஸ்அப் உரையை மட்டுமே எடுத்துச் செல்லும். தேவைப்பட்டால் முதலில் பிடிஎஃப் பதிவிறக்கி அங்கே இணையுங்கள்.",
    },
    "te": {
        "chip": "వాట్సాప్",
        "title": "దరఖాస్తు సారాంశాన్ని పంపండి",
        "body": "కౌంటర్‌లో త్వరగా అప్పగించడానికి ఈ సారాంశాన్ని మీ ఛానెల్ భాగస్వామికి లేదా కుటుంబానికి పంపండి.",
        "phoneLabel": "స్వీకర్త ఫోన్ (ఐచ్ఛికం)",
        "phoneHint": "ఖాళీగా వదిలితే వాట్సాప్‌లోనే స్వీకర్తను ఎంచుకోవచ్చు.",
        "messageLabel": "సందేశం",
        "copy": "కాపీ",
        "copied": "కాపీ అయింది",
        "open": "వాట్సాప్‌లో తెరవండి",
        "attachHint": "వాట్సాప్ టెక్స్ట్ మాత్రమే తీసుకెళ్తుంది. అవసరమైతే ముందుగా పీడీఎఫ్ డౌన్‌లోడ్ చేసి అక్కడ జతచేయండి.",
    },
}

DBT = {
    "en": {
        "chip": "Aadhaar · DBT",
        "title": "Is your bank account Aadhaar-DBT linked?",
        "body": "A DBT-seeded account is the one a subsidy or grant actually lands in. Without seeding the money can be sanctioned and still not reach you.",
        "ifscLabel": "Bank IFSC",
        "ifscHint": "The first four letters identify your bank, e.g. SBIN, HDFC, PUNB.",
        "ifscBank": "Bank code {code}. That is a well-formed IFSC.",
        "ifscMalformed": "That does not look like an IFSC — four letters, a zero, then six characters.",
        "cannotCheck": "SamarthSetu cannot check your seeding status. Only NPCI and your bank can, so this sends you to the official page rather than guessing.",
        "openOfficial": "Check on the NPCI page",
        "noAadhaar": "We do not ask for your Aadhaar number.",
    },
    "hi": {
        "chip": "आधार · डीबीटी",
        "title": "क्या आपका बैंक खाता आधार-डीबीटी से जुड़ा है?",
        "body": "सब्सिडी या अनुदान उसी खाते में आता है जो डीबीटी से जुड़ा हो। जुड़ा न हो तो राशि स्वीकृत होकर भी आप तक नहीं पहुँचती।",
        "ifscLabel": "बैंक आईएफ़एससी",
        "ifscHint": "पहले चार अक्षर आपका बैंक बताते हैं, जैसे SBIN, HDFC, PUNB।",
        "ifscBank": "बैंक कोड {code}. यह सही रूप का आईएफ़एससी है।",
        "ifscMalformed": "यह आईएफ़एससी जैसा नहीं लगता — चार अक्षर, एक शून्य, फिर छह अक्षर।",
        "cannotCheck": "SamarthSetu आपकी डीबीटी स्थिति नहीं जाँच सकता। यह केवल एनपीसीआई और आपका बैंक बता सकते हैं, इसलिए अनुमान लगाने के बजाय यह आपको आधिकारिक पेज पर भेजता है।",
        "openOfficial": "एनपीसीआई पेज पर देखें",
        "noAadhaar": "हम आपका आधार नंबर नहीं पूछते।",
    },
    "mr": {
        "chip": "आधार · डीबीटी",
        "title": "तुमचे बँक खाते आधार-डीबीटीशी जोडलेले आहे का?",
        "body": "अनुदान त्याच खात्यात जमा होते जे डीबीटीशी जोडलेले असते. जोडलेले नसेल तर रक्कम मंजूर होऊनही तुमच्यापर्यंत पोहोचत नाही.",
        "ifscLabel": "बँक आयएफएससी",
        "ifscHint": "पहिली चार अक्षरे तुमची बँक ओळखतात, उदा. SBIN, HDFC, PUNB.",
        "ifscBank": "बँक कोड {code}. हा योग्य स्वरूपाचा आयएफएससी आहे.",
        "ifscMalformed": "हा आयएफएससी वाटत नाही — चार अक्षरे, एक शून्य, मग सहा अक्षरे.",
        "cannotCheck": "SamarthSetu तुमची डीबीटी स्थिती तपासू शकत नाही. ते फक्त एनपीसीआय आणि तुमची बँक सांगू शकते, म्हणून अंदाज न लावता हे तुम्हाला अधिकृत पानावर पाठवते.",
        "openOfficial": "एनपीसीआय पानावर पाहा",
        "noAadhaar": "आम्ही तुमचा आधार क्रमांक विचारत नाही.",
    },
    "bn": {
        "chip": "আধার · ডিবিটি",
        "title": "আপনার ব্যাঙ্ক অ্যাকাউন্ট কি আধার-ডিবিটি যুক্ত?",
        "body": "ভর্তুকি বা অনুদান সেই অ্যাকাউন্টেই আসে যা ডিবিটি-যুক্ত। যুক্ত না থাকলে টাকা মঞ্জুর হয়েও আপনার কাছে পৌঁছায় না।",
        "ifscLabel": "ব্যাঙ্ক আইএফএসসি",
        "ifscHint": "প্রথম চারটি অক্ষর আপনার ব্যাঙ্ক চেনায়, যেমন SBIN, HDFC, PUNB।",
        "ifscBank": "ব্যাঙ্ক কোড {code}। এটি সঠিক গঠনের আইএফএসসি।",
        "ifscMalformed": "এটি আইএফএসসি বলে মনে হচ্ছে না — চারটি অক্ষর, একটি শূন্য, তারপর ছয়টি অক্ষর।",
        "cannotCheck": "SamarthSetu আপনার ডিবিটি অবস্থা যাচাই করতে পারে না। কেবল এনপিসিআই ও আপনার ব্যাঙ্কই পারে, তাই অনুমান না করে এটি আপনাকে সরকারি পাতায় পাঠায়।",
        "openOfficial": "এনপিসিআই পাতায় দেখুন",
        "noAadhaar": "আমরা আপনার আধার নম্বর চাই না।",
    },
    "ta": {
        "chip": "ஆதார் · டிபிடி",
        "title": "உங்கள் வங்கிக் கணக்கு ஆதார்-டிபிடியுடன் இணைக்கப்பட்டுள்ளதா?",
        "body": "மானியம் அல்லது நிதியுதவி டிபிடி இணைக்கப்பட்ட கணக்கிலேயே வந்து சேரும். இணைக்கப்படவில்லை என்றால் பணம் ஒப்புதல் பெற்றும் உங்களை வந்தடையாது.",
        "ifscLabel": "வங்கி ஐஎஃப்எஸ்சி",
        "ifscHint": "முதல் நான்கு எழுத்துகள் உங்கள் வங்கியைக் குறிக்கும், எ.கா. SBIN, HDFC, PUNB.",
        "ifscBank": "வங்கிக் குறியீடு {code}. இது சரியான வடிவ ஐஎஃப்எஸ்சி.",
        "ifscMalformed": "இது ஐஎஃப்எஸ்சி போல் இல்லை — நான்கு எழுத்துகள், ஒரு பூஜ்ஜியம், பின் ஆறு எழுத்துகள்.",
        "cannotCheck": "SamarthSetu உங்கள் டிபிடி நிலையைச் சரிபார்க்க முடியாது. அதை என்பிசிஐ மற்றும் உங்கள் வங்கியால் மட்டுமே சொல்ல முடியும், எனவே ஊகிக்காமல் இது உங்களை அதிகாரப்பூர்வ பக்கத்திற்கு அனுப்புகிறது.",
        "openOfficial": "என்பிசிஐ பக்கத்தில் பார்க்க",
        "noAadhaar": "உங்கள் ஆதார் எண்ணை நாங்கள் கேட்பதில்லை.",
    },
    "te": {
        "chip": "ఆధార్ · డీబీటీ",
        "title": "మీ బ్యాంకు ఖాతా ఆధార్-డీబీటీతో అనుసంధానమైందా?",
        "body": "సబ్సిడీ లేదా గ్రాంట్ డీబీటీ అనుసంధాన ఖాతాలోనే జమ అవుతుంది. అనుసంధానం లేకపోతే డబ్బు మంజూరైనా మీకు చేరదు.",
        "ifscLabel": "బ్యాంకు ఐఎఫ్ఎస్‌సీ",
        "ifscHint": "మొదటి నాలుగు అక్షరాలు మీ బ్యాంకును సూచిస్తాయి, ఉదా. SBIN, HDFC, PUNB.",
        "ifscBank": "బ్యాంకు కోడ్ {code}. ఇది సరైన రూపంలోని ఐఎఫ్ఎస్‌సీ.",
        "ifscMalformed": "ఇది ఐఎఫ్ఎస్‌సీలా అనిపించడం లేదు — నాలుగు అక్షరాలు, ఒక సున్నా, తర్వాత ఆరు అక్షరాలు.",
        "cannotCheck": "SamarthSetu మీ డీబీటీ స్థితిని తనిఖీ చేయలేదు. అది ఎన్‌పీసీఐ మరియు మీ బ్యాంకు మాత్రమే చెప్పగలవు, కాబట్టి ఊహించకుండా ఇది మిమ్మల్ని అధికారిక పేజీకి పంపుతుంది.",
        "openOfficial": "ఎన్‌పీసీఐ పేజీలో చూడండి",
        "noAadhaar": "మేము మీ ఆధార్ నంబర్ అడగము.",
    },
}


def main() -> None:
    for locale in DRAFT:
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        draft = data.setdefault("applicationDraft", {})
        steps = {**draft.get("step", {}), **DRAFT[locale]["step"]}
        draft.update({**DRAFT[locale], "step": steps})

        data.setdefault("shareWhatsApp", {}).update(WHATSAPP[locale])
        data.setdefault("dbtCheck", {}).update(DBT[locale])

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"{locale}: +{len(DRAFT[locale]) - 1} applicationDraft, "
            f"+{len(WHATSAPP[locale])} shareWhatsApp, +{len(DBT[locale])} dbtCheck"
        )


if __name__ == "__main__":
    main()
