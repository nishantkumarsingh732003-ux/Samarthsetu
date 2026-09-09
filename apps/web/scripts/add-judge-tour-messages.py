"""One-off: the nine-step judge walkthrough, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

EVERY CLAIM HERE HAS TO SURVIVE THE JUDGE PRESSING THE BUTTON IT DESCRIBES. That is the
one rule this copy is written under, and it is why several obvious phrases are missing:

  - Not "AI-powered matching" or "AI-driven recommendations". A deterministic, versioned
    rule engine decides, and the LLM is nowhere near a verdict (CLAUDE.md rule 1). The
    tour says so, because that is the differentiator — claiming the opposite would trade
    the strongest thing about this build for a weaker and untrue one.
  - Not a named model or version. What is configured is a provider setting; `none` is a
    first-class value and the product works with it. Step 8 says that instead.
  - Not "verified", "approved" or any number that is not on screen. SamarthSetu does not
    approve loans; the Channel Partner does, and step 9 says so.

    python scripts/add-judge-tour-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

JUDGE_TOUR = {
    "en": {
        "start": "Judge mode · 3-min tour",
        "label": "Judge walkthrough · {current}/{total}",
        "back": "Back",
        "next": "Next",
        "finish": "Finish",
        "close": "Close the walkthrough",

        "problemTitle": "The problem",
        "problemBody": (
            "A Scheduled Caste entrepreneur cannot easily answer two questions: which "
            "government credit scheme fits me, and which of the 100+ Channel Partners "
            "near me is authorised to process that one. Today they guess."
        ),
        "problemTip": (
            "The whole journey works without an account. “Check my eligibility” is the "
            "front door."
        ),

        "intakeTitle": "Four steps, saved as you go",
        "intakeBody": (
            "Each step saves as you leave it, so losing signal on a 2G connection costs "
            "one screen and not the whole form."
        ),
        "intakeTip": (
            "Step 1 is what the rules read. Step 2 is what a partner officer reads — it "
            "can never change a verdict."
        ),

        "dashboardTitle": "Every figure from the real database",
        "dashboardBody": (
            "Profile completion, the best match, what is left to borrow, and where the "
            "application stands."
        ),
        "dashboardTip": (
            "Nothing here is a placeholder. Seed scripts populate every screen from "
            "Postgres before the demo starts."
        ),

        "verdictTitle": "A deterministic engine decides",
        "verdictBody": (
            "Not a model. The same profile against the same rule pack gives "
            "byte-identical output every time, and the pack is versioned."
        ),
        "verdictTip": (
            "The line under the results names the engine version and the rule-pack hash "
            "that produced them."
        ),

        "explainTitle": "Every verdict names its rule",
        "explainBody": (
            "Each result carries matched_because[] and blocked_because[], and each of "
            "those carries a rule id. Where a scheme does not fit, the gap is shown "
            "against the requirement."
        ),
        "explainTip": (
            "Open “View eligibility” on any card, then “Why not this scheme?” on one "
            "that was blocked."
        ),

        "calculatorTitle": "What the instalments come to",
        "calculatorBody": (
            "EMI with a moratorium, principal against interest across the tenure, and a "
            "repayment plan the citizen can print and carry to the branch."
        ),
        "calculatorTip": (
            "The rates come from the rule pack, where every figure carries a source_url "
            "and a last_verified_on."
        ),

        "partnersTitle": "Where the money actually reaches",
        "partnersBody": (
            "Every pin is a branch at its own coordinates out of the PostGIS registry — "
            "State Channelising Agencies, public sector banks, RRBs and NBFC-MFIs."
        ),
        "partnersTip": (
            "The interesting thing is the absence: a district with banks but no SCA "
            "cannot process the schemes that route only through one."
        ),

        "assistantTitle": "The assistant explains; it never decides",
        "assistantBody": (
            "It answers from a context pack built out of the published rule pack and the "
            "engine's own verdicts, in the citizen's language, and restates what the "
            "rules decided rather than reaching its own conclusion."
        ),
        "assistantTip": (
            "With no model configured it still answers, deterministically. The model "
            "makes the words better and is never load-bearing."
        ),

        "applicationTitle": "Routed to a Channel Partner",
        "applicationBody": (
            "The draft is filled from the profile, the citizen confirms it, and it goes "
            "to a partner authorised for that loan category. SamarthSetu never lends."
        ),
        "applicationTip": (
            "The reference number tracks it without an account. The API walkthrough, "
            "with runnable requests, is at /demo."
        ),
    },
    "hi": {
        "start": "जज मोड · 3 मिनट का दौरा",
        "label": "जज वॉकथ्रू · {current}/{total}",
        "back": "पीछे",
        "next": "आगे",
        "finish": "समाप्त",
        "close": "वॉकथ्रू बंद करें",

        "problemTitle": "समस्या",
        "problemBody": (
            "एक अनुसूचित जाति उद्यमी दो सवालों का जवाब आसानी से नहीं दे पाता: कौन-सी सरकारी "
            "ऋण योजना मुझ पर लागू होती है, और मेरे पास के 100+ चैनल पार्टनर में से कौन उसी "
            "योजना के लिए अधिकृत है। आज वे अंदाज़ा लगाते हैं।"
        ),
        "problemTip": (
            "पूरी यात्रा बिना खाते के चलती है। “अपनी पात्रता देखें” ही मुख्य दरवाज़ा है।"
        ),

        "intakeTitle": "चार चरण, हर चरण पर सहेजे गए",
        "intakeBody": (
            "हर चरण छोड़ते ही सहेजा जाता है, इसलिए 2G पर सिग्नल जाने से एक स्क्रीन जाती है, "
            "पूरा फ़ॉर्म नहीं।"
        ),
        "intakeTip": (
            "चरण 1 वही है जो नियम पढ़ते हैं। चरण 2 पार्टनर अधिकारी पढ़ता है — वह फ़ैसला कभी "
            "नहीं बदल सकता।"
        ),

        "dashboardTitle": "हर आँकड़ा असली डेटाबेस से",
        "dashboardBody": (
            "प्रोफ़ाइल पूर्णता, सबसे अच्छा मैच, कितना उधार लेना बाकी है, और आवेदन कहाँ पहुँचा है।"
        ),
        "dashboardTip": (
            "यहाँ कुछ भी नकली नहीं है। डेमो से पहले सीड स्क्रिप्ट हर स्क्रीन को Postgres से "
            "भरती हैं।"
        ),

        "verdictTitle": "फ़ैसला एक निश्चित नियम इंजन करता है",
        "verdictBody": (
            "कोई मॉडल नहीं। वही प्रोफ़ाइल और वही रूल पैक हर बार बिल्कुल एक जैसा परिणाम देते "
            "हैं, और पैक संस्करणित है।"
        ),
        "verdictTip": (
            "परिणामों के नीचे की पंक्ति इंजन संस्करण और रूल-पैक हैश बताती है जिसने इन्हें बनाया।"
        ),

        "explainTitle": "हर फ़ैसला अपना नियम बताता है",
        "explainBody": (
            "हर परिणाम में matched_because[] और blocked_because[] होते हैं, और हर एक में "
            "नियम आईडी होती है। जहाँ योजना फिट नहीं बैठती, वहाँ आवश्यकता के सामने अंतर "
            "दिखाया जाता है।"
        ),
        "explainTip": (
            "किसी भी कार्ड पर “पात्रता देखें” खोलें, फिर रुकी हुई योजना पर “यह योजना क्यों "
            "नहीं?” देखें।"
        ),

        "calculatorTitle": "किस्तें कितनी बनेंगी",
        "calculatorBody": (
            "मोरेटोरियम के साथ ईएमआई, पूरी अवधि में मूलधन बनाम ब्याज, और एक चुकौती योजना "
            "जिसे नागरिक छापकर शाखा ले जा सकता है।"
        ),
        "calculatorTip": (
            "दरें रूल पैक से आती हैं, जहाँ हर आँकड़े के साथ source_url और last_verified_on "
            "होता है।"
        ),

        "partnersTitle": "पैसा असल में कहाँ पहुँचता है",
        "partnersBody": (
            "हर पिन PostGIS रजिस्ट्री से अपने ही अक्षांश-देशांतर पर एक शाखा है — राज्य "
            "चैनलाइज़िंग एजेंसियाँ, सार्वजनिक क्षेत्र के बैंक, आरआरबी और एनबीएफ़सी-एमएफ़आई।"
        ),
        "partnersTip": (
            "दिलचस्प बात अनुपस्थिति है: जिस ज़िले में बैंक हैं पर कोई एससीए नहीं, वहाँ केवल "
            "एससीए से जाने वाली योजनाएँ नहीं बन सकतीं।"
        ),

        "assistantTitle": "सहायक समझाता है; फ़ैसला कभी नहीं करता",
        "assistantBody": (
            "यह प्रकाशित रूल पैक और इंजन के अपने फ़ैसलों से बने संदर्भ से, नागरिक की भाषा में "
            "जवाब देता है, और अपना निष्कर्ष निकालने के बजाय नियमों का फ़ैसला दोहराता है।"
        ),
        "assistantTip": (
            "बिना किसी मॉडल के भी यह निश्चित रूप से जवाब देता है। मॉडल शब्द बेहतर बनाता है, "
            "कभी ज़रूरी नहीं होता।"
        ),

        "applicationTitle": "चैनल पार्टनर तक भेजा गया",
        "applicationBody": (
            "मसौदा प्रोफ़ाइल से भरा जाता है, नागरिक उसकी पुष्टि करता है, और वह उस ऋण श्रेणी "
            "के लिए अधिकृत पार्टनर के पास जाता है। SamarthSetu कभी ऋण नहीं देता।"
        ),
        "applicationTip": (
            "संदर्भ संख्या बिना खाते के भी स्थिति बताती है। चलाने योग्य अनुरोधों वाला API "
            "वॉकथ्रू /demo पर है।"
        ),
    },
    "mr": {
        "start": "जज मोड · 3 मिनिटांचा फेरफटका",
        "label": "जज वॉकथ्रू · {current}/{total}",
        "back": "मागे",
        "next": "पुढे",
        "finish": "पूर्ण",
        "close": "वॉकथ्रू बंद करा",

        "problemTitle": "समस्या",
        "problemBody": (
            "अनुसूचित जातीच्या उद्योजकाला दोन प्रश्नांची उत्तरे सहज मिळत नाहीत: कोणती सरकारी "
            "कर्ज योजना माझ्यासाठी आहे, आणि जवळच्या 100+ चॅनेल पार्टनरपैकी कोण तीच योजना "
            "हाताळण्यास अधिकृत आहे. आज ते अंदाज लावतात."
        ),
        "problemTip": (
            "संपूर्ण प्रवास खात्याशिवाय चालतो. “तुमची पात्रता पाहा” हेच मुख्य प्रवेशद्वार आहे."
        ),

        "intakeTitle": "चार पायऱ्या, प्रत्येक पायरीवर जतन",
        "intakeBody": (
            "प्रत्येक पायरी सोडताच जतन होते, त्यामुळे 2G वर सिग्नल गेला तर एक स्क्रीन जाते, "
            "पूर्ण फॉर्म नाही."
        ),
        "intakeTip": (
            "पायरी 1 नियम वाचतात. पायरी 2 पार्टनर अधिकारी वाचतो — ती निकाल कधीच बदलू शकत नाही."
        ),

        "dashboardTitle": "प्रत्येक आकडा खऱ्या डेटाबेसमधून",
        "dashboardBody": (
            "प्रोफाइल पूर्णता, सर्वोत्तम जुळणी, किती कर्ज घ्यायचे बाकी आहे, आणि अर्ज कुठे "
            "पोहोचला आहे."
        ),
        "dashboardTip": (
            "इथे काहीही बनावट नाही. डेमोपूर्वी सीड स्क्रिप्ट प्रत्येक स्क्रीन Postgres मधून भरतात."
        ),

        "verdictTitle": "निकाल ठरवते ते निश्चित नियम इंजिन",
        "verdictBody": (
            "मॉडेल नाही. तीच प्रोफाइल आणि तोच रूल पॅक दरवेळी अगदी सारखाच निकाल देतो, आणि "
            "पॅकला आवृत्ती आहे."
        ),
        "verdictTip": (
            "निकालांखालची ओळ इंजिन आवृत्ती आणि रूल-पॅक हॅश सांगते ज्याने हे तयार केले."
        ),

        "explainTitle": "प्रत्येक निकाल त्याचा नियम सांगतो",
        "explainBody": (
            "प्रत्येक निकालात matched_because[] आणि blocked_because[] असतात, आणि प्रत्येकात "
            "नियम आयडी असतो. योजना बसत नसेल तिथे आवश्यकतेसमोर फरक दाखवला जातो."
        ),
        "explainTip": (
            "कोणत्याही कार्डवर “पात्रता पाहा” उघडा, मग अडलेल्या योजनेवर “ही योजना का नाही?” पाहा."
        ),

        "calculatorTitle": "हप्ते किती होतील",
        "calculatorBody": (
            "मोरेटोरियमसह ईएमआय, संपूर्ण मुदतीत मुद्दल विरुद्ध व्याज, आणि नागरिक छापून "
            "शाखेत नेऊ शकेल अशी परतफेड योजना."
        ),
        "calculatorTip": (
            "दर रूल पॅकमधून येतात, जिथे प्रत्येक आकड्यासोबत source_url आणि last_verified_on असते."
        ),

        "partnersTitle": "पैसा प्रत्यक्षात कुठे पोहोचतो",
        "partnersBody": (
            "प्रत्येक पिन PostGIS नोंदणीतून स्वतःच्या अक्षांश-रेखांशावरची शाखा आहे — राज्य "
            "चॅनेलायझिंग एजन्सी, सार्वजनिक क्षेत्रातील बँका, आरआरबी आणि एनबीएफसी-एमएफआय."
        ),
        "partnersTip": (
            "मनोरंजक गोष्ट अनुपस्थिती आहे: बँका असूनही एससीए नसलेल्या जिल्ह्यात फक्त एससीएमार्गे "
            "जाणाऱ्या योजना होऊ शकत नाहीत."
        ),

        "assistantTitle": "सहायक समजावतो; निर्णय कधीच घेत नाही",
        "assistantBody": (
            "तो प्रकाशित रूल पॅक आणि इंजिनच्या स्वतःच्या निकालांवरून बनवलेल्या संदर्भातून, "
            "नागरिकाच्या भाषेत उत्तर देतो, आणि स्वतःचा निष्कर्ष काढण्याऐवजी नियमांचा निकाल "
            "पुन्हा सांगतो."
        ),
        "assistantTip": (
            "कोणतेही मॉडेल नसतानाही तो निश्चितपणे उत्तर देतो. मॉडेल शब्द अधिक चांगले करते, "
            "ते कधीच अनिवार्य नसते."
        ),

        "applicationTitle": "चॅनेल पार्टनरकडे पाठवले",
        "applicationBody": (
            "मसुदा प्रोफाइलमधून भरला जातो, नागरिक त्याची खात्री करतो, आणि तो त्या कर्ज "
            "प्रकारासाठी अधिकृत पार्टनरकडे जातो. SamarthSetu कधीही कर्ज देत नाही."
        ),
        "applicationTip": (
            "संदर्भ क्रमांक खात्याशिवायही स्थिती दाखवतो. चालवता येणाऱ्या विनंत्यांसह API "
            "वॉकथ्रू /demo वर आहे."
        ),
    },
    "bn": {
        "start": "জাজ মোড · ৩ মিনিটের সফর",
        "label": "জাজ ওয়াকথ্রু · {current}/{total}",
        "back": "পিছনে",
        "next": "পরবর্তী",
        "finish": "শেষ",
        "close": "ওয়াকথ্রু বন্ধ করুন",

        "problemTitle": "সমস্যাটি",
        "problemBody": (
            "একজন তফসিলি জাতির উদ্যোক্তা দুটি প্রশ্নের উত্তর সহজে পান না: কোন সরকারি ঋণ "
            "প্রকল্প আমার জন্য, আর কাছের ১০০+ চ্যানেল পার্টনারের মধ্যে কে সেই প্রকল্পের জন্য "
            "অনুমোদিত। আজ তাঁরা অনুমান করেন।"
        ),
        "problemTip": (
            "পুরো যাত্রা অ্যাকাউন্ট ছাড়াই চলে। “আপনার যোগ্যতা দেখুন” হল প্রবেশপথ।"
        ),

        "intakeTitle": "চারটি ধাপ, প্রতিটিতেই সংরক্ষিত",
        "intakeBody": (
            "প্রতিটি ধাপ ছাড়ার সঙ্গে সঙ্গে সংরক্ষিত হয়, তাই 2G-তে সিগন্যাল গেলে একটি স্ক্রিন "
            "যায়, পুরো ফর্ম নয়।"
        ),
        "intakeTip": (
            "ধাপ ১ নিয়ম পড়ে। ধাপ ২ পার্টনার অফিসার পড়েন — তা কখনও সিদ্ধান্ত বদলাতে পারে না।"
        ),

        "dashboardTitle": "প্রতিটি সংখ্যা আসল ডেটাবেস থেকে",
        "dashboardBody": (
            "প্রোফাইল সম্পূর্ণতা, সেরা মিল, কত ধার নেওয়া বাকি, এবং আবেদন কোথায় পৌঁছেছে।"
        ),
        "dashboardTip": (
            "এখানে কিছুই সাজানো নয়। ডেমোর আগে সিড স্ক্রিপ্ট প্রতিটি স্ক্রিন Postgres থেকে ভরে।"
        ),

        "verdictTitle": "সিদ্ধান্ত নেয় একটি নির্দিষ্ট নিয়ম ইঞ্জিন",
        "verdictBody": (
            "কোনও মডেল নয়। একই প্রোফাইল ও একই রুল প্যাক প্রতিবার হুবহু একই ফল দেয়, এবং "
            "প্যাকটির সংস্করণ আছে।"
        ),
        "verdictTip": (
            "ফলাফলের নিচের লাইনটি ইঞ্জিন সংস্করণ ও রুল-প্যাক হ্যাশ জানায় যা এগুলি তৈরি করেছে।"
        ),

        "explainTitle": "প্রতিটি সিদ্ধান্ত তার নিয়ম জানায়",
        "explainBody": (
            "প্রতিটি ফলে matched_because[] ও blocked_because[] থাকে, আর প্রতিটিতে একটি "
            "রুল আইডি থাকে। যেখানে প্রকল্প মেলে না, সেখানে প্রয়োজনের পাশে ফারাক দেখানো হয়।"
        ),
        "explainTip": (
            "যেকোনও কার্ডে “যোগ্যতা দেখুন” খুলুন, তারপর আটকে যাওয়া প্রকল্পে “কেন এই প্রকল্প নয়?” দেখুন।"
        ),

        "calculatorTitle": "কিস্তি কত দাঁড়ায়",
        "calculatorBody": (
            "মোরাটোরিয়াম সহ ইএমআই, পুরো মেয়াদে আসল বনাম সুদ, এবং একটি পরিশোধ পরিকল্পনা যা "
            "নাগরিক ছাপিয়ে শাখায় নিয়ে যেতে পারেন।"
        ),
        "calculatorTip": (
            "হার আসে রুল প্যাক থেকে, যেখানে প্রতিটি সংখ্যার সঙ্গে source_url ও "
            "last_verified_on থাকে।"
        ),

        "partnersTitle": "টাকা আসলে কোথায় পৌঁছয়",
        "partnersBody": (
            "প্রতিটি পিন PostGIS রেজিস্ট্রি থেকে নিজের অক্ষাংশ-দ্রাঘিমায় একটি শাখা — রাজ্য "
            "চ্যানেলাইজিং এজেন্সি, রাষ্ট্রায়ত্ত ব্যাঙ্ক, আরআরবি ও এনবিএফসি-এমএফআই।"
        ),
        "partnersTip": (
            "আসল কথা অনুপস্থিতি: যে জেলায় ব্যাঙ্ক আছে কিন্তু এসসিএ নেই, সেখানে কেবল এসসিএ "
            "দিয়ে যাওয়া প্রকল্পগুলি হয় না।"
        ),

        "assistantTitle": "সহায়ক ব্যাখ্যা করে; সিদ্ধান্ত কখনও নেয় না",
        "assistantBody": (
            "প্রকাশিত রুল প্যাক ও ইঞ্জিনের নিজস্ব সিদ্ধান্ত থেকে তৈরি প্রসঙ্গ থেকে এটি "
            "নাগরিকের ভাষায় উত্তর দেয়, এবং নিজের সিদ্ধান্তে না গিয়ে নিয়ম যা ঠিক করেছে তা-ই "
            "আবার বলে।"
        ),
        "assistantTip": (
            "কোনও মডেল না থাকলেও এটি নির্দিষ্টভাবে উত্তর দেয়। মডেল শব্দগুলিকে ভালো করে, "
            "কখনও অপরিহার্য নয়।"
        ),

        "applicationTitle": "চ্যানেল পার্টনারের কাছে পাঠানো",
        "applicationBody": (
            "খসড়া প্রোফাইল থেকে ভরা হয়, নাগরিক তা নিশ্চিত করেন, এবং সেটি ওই ঋণ শ্রেণির জন্য "
            "অনুমোদিত পার্টনারের কাছে যায়। SamarthSetu কখনও ঋণ দেয় না।"
        ),
        "applicationTip": (
            "রেফারেন্স নম্বর অ্যাকাউন্ট ছাড়াই অবস্থা জানায়। চালানোর মতো অনুরোধ সহ API "
            "ওয়াকথ্রু আছে /demo-তে।"
        ),
    },
    "ta": {
        "start": "நடுவர் பயன்முறை · 3 நிமிட சுற்று",
        "label": "நடுவர் சுற்று · {current}/{total}",
        "back": "பின்",
        "next": "அடுத்து",
        "finish": "முடி",
        "close": "சுற்றை மூடு",

        "problemTitle": "பிரச்சினை",
        "problemBody": (
            "பட்டியல் சாதி தொழில்முனைவோர் இரு கேள்விகளுக்கு எளிதில் பதில் காண முடிவதில்லை: "
            "எந்த அரசு கடன் திட்டம் எனக்குப் பொருந்தும், அருகிலுள்ள 100+ சேனல் பார்ட்னர்களில் "
            "அந்தத் திட்டத்தை யார் கையாள அங்கீகரிக்கப்பட்டவர். இன்று அவர்கள் ஊகிக்கிறார்கள்."
        ),
        "problemTip": (
            "முழுப் பயணமும் கணக்கு இல்லாமல் இயங்கும். “உங்கள் தகுதியைப் பாருங்கள்” என்பதே "
            "நுழைவாயில்."
        ),

        "intakeTitle": "நான்கு படிகள், ஒவ்வொன்றிலும் சேமிப்பு",
        "intakeBody": (
            "ஒவ்வொரு படியையும் விட்டு நகரும்போதே சேமிக்கப்படுகிறது, எனவே 2G-யில் சிக்னல் "
            "போனால் ஒரு திரை மட்டுமே போகும், முழு படிவமும் அல்ல."
        ),
        "intakeTip": (
            "படி 1-ஐ விதிகள் படிக்கின்றன. படி 2-ஐ பார்ட்னர் அதிகாரி படிக்கிறார் — அது முடிவை "
            "ஒருபோதும் மாற்றாது."
        ),

        "dashboardTitle": "ஒவ்வொரு எண்ணும் உண்மையான தரவுத்தளத்திலிருந்து",
        "dashboardBody": (
            "சுயவிவரம் நிறைவு, சிறந்த பொருத்தம், இன்னும் எவ்வளவு கடன் தேவை, விண்ணப்பம் எங்கு "
            "இருக்கிறது."
        ),
        "dashboardTip": (
            "இங்கே எதுவும் போலியானது அல்ல. விளக்கத்திற்கு முன் சீட் ஸ்கிரிப்ட்கள் ஒவ்வொரு "
            "திரையையும் Postgres-லிருந்து நிரப்புகின்றன."
        ),

        "verdictTitle": "முடிவை ஒரு உறுதியான விதி இயந்திரம் எடுக்கிறது",
        "verdictBody": (
            "மாதிரி அல்ல. அதே சுயவிவரமும் அதே விதித் தொகுப்பும் ஒவ்வொரு முறையும் அப்படியே "
            "ஒரே முடிவைத் தரும், தொகுப்புக்குப் பதிப்பு உண்டு."
        ),
        "verdictTip": (
            "முடிவுகளுக்குக் கீழுள்ள வரி, அவற்றை உருவாக்கிய இயந்திரப் பதிப்பையும் விதித் "
            "தொகுப்பு ஹாஷையும் சொல்கிறது."
        ),

        "explainTitle": "ஒவ்வொரு முடிவும் தன் விதியைச் சொல்கிறது",
        "explainBody": (
            "ஒவ்வொரு முடிவிலும் matched_because[] மற்றும் blocked_because[] உள்ளன, "
            "ஒவ்வொன்றிலும் விதி ஐடி உண்டு. திட்டம் பொருந்தாத இடத்தில், தேவைக்கு எதிராக இடைவெளி "
            "காட்டப்படுகிறது."
        ),
        "explainTip": (
            "எந்த அட்டையிலும் “தகுதியைப் பாருங்கள்” திறந்து, பின் தடுக்கப்பட்ட ஒன்றில் “இந்தத் "
            "திட்டம் ஏன் இல்லை?” பாருங்கள்."
        ),

        "calculatorTitle": "தவணைகள் எவ்வளவு வரும்",
        "calculatorBody": (
            "மொரட்டோரியத்துடன் EMI, முழுக் காலத்திலும் அசல் எதிராக வட்டி, மற்றும் குடிமகன் "
            "அச்சிட்டு கிளைக்கு எடுத்துச் செல்லக்கூடிய திருப்பிச் செலுத்தும் திட்டம்."
        ),
        "calculatorTip": (
            "விகிதங்கள் விதித் தொகுப்பிலிருந்து வருகின்றன, அங்கு ஒவ்வொரு எண்ணுடனும் "
            "source_url மற்றும் last_verified_on இருக்கும்."
        ),

        "partnersTitle": "பணம் உண்மையில் எங்கு சேர்கிறது",
        "partnersBody": (
            "ஒவ்வொரு குறியும் PostGIS பதிவேட்டிலிருந்து அதன் சொந்த அட்சரேகை-தீர்க்கரேகையில் "
            "உள்ள ஒரு கிளை — மாநில சேனலைசிங் ஏஜென்சிகள், பொதுத்துறை வங்கிகள், RRB மற்றும் "
            "NBFC-MFI."
        ),
        "partnersTip": (
            "முக்கியமானது இல்லாமை: வங்கிகள் இருந்தும் SCA இல்லாத மாவட்டத்தில், SCA வழியாக "
            "மட்டுமே செல்லும் திட்டங்கள் நடக்காது."
        ),

        "assistantTitle": "உதவியாளர் விளக்குகிறார்; ஒருபோதும் முடிவெடுப்பதில்லை",
        "assistantBody": (
            "வெளியிடப்பட்ட விதித் தொகுப்பிலிருந்தும் இயந்திரத்தின் சொந்த முடிவுகளிலிருந்தும் "
            "கட்டப்பட்ட சூழலிலிருந்து, குடிமகனின் மொழியில் பதிலளிக்கிறது, தன் சொந்த முடிவுக்கு "
            "வராமல் விதிகள் சொன்னதையே திரும்பச் சொல்கிறது."
        ),
        "assistantTip": (
            "எந்த மாதிரியும் இல்லாமலும் இது உறுதியாகப் பதிலளிக்கும். மாதிரி சொற்களை "
            "மேம்படுத்துகிறது, ஒருபோதும் இன்றியமையாதது அல்ல."
        ),

        "applicationTitle": "சேனல் பார்ட்னருக்கு அனுப்பப்பட்டது",
        "applicationBody": (
            "வரைவு சுயவிவரத்திலிருந்து நிரப்பப்படுகிறது, குடிமகன் உறுதி செய்கிறார், அது அந்தக் "
            "கடன் வகைக்கு அங்கீகரிக்கப்பட்ட பார்ட்னரிடம் செல்கிறது. SamarthSetu ஒருபோதும் "
            "கடன் தருவதில்லை."
        ),
        "applicationTip": (
            "குறிப்பு எண் கணக்கு இல்லாமலும் நிலையைக் காட்டும். இயக்கக்கூடிய கோரிக்கைகளுடன் "
            "API சுற்று /demo-வில் உள்ளது."
        ),
    },
    "te": {
        "start": "జడ్జ్ మోడ్ · 3 నిమిషాల పర్యటన",
        "label": "జడ్జ్ వాక్‌త్రూ · {current}/{total}",
        "back": "వెనుకకు",
        "next": "తదుపరి",
        "finish": "ముగించు",
        "close": "వాక్‌త్రూ మూసివేయి",

        "problemTitle": "సమస్య",
        "problemBody": (
            "షెడ్యూల్డ్ కులాల వ్యాపారికి రెండు ప్రశ్నలకు సులభంగా సమాధానం దొరకదు: ఏ ప్రభుత్వ "
            "రుణ పథకం నాకు సరిపోతుంది, దగ్గరలోని 100+ ఛానల్ పార్టనర్లలో ఆ పథకాన్ని ఎవరు "
            "నిర్వహించడానికి అధికారం కలిగి ఉన్నారు. ఇప్పుడు వారు ఊహిస్తున్నారు."
        ),
        "problemTip": (
            "మొత్తం ప్రయాణం ఖాతా లేకుండానే పనిచేస్తుంది. “మీ అర్హత చూడండి” అనేదే ప్రవేశ ద్వారం."
        ),

        "intakeTitle": "నాలుగు దశలు, ప్రతి దశలోనూ భద్రం",
        "intakeBody": (
            "ప్రతి దశ దాటగానే భద్రపరచబడుతుంది, కాబట్టి 2G లో సిగ్నల్ పోతే ఒక స్క్రీన్ మాత్రమే "
            "పోతుంది, మొత్తం ఫారం కాదు."
        ),
        "intakeTip": (
            "దశ 1 ను నియమాలు చదువుతాయి. దశ 2 ను పార్టనర్ అధికారి చదువుతారు — అది నిర్ణయాన్ని "
            "ఎప్పుడూ మార్చలేదు."
        ),

        "dashboardTitle": "ప్రతి సంఖ్యా నిజమైన డేటాబేస్ నుండి",
        "dashboardBody": (
            "ప్రొఫైల్ పూర్తి, ఉత్తమ సరిపోలిక, ఇంకా ఎంత అప్పు కావాలి, దరఖాస్తు ఎక్కడ ఉంది."
        ),
        "dashboardTip": (
            "ఇక్కడ ఏదీ కల్పితం కాదు. డెమో ముందు సీడ్ స్క్రిప్ట్‌లు ప్రతి స్క్రీన్‌ను Postgres "
            "నుండి నింపుతాయి."
        ),

        "verdictTitle": "నిర్ణయం తీసుకునేది ఒక నిర్దిష్ట నియమ ఇంజిన్",
        "verdictBody": (
            "మోడల్ కాదు. అదే ప్రొఫైల్, అదే రూల్ ప్యాక్ ప్రతిసారీ సరిగ్గా ఒకే ఫలితాన్ని ఇస్తాయి, "
            "ప్యాక్‌కు వెర్షన్ ఉంది."
        ),
        "verdictTip": (
            "ఫలితాల కింది వరుస, వాటిని రూపొందించిన ఇంజిన్ వెర్షన్‌ను, రూల్-ప్యాక్ హాష్‌ను చెబుతుంది."
        ),

        "explainTitle": "ప్రతి నిర్ణయం తన నియమాన్ని చెబుతుంది",
        "explainBody": (
            "ప్రతి ఫలితంలో matched_because[] మరియు blocked_because[] ఉంటాయి, ప్రతిదానిలో "
            "నియమ ఐడీ ఉంటుంది. పథకం సరిపోని చోట, అవసరానికి ఎదురుగా తేడా చూపబడుతుంది."
        ),
        "explainTip": (
            "ఏ కార్డు మీదైనా “అర్హత చూడండి” తెరిచి, ఆపై ఆగిపోయిన పథకంపై “ఈ పథకం ఎందుకు కాదు?” చూడండి."
        ),

        "calculatorTitle": "వాయిదాలు ఎంత అవుతాయి",
        "calculatorBody": (
            "మారటోరియంతో EMI, మొత్తం కాలంలో అసలు వర్సెస్ వడ్డీ, మరియు పౌరుడు ముద్రించి "
            "శాఖకు తీసుకెళ్లగలిగే తిరిగి చెల్లింపు ప్రణాళిక."
        ),
        "calculatorTip": (
            "రేట్లు రూల్ ప్యాక్ నుండి వస్తాయి, అక్కడ ప్రతి సంఖ్యతో source_url మరియు "
            "last_verified_on ఉంటాయి."
        ),

        "partnersTitle": "డబ్బు నిజంగా ఎక్కడికి చేరుతుంది",
        "partnersBody": (
            "ప్రతి పిన్ PostGIS రిజిస్ట్రీ నుండి దాని స్వంత అక్షాంశ-రేఖాంశంలో ఉన్న ఒక శాఖ — "
            "రాష్ట్ర ఛానలైజింగ్ ఏజెన్సీలు, ప్రభుత్వ రంగ బ్యాంకులు, RRB మరియు NBFC-MFI."
        ),
        "partnersTip": (
            "ముఖ్యమైనది లేకపోవడం: బ్యాంకులు ఉండి SCA లేని జిల్లాలో, SCA ద్వారా మాత్రమే వెళ్లే "
            "పథకాలు జరగవు."
        ),

        "assistantTitle": "సహాయకుడు వివరిస్తాడు; ఎప్పుడూ నిర్ణయించడు",
        "assistantBody": (
            "ప్రచురించిన రూల్ ప్యాక్ నుండి, ఇంజిన్ స్వంత నిర్ణయాల నుండి నిర్మించిన సందర్భం "
            "నుండి, పౌరుడి భాషలో సమాధానం ఇస్తుంది, తన సొంత నిర్ణయానికి రాకుండా నియమాలు "
            "నిర్ణయించినదానినే మళ్లీ చెబుతుంది."
        ),
        "assistantTip": (
            "ఏ మోడల్ లేకపోయినా ఇది నిర్దిష్టంగా సమాధానం ఇస్తుంది. మోడల్ మాటలను మెరుగుపరుస్తుంది, "
            "ఎప్పుడూ అనివార్యం కాదు."
        ),

        "applicationTitle": "ఛానల్ పార్టనర్‌కు పంపబడింది",
        "applicationBody": (
            "ముసాయిదా ప్రొఫైల్ నుండి నింపబడుతుంది, పౌరుడు ధృవీకరిస్తాడు, అది ఆ రుణ వర్గానికి "
            "అధికారం ఉన్న పార్టనర్‌కు వెళ్తుంది. SamarthSetu ఎప్పుడూ రుణం ఇవ్వదు."
        ),
        "applicationTip": (
            "రిఫరెన్స్ నంబర్ ఖాతా లేకుండానే స్థితిని చూపుతుంది. అమలు చేయగల అభ్యర్థనలతో API "
            "వాక్‌త్రూ /demo లో ఉంది."
        ),
    },
}

# Both headers now start the walkthrough instead of linking to `/demo`, so the two old
# button labels have no reader left. `/demo` itself is unchanged and is named in the
# last step's tip.
REMOVED = {"nav": ["judgeMode"], "landing": ["judgeMode"]}


def main() -> None:
    for locale, block in JUDGE_TOUR.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        data.setdefault("judgeTour", {}).update(block)

        dropped = 0
        for namespace, keys in REMOVED.items():
            section = data.get(namespace)
            if not isinstance(section, dict):
                continue
            for key in keys:
                if section.pop(key, None) is not None:
                    dropped += 1

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} judgeTour, -{dropped}")


if __name__ == "__main__":
    main()
