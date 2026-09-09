"""One-off: Samarth AI's chat strings, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`badge` and `disclaimer` are the pair that keeps this page honest and neither may drift.
The model on this path reads the citizen's words and restates the *rule engine's* verdict
in their language; it does not decide eligibility (CLAUDE.md rule 1). So the badge says
what it does — reads and explains — rather than "Powered by AI", which invites a citizen
to read the verdict as the model's opinion, and the disclaimer says plainly that nothing
here approves anything.

    python scripts/add-assistant-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

ASSISTANT = {
    "en": {
        "name": "Samarth AI",
        "tagline": "Your guide to MoSJE credit schemes",
        "badge": "Explains the rule engine",
        "conversation": "Conversation with Samarth AI",
        "greeting": (
            "Namaste. Ask me about the schemes, whether you qualify, what documents to "
            "bring, or what the instalments would look like. I read your answers and "
            "explain what the rules decide — I do not decide anything myself."
        ),
        "noReading": (
            "I could not get anything from that. Try telling me what you want the money "
            "for, roughly how much, and where you live."
        ),
        "placeholder": "Ask about eligibility, schemes or EMI…",
        "suggested": "Suggested questions",
        "promptEligible": "Am I eligible for a Term Loan?",
        "promptBest": "Which scheme is best for me?",
        "promptWhy": "Why was this scheme recommended?",
        "promptDocuments": "What documents do I need?",
        "promptPartner": "Find a partner near me",
        "openScheme": "Open scheme",
        "startApplication": "Start application",
        "docsHeading": "{count} documents still needed",
        "uploaded": "{name} added. I will keep the rest of the list here.",
        "disclaimer": (
            "Answers come from the published scheme rules and the answers you gave. "
            "SamarthSetu does not approve loans — the Channel Partner does."
        ),
    },
    "hi": {
        "name": "समर्थ एआई",
        "tagline": "MoSJE ऋण योजनाओं के लिए आपका मार्गदर्शक",
        "badge": "नियम इंजन को समझाता है",
        "conversation": "समर्थ एआई से बातचीत",
        "greeting": (
            "नमस्ते। योजनाओं के बारे में, अपनी पात्रता, ज़रूरी दस्तावेज़ या किस्तों के "
            "बारे में पूछिए। मैं आपके उत्तर पढ़कर बताता हूँ कि नियम क्या तय करते हैं — "
            "निर्णय मैं नहीं करता।"
        ),
        "noReading": (
            "इससे मुझे कुछ समझ नहीं आया। बताइए पैसा किस काम के लिए चाहिए, लगभग कितना, "
            "और आप कहाँ रहते हैं।"
        ),
        "placeholder": "पात्रता, योजना या ईएमआई के बारे में पूछें…",
        "suggested": "सुझाए गए प्रश्न",
        "promptEligible": "क्या मैं टर्म लोन के लिए पात्र हूँ?",
        "promptBest": "मेरे लिए कौन सी योजना सबसे अच्छी है?",
        "promptWhy": "यह योजना क्यों सुझाई गई?",
        "promptDocuments": "मुझे कौन से दस्तावेज़ चाहिए?",
        "promptPartner": "मेरे पास का भागीदार खोजें",
        "openScheme": "योजना खोलें",
        "startApplication": "आवेदन शुरू करें",
        "docsHeading": "{count} दस्तावेज़ अभी बाकी हैं",
        "uploaded": "{name} जुड़ गया। बाकी सूची यहीं रखता हूँ।",
        "disclaimer": (
            "उत्तर प्रकाशित योजना नियमों और आपके दिए उत्तरों से आते हैं। SamarthSetu ऋण "
            "स्वीकृत नहीं करता — यह चैनल पार्टनर करता है।"
        ),
    },
    "mr": {
        "name": "समर्थ एआय",
        "tagline": "MoSJE कर्ज योजनांसाठी तुमचा मार्गदर्शक",
        "badge": "नियम इंजिन समजावतो",
        "conversation": "समर्थ एआयशी संवाद",
        "greeting": (
            "नमस्कार. योजनांबद्दल, तुमच्या पात्रतेबद्दल, लागणाऱ्या कागदपत्रांबद्दल किंवा "
            "हप्त्यांबद्दल विचारा. मी तुमची उत्तरे वाचून नियम काय ठरवतात ते सांगतो — "
            "निर्णय मी घेत नाही."
        ),
        "noReading": (
            "यातून मला काही समजले नाही. पैसे कशासाठी हवेत, साधारण किती, आणि तुम्ही कुठे "
            "राहता ते सांगा."
        ),
        "placeholder": "पात्रता, योजना किंवा ईएमआयबद्दल विचारा…",
        "suggested": "सुचवलेले प्रश्न",
        "promptEligible": "मी टर्म लोनसाठी पात्र आहे का?",
        "promptBest": "माझ्यासाठी कोणती योजना सर्वोत्तम आहे?",
        "promptWhy": "ही योजना का सुचवली गेली?",
        "promptDocuments": "मला कोणती कागदपत्रे लागतील?",
        "promptPartner": "जवळचा भागीदार शोधा",
        "openScheme": "योजना उघडा",
        "startApplication": "अर्ज सुरू करा",
        "docsHeading": "{count} कागदपत्रे अजून बाकी",
        "uploaded": "{name} जोडले. उरलेली यादी इथेच ठेवतो.",
        "disclaimer": (
            "उत्तरे प्रकाशित योजना नियम आणि तुम्ही दिलेल्या उत्तरांवरून येतात. "
            "SamarthSetu कर्ज मंजूर करत नाही — ते चॅनेल भागीदार करतो."
        ),
    },
    "bn": {
        "name": "সমর্থ এআই",
        "tagline": "MoSJE ঋণ প্রকল্পে আপনার পথপ্রদর্শক",
        "badge": "নিয়ম ইঞ্জিন ব্যাখ্যা করে",
        "conversation": "সমর্থ এআই-এর সঙ্গে কথোপকথন",
        "greeting": (
            "নমস্কার। প্রকল্প, আপনার যোগ্যতা, প্রয়োজনীয় নথি বা কিস্তি নিয়ে জিজ্ঞাসা "
            "করুন। আমি আপনার উত্তর পড়ে নিয়ম কী বলে তা জানাই — সিদ্ধান্ত আমি নিই না।"
        ),
        "noReading": (
            "এতে আমি কিছু বুঝতে পারিনি। টাকা কী কাজে লাগবে, আনুমানিক কত, আর আপনি কোথায় "
            "থাকেন তা বলুন।"
        ),
        "placeholder": "যোগ্যতা, প্রকল্প বা ইএমআই নিয়ে জিজ্ঞাসা করুন…",
        "suggested": "প্রস্তাবিত প্রশ্ন",
        "promptEligible": "আমি কি টার্ম লোনের যোগ্য?",
        "promptBest": "আমার জন্য কোন প্রকল্প সবচেয়ে ভালো?",
        "promptWhy": "এই প্রকল্পটি কেন প্রস্তাব করা হল?",
        "promptDocuments": "আমার কোন নথি লাগবে?",
        "promptPartner": "কাছাকাছি অংশীদার খুঁজুন",
        "openScheme": "প্রকল্প খুলুন",
        "startApplication": "আবেদন শুরু করুন",
        "docsHeading": "{count}টি নথি এখনও বাকি",
        "uploaded": "{name} যুক্ত হয়েছে। বাকি তালিকা এখানেই রাখছি।",
        "disclaimer": (
            "উত্তর আসে প্রকাশিত প্রকল্পের নিয়ম ও আপনার দেওয়া উত্তর থেকে। SamarthSetu "
            "ঋণ অনুমোদন করে না — সেটি চ্যানেল পার্টনার করেন।"
        ),
    },
    "ta": {
        "name": "சமர்த் ஏஐ",
        "tagline": "MoSJE கடன் திட்டங்களுக்கு உங்கள் வழிகாட்டி",
        "badge": "விதி இயந்திரத்தை விளக்குகிறது",
        "conversation": "சமர்த் ஏஐ உடன் உரையாடல்",
        "greeting": (
            "வணக்கம். திட்டங்கள், உங்கள் தகுதி, தேவையான ஆவணங்கள் அல்லது தவணைகள் பற்றிக் "
            "கேளுங்கள். உங்கள் பதில்களைப் படித்து விதிகள் என்ன சொல்கின்றன என்பதை நான் "
            "விளக்குகிறேன் — முடிவை நான் எடுப்பதில்லை."
        ),
        "noReading": (
            "அதிலிருந்து எனக்கு ஒன்றும் புரியவில்லை. பணம் எதற்குத் தேவை, தோராயமாக "
            "எவ்வளவு, நீங்கள் எங்கு வசிக்கிறீர்கள் என்று சொல்லுங்கள்."
        ),
        "placeholder": "தகுதி, திட்டம் அல்லது இஎம்ஐ பற்றிக் கேளுங்கள்…",
        "suggested": "பரிந்துரைக்கப்பட்ட கேள்விகள்",
        "promptEligible": "நான் டர்ம் லோனுக்குத் தகுதியானவனா?",
        "promptBest": "எனக்கு எந்தத் திட்டம் சிறந்தது?",
        "promptWhy": "இந்தத் திட்டம் ஏன் பரிந்துரைக்கப்பட்டது?",
        "promptDocuments": "எனக்கு என்ன ஆவணங்கள் தேவை?",
        "promptPartner": "அருகிலுள்ள பங்குதாரரைக் கண்டறியுங்கள்",
        "openScheme": "திட்டத்தைத் திற",
        "startApplication": "விண்ணப்பத்தைத் தொடங்கு",
        "docsHeading": "{count} ஆவணங்கள் இன்னும் தேவை",
        "uploaded": "{name} சேர்க்கப்பட்டது. மீதிப் பட்டியலை இங்கேயே வைக்கிறேன்.",
        "disclaimer": (
            "பதில்கள் வெளியிடப்பட்ட திட்ட விதிகளிலிருந்தும் நீங்கள் அளித்த பதில்களிலிருந்தும் "
            "வருகின்றன. SamarthSetu கடனை ஒப்புதல் அளிப்பதில்லை — சேனல் பங்குதாரரே அளிக்கிறார்."
        ),
    },
    "te": {
        "name": "సమర్థ్ ఏఐ",
        "tagline": "MoSJE రుణ పథకాలకు మీ మార్గదర్శి",
        "badge": "నిబంధనల ఇంజిన్‌ను వివరిస్తుంది",
        "conversation": "సమర్థ్ ఏఐతో సంభాషణ",
        "greeting": (
            "నమస్కారం. పథకాల గురించి, మీ అర్హత గురించి, కావలసిన పత్రాల గురించి లేదా "
            "వాయిదాల గురించి అడగండి. మీ సమాధానాలు చదివి నిబంధనలు ఏమి చెబుతున్నాయో "
            "వివరిస్తాను — నిర్ణయం నేను తీసుకోను."
        ),
        "noReading": (
            "దాని నుండి నాకు ఏమీ అర్థం కాలేదు. డబ్బు దేనికి కావాలి, సుమారు ఎంత, మీరు "
            "ఎక్కడ ఉంటారు అని చెప్పండి."
        ),
        "placeholder": "అర్హత, పథకం లేదా ఈఎంఐ గురించి అడగండి…",
        "suggested": "సూచించిన ప్రశ్నలు",
        "promptEligible": "నేను టర్మ్ లోన్‌కు అర్హుడినా?",
        "promptBest": "నాకు ఏ పథకం మంచిది?",
        "promptWhy": "ఈ పథకం ఎందుకు సిఫారసు చేయబడింది?",
        "promptDocuments": "నాకు ఏ పత్రాలు కావాలి?",
        "promptPartner": "దగ్గరలోని భాగస్వామిని కనుగొనండి",
        "openScheme": "పథకం తెరవండి",
        "startApplication": "దరఖాస్తు ప్రారంభించండి",
        "docsHeading": "{count} పత్రాలు ఇంకా కావాలి",
        "uploaded": "{name} జోడించబడింది. మిగిలిన జాబితా ఇక్కడే ఉంచుతాను.",
        "disclaimer": (
            "సమాధానాలు ప్రచురించిన పథక నిబంధనలు మరియు మీరు ఇచ్చిన సమాధానాల నుండి "
            "వస్తాయి. SamarthSetu రుణాలను ఆమోదించదు — ఛానెల్ భాగస్వామి ఆమోదిస్తారు."
        ),
    },
}


def main() -> None:
    for locale, block in ASSISTANT.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("assistant", {}).update(block)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} assistant")


if __name__ == "__main__":
    main()
