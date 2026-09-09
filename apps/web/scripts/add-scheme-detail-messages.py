"""One-off: the strings the scheme detail page needs, drawn to the SamarthSetu drop.

Kept in the repo, like `add-match-layout-messages.py`, as the record of which strings were
added together and in which languages — useful when a reviewer sits down to check the four
draft locales (OPEN_ITEMS OI-4, OI-33).

The three `desc*` strings deserve a reviewer's attention. They are the only prose on the
page that is not either the citizen's own verdict or text out of the rule pack, and they
are written to state nothing the pack does not: every number in them is a placeholder
filled from `limits` at render time, and the sentence about Channel Partners is the
problem statement's own constraint that no money is lent directly. A translation that adds
a term, a document or a promise is a bug — there is no source behind it.

    python scripts/add-scheme-detail-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

DETAIL = {
    "en": {
        "tabOverview": "Overview",
        "tabEligibility": "Eligibility",
        "tabBenefits": "Benefits",
        "tabDocuments": "Documents",
        "tabPartners": "Partners",
        "tabProvenance": "Sources",
        "recommended": "Recommended for you",
        "maxFinancing": "Maximum financing",
        "interestRate": "Interest rate",
        "tenure": "Tenure",
        "tenureFull": "Repayment period",
        "description": "Description",
        "whoCanApply": "Who can apply",
        "financialAssistance": "Financial assistance",
        "descMicroFinance": (
            "Credit for a small production or service unit, funding up to {pct}% of its "
            "cost at {rate}% a year and advancing up to ₹{amount}. The money is released "
            "through an authorised Channel Partner, never directly."
        ),
        "descTermLoan": (
            "Credit for setting up or expanding an enterprise, funding up to {pct}% of "
            "project cost at {rate}% a year and advancing up to ₹{amount}. The money is "
            "released through an authorised Channel Partner, never directly."
        ),
        "descEducationLoan": (
            "Credit for course fees and related costs, funding up to {pct}% of the cost "
            "at {rate}% a year and advancing up to ₹{amount}. The money is released "
            "through an authorised Channel Partner, never directly."
        ),
        "workedExample": "What repayment would look like",
        "workedExampleIntro": (
            "Worked at this scheme's own ceiling — {amount} at {rate}% a year over "
            "{years} years."
        ),
        "monthlyEmi": "Monthly instalment",
        "totalInterest": "Interest",
        "totalRepaid": "Total repaid",
        "moratoriumInterest": "Added in moratorium",
        "exampleDisclaimer": (
            "Indicative only, from published rates. The sanctioning partner sets the "
            "actual terms."
        ),
        "noExample": (
            "This scheme does not publish a repayment period, so instalments cannot be "
            "worked out here."
        ),
        "partnersIntro": (
            "No money is lent directly. Only a Channel Partner authorised for this "
            "scheme can take and process your application."
        ),
        "readyToApply": "Ready to apply?",
        "calculateEmi": "Calculate EMI",
        "apply": "Start application",
    },
    "hi": {
        "tabOverview": "अवलोकन",
        "tabEligibility": "पात्रता",
        "tabBenefits": "लाभ",
        "tabDocuments": "दस्तावेज़",
        "tabPartners": "भागीदार",
        "tabProvenance": "स्रोत",
        "recommended": "आपके लिए सुझाई गई",
        "maxFinancing": "अधिकतम वित्तपोषण",
        "interestRate": "ब्याज दर",
        "tenure": "अवधि",
        "tenureFull": "चुकौती अवधि",
        "description": "विवरण",
        "whoCanApply": "कौन आवेदन कर सकता है",
        "financialAssistance": "वित्तीय सहायता",
        "descMicroFinance": (
            "छोटी उत्पादन या सेवा इकाई के लिए ऋण, जो इकाई की लागत का {pct}% तक {rate}% "
            "वार्षिक ब्याज पर और अधिकतम ₹{amount} तक देता है। राशि सीधे नहीं, अधिकृत "
            "चैनल पार्टनर के माध्यम से दी जाती है।"
        ),
        "descTermLoan": (
            "उद्यम शुरू करने या बढ़ाने के लिए ऋण, जो परियोजना लागत का {pct}% तक {rate}% "
            "वार्षिक ब्याज पर और अधिकतम ₹{amount} तक देता है। राशि सीधे नहीं, अधिकृत "
            "चैनल पार्टनर के माध्यम से दी जाती है।"
        ),
        "descEducationLoan": (
            "पाठ्यक्रम शुल्क और संबंधित खर्चों के लिए ऋण, जो लागत का {pct}% तक {rate}% "
            "वार्षिक ब्याज पर और अधिकतम ₹{amount} तक देता है। राशि सीधे नहीं, अधिकृत "
            "चैनल पार्टनर के माध्यम से दी जाती है।"
        ),
        "workedExample": "चुकौती कैसी दिखेगी",
        "workedExampleIntro": (
            "इस योजना की अपनी अधिकतम सीमा पर गणना — {amount}, {rate}% वार्षिक, "
            "{years} साल में।"
        ),
        "monthlyEmi": "मासिक किस्त",
        "totalInterest": "ब्याज",
        "totalRepaid": "कुल चुकाया",
        "moratoriumInterest": "अधिस्थगन में जुड़ा",
        "exampleDisclaimer": (
            "केवल संकेतात्मक, प्रकाशित दरों से। वास्तविक शर्तें स्वीकृति देने वाला "
            "भागीदार तय करता है।"
        ),
        "noExample": (
            "यह योजना चुकौती अवधि प्रकाशित नहीं करती, इसलिए यहाँ किस्त की गणना नहीं की "
            "जा सकती।"
        ),
        "partnersIntro": (
            "कोई राशि सीधे नहीं दी जाती। केवल इस योजना के लिए अधिकृत चैनल पार्टनर ही "
            "आपका आवेदन ले और आगे बढ़ा सकता है।"
        ),
        "readyToApply": "आवेदन के लिए तैयार?",
        "calculateEmi": "ईएमआई निकालें",
        "apply": "आवेदन शुरू करें",
    },
    "mr": {
        "tabOverview": "आढावा",
        "tabEligibility": "पात्रता",
        "tabBenefits": "लाभ",
        "tabDocuments": "कागदपत्रे",
        "tabPartners": "भागीदार",
        "tabProvenance": "स्रोत",
        "recommended": "तुमच्यासाठी सुचवलेली",
        "maxFinancing": "कमाल वित्तपुरवठा",
        "interestRate": "व्याजदर",
        "tenure": "मुदत",
        "tenureFull": "परतफेडीची मुदत",
        "description": "वर्णन",
        "whoCanApply": "कोण अर्ज करू शकते",
        "financialAssistance": "आर्थिक साहाय्य",
        "descMicroFinance": (
            "लहान उत्पादन किंवा सेवा घटकासाठी कर्ज, जे घटकाच्या खर्चाच्या {pct}% पर्यंत "
            "{rate}% वार्षिक दराने आणि जास्तीत जास्त ₹{amount} पर्यंत देते. रक्कम थेट "
            "नाही, अधिकृत चॅनेल भागीदारामार्फत दिली जाते."
        ),
        "descTermLoan": (
            "उद्यम सुरू करण्यासाठी किंवा वाढवण्यासाठी कर्ज, जे प्रकल्प खर्चाच्या {pct}% "
            "पर्यंत {rate}% वार्षिक दराने आणि जास्तीत जास्त ₹{amount} पर्यंत देते. रक्कम "
            "थेट नाही, अधिकृत चॅनेल भागीदारामार्फत दिली जाते."
        ),
        "descEducationLoan": (
            "अभ्यासक्रम शुल्क आणि संबंधित खर्चासाठी कर्ज, जे खर्चाच्या {pct}% पर्यंत "
            "{rate}% वार्षिक दराने आणि जास्तीत जास्त ₹{amount} पर्यंत देते. रक्कम थेट "
            "नाही, अधिकृत चॅनेल भागीदारामार्फत दिली जाते."
        ),
        "workedExample": "परतफेड कशी दिसेल",
        "workedExampleIntro": (
            "या योजनेच्या स्वतःच्या कमाल मर्यादेवर गणना — {amount}, {rate}% वार्षिक, "
            "{years} वर्षांत."
        ),
        "monthlyEmi": "मासिक हप्ता",
        "totalInterest": "व्याज",
        "totalRepaid": "एकूण परतफेड",
        "moratoriumInterest": "स्थगितीत जोडलेले",
        "exampleDisclaimer": (
            "फक्त सूचक, प्रकाशित दरांवरून. प्रत्यक्ष अटी मंजुरी देणारा भागीदार ठरवतो."
        ),
        "noExample": (
            "ही योजना परतफेडीची मुदत प्रकाशित करत नाही, त्यामुळे इथे हप्ता काढता येत नाही."
        ),
        "partnersIntro": (
            "कोणतीही रक्कम थेट दिली जात नाही. फक्त या योजनेसाठी अधिकृत चॅनेल भागीदारच "
            "तुमचा अर्ज घेऊ आणि पुढे नेऊ शकतो."
        ),
        "readyToApply": "अर्जासाठी तयार?",
        "calculateEmi": "ईएमआय काढा",
        "apply": "अर्ज सुरू करा",
    },
    "bn": {
        "tabOverview": "সংক্ষিপ্ত বিবরণ",
        "tabEligibility": "যোগ্যতা",
        "tabBenefits": "সুবিধা",
        "tabDocuments": "নথিপত্র",
        "tabPartners": "অংশীদার",
        "tabProvenance": "উৎস",
        "recommended": "আপনার জন্য প্রস্তাবিত",
        "maxFinancing": "সর্বোচ্চ অর্থায়ন",
        "interestRate": "সুদের হার",
        "tenure": "মেয়াদ",
        "tenureFull": "পরিশোধের মেয়াদ",
        "description": "বিবরণ",
        "whoCanApply": "কারা আবেদন করতে পারেন",
        "financialAssistance": "আর্থিক সহায়তা",
        "descMicroFinance": (
            "ছোট উৎপাদন বা পরিষেবা ইউনিটের জন্য ঋণ, যা ইউনিটের ব্যয়ের {pct}% পর্যন্ত "
            "{rate}% বার্ষিক হারে এবং সর্বোচ্চ ₹{amount} পর্যন্ত দেয়। টাকা সরাসরি নয়, "
            "অনুমোদিত চ্যানেল পার্টনারের মাধ্যমে দেওয়া হয়।"
        ),
        "descTermLoan": (
            "উদ্যোগ শুরু বা সম্প্রসারণের জন্য ঋণ, যা প্রকল্প ব্যয়ের {pct}% পর্যন্ত "
            "{rate}% বার্ষিক হারে এবং সর্বোচ্চ ₹{amount} পর্যন্ত দেয়। টাকা সরাসরি নয়, "
            "অনুমোদিত চ্যানেল পার্টনারের মাধ্যমে দেওয়া হয়।"
        ),
        "descEducationLoan": (
            "পাঠ্যক্রমের ফি ও সংশ্লিষ্ট ব্যয়ের জন্য ঋণ, যা ব্যয়ের {pct}% পর্যন্ত "
            "{rate}% বার্ষিক হারে এবং সর্বোচ্চ ₹{amount} পর্যন্ত দেয়। টাকা সরাসরি নয়, "
            "অনুমোদিত চ্যানেল পার্টনারের মাধ্যমে দেওয়া হয়।"
        ),
        "workedExample": "পরিশোধ কেমন দেখাবে",
        "workedExampleIntro": (
            "এই প্রকল্পের নিজস্ব সর্বোচ্চ সীমায় হিসাব — {amount}, {rate}% বার্ষিক, "
            "{years} বছরে।"
        ),
        "monthlyEmi": "মাসিক কিস্তি",
        "totalInterest": "সুদ",
        "totalRepaid": "মোট পরিশোধ",
        "moratoriumInterest": "স্থগিতিতে যুক্ত",
        "exampleDisclaimer": (
            "কেবল নির্দেশক, প্রকাশিত হার থেকে। প্রকৃত শর্ত অনুমোদনকারী অংশীদার ঠিক করেন।"
        ),
        "noExample": (
            "এই প্রকল্প পরিশোধের মেয়াদ প্রকাশ করে না, তাই এখানে কিস্তি হিসাব করা যায় না।"
        ),
        "partnersIntro": (
            "কোনও টাকা সরাসরি দেওয়া হয় না। কেবল এই প্রকল্পের জন্য অনুমোদিত চ্যানেল "
            "পার্টনারই আপনার আবেদন নিতে ও এগিয়ে নিতে পারেন।"
        ),
        "readyToApply": "আবেদনের জন্য প্রস্তুত?",
        "calculateEmi": "ইএমআই হিসাব করুন",
        "apply": "আবেদন শুরু করুন",
    },
    "ta": {
        "tabOverview": "மேலோட்டம்",
        "tabEligibility": "தகுதி",
        "tabBenefits": "பயன்கள்",
        "tabDocuments": "ஆவணங்கள்",
        "tabPartners": "பங்குதாரர்கள்",
        "tabProvenance": "ஆதாரங்கள்",
        "recommended": "உங்களுக்குப் பரிந்துரைக்கப்பட்டது",
        "maxFinancing": "அதிகபட்ச நிதியுதவி",
        "interestRate": "வட்டி விகிதம்",
        "tenure": "காலம்",
        "tenureFull": "திருப்பிச் செலுத்தும் காலம்",
        "description": "விளக்கம்",
        "whoCanApply": "யார் விண்ணப்பிக்கலாம்",
        "financialAssistance": "நிதி உதவி",
        "descMicroFinance": (
            "சிறிய உற்பத்தி அல்லது சேவை அலகுக்கான கடன். அலகின் செலவில் {pct}% வரை, "
            "ஆண்டுக்கு {rate}% வட்டியில், அதிகபட்சம் ₹{amount} வரை வழங்குகிறது. பணம் "
            "நேரடியாக அல்ல, அங்கீகரிக்கப்பட்ட சேனல் பங்குதாரர் வழியாகவே வழங்கப்படும்."
        ),
        "descTermLoan": (
            "தொழில் தொடங்க அல்லது விரிவாக்கக் கடன். திட்டச் செலவில் {pct}% வரை, "
            "ஆண்டுக்கு {rate}% வட்டியில், அதிகபட்சம் ₹{amount} வரை வழங்குகிறது. பணம் "
            "நேரடியாக அல்ல, அங்கீகரிக்கப்பட்ட சேனல் பங்குதாரர் வழியாகவே வழங்கப்படும்."
        ),
        "descEducationLoan": (
            "படிப்புக் கட்டணம் மற்றும் தொடர்புடைய செலவுகளுக்கான கடன். செலவில் {pct}% "
            "வரை, ஆண்டுக்கு {rate}% வட்டியில், அதிகபட்சம் ₹{amount} வரை வழங்குகிறது. "
            "பணம் நேரடியாக அல்ல, அங்கீகரிக்கப்பட்ட சேனல் பங்குதாரர் வழியாகவே வழங்கப்படும்."
        ),
        "workedExample": "திருப்பிச் செலுத்துவது எப்படி இருக்கும்",
        "workedExampleIntro": (
            "இத்திட்டத்தின் சொந்த உச்சவரம்பில் கணக்கிடப்பட்டது — {amount}, ஆண்டுக்கு "
            "{rate}%, {years} ஆண்டுகளில்."
        ),
        "monthlyEmi": "மாதத் தவணை",
        "totalInterest": "வட்டி",
        "totalRepaid": "மொத்தம் திருப்பியது",
        "moratoriumInterest": "தவணை விடுப்பில் சேர்ந்தது",
        "exampleDisclaimer": (
            "வெளியிடப்பட்ட விகிதங்களிலிருந்து, சுட்டிக்காட்டுவதற்கு மட்டுமே. உண்மையான "
            "நிபந்தனைகளை ஒப்புதல் அளிக்கும் பங்குதாரரே நிர்ணயிக்கிறார்."
        ),
        "noExample": (
            "இத்திட்டம் திருப்பிச் செலுத்தும் காலத்தை வெளியிடவில்லை, எனவே இங்கே தவணையைக் "
            "கணக்கிட முடியாது."
        ),
        "partnersIntro": (
            "எந்தப் பணமும் நேரடியாக வழங்கப்படுவதில்லை. இத்திட்டத்திற்கு அங்கீகரிக்கப்பட்ட "
            "சேனல் பங்குதாரர் மட்டுமே உங்கள் விண்ணப்பத்தைப் பெற்று நடத்த முடியும்."
        ),
        "readyToApply": "விண்ணப்பிக்கத் தயாரா?",
        "calculateEmi": "இஎம்ஐ கணக்கிடு",
        "apply": "விண்ணப்பத்தைத் தொடங்கு",
    },
    "te": {
        "tabOverview": "అవలోకనం",
        "tabEligibility": "అర్హత",
        "tabBenefits": "ప్రయోజనాలు",
        "tabDocuments": "పత్రాలు",
        "tabPartners": "భాగస్వాములు",
        "tabProvenance": "మూలాలు",
        "recommended": "మీ కోసం సిఫారసు చేయబడింది",
        "maxFinancing": "గరిష్ఠ ఆర్థిక సహాయం",
        "interestRate": "వడ్డీ రేటు",
        "tenure": "కాలం",
        "tenureFull": "తిరిగి చెల్లించే కాలం",
        "description": "వివరణ",
        "whoCanApply": "ఎవరు దరఖాస్తు చేయవచ్చు",
        "financialAssistance": "ఆర్థిక సహాయం",
        "descMicroFinance": (
            "చిన్న ఉత్పత్తి లేదా సేవా యూనిట్ కోసం రుణం. యూనిట్ ఖర్చులో {pct}% వరకు, "
            "సంవత్సరానికి {rate}% వడ్డీతో, గరిష్ఠంగా ₹{amount} వరకు ఇస్తుంది. డబ్బు "
            "నేరుగా కాదు, అధీకృత ఛానెల్ భాగస్వామి ద్వారానే విడుదల అవుతుంది."
        ),
        "descTermLoan": (
            "సంస్థ ప్రారంభించడానికి లేదా విస్తరించడానికి రుణం. ప్రాజెక్ట్ ఖర్చులో {pct}% "
            "వరకు, సంవత్సరానికి {rate}% వడ్డీతో, గరిష్ఠంగా ₹{amount} వరకు ఇస్తుంది. డబ్బు "
            "నేరుగా కాదు, అధీకృత ఛానెల్ భాగస్వామి ద్వారానే విడుదల అవుతుంది."
        ),
        "descEducationLoan": (
            "కోర్సు ఫీజు మరియు సంబంధిత ఖర్చుల కోసం రుణం. ఖర్చులో {pct}% వరకు, "
            "సంవత్సరానికి {rate}% వడ్డీతో, గరిష్ఠంగా ₹{amount} వరకు ఇస్తుంది. డబ్బు "
            "నేరుగా కాదు, అధీకృత ఛానెల్ భాగస్వామి ద్వారానే విడుదల అవుతుంది."
        ),
        "workedExample": "తిరిగి చెల్లింపు ఎలా ఉంటుంది",
        "workedExampleIntro": (
            "ఈ పథకం సొంత గరిష్ఠ పరిమితిపై లెక్కించినది — {amount}, సంవత్సరానికి "
            "{rate}%, {years} సంవత్సరాలలో."
        ),
        "monthlyEmi": "నెలవారీ వాయిదా",
        "totalInterest": "వడ్డీ",
        "totalRepaid": "మొత్తం చెల్లించినది",
        "moratoriumInterest": "మారటోరియంలో కలిపినది",
        "exampleDisclaimer": (
            "ప్రచురించిన రేట్ల నుండి, సూచన కోసం మాత్రమే. వాస్తవ షరతులను మంజూరు చేసే "
            "భాగస్వామి నిర్ణయిస్తారు."
        ),
        "noExample": (
            "ఈ పథకం తిరిగి చెల్లించే కాలాన్ని ప్రచురించదు, కాబట్టి ఇక్కడ వాయిదాను "
            "లెక్కించలేము."
        ),
        "partnersIntro": (
            "ఏ డబ్బూ నేరుగా ఇవ్వబడదు. ఈ పథకానికి అధీకృతమైన ఛానెల్ భాగస్వామి మాత్రమే మీ "
            "దరఖాస్తును స్వీకరించి ముందుకు తీసుకెళ్లగలరు."
        ),
        "readyToApply": "దరఖాస్తుకు సిద్ధమా?",
        "calculateEmi": "ఈఎంఐ లెక్కించండి",
        "apply": "దరఖాస్తు ప్రారంభించండి",
    },
}

# The labelled listen control on the scheme header names the language it will speak in,
# because the synthesiser reads in the page's language and someone who switched needs to
# know that before tapping. The language name itself comes from `LOCALE_NAMES`, always in
# its own script, so it is a placeholder here and never translated.
LISTEN_IN = {
    "en": "Listen ({language})",
    "hi": "सुनें ({language})",
    "mr": "ऐका ({language})",
    "bn": "শুনুন ({language})",
    "ta": "கேட்க ({language})",
    "te": "వినండి ({language})",
}

# `tabRules` became `tabEligibility`; `interestBand` and `maxLoan` stay, but the header
# tiles use their own shorter labels now.
REMOVED = ["tabRules"]


def main() -> None:
    for locale, block in DETAIL.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        detail = data.setdefault("schemeDetail", {})
        detail.update(block)
        dropped = [key for key in REMOVED if detail.pop(key, None) is not None]

        data.setdefault("results", {})["listenIn"] = LISTEN_IN[locale]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} schemeDetail, +1 results, -{len(dropped)}")


if __name__ == "__main__":
    main()
