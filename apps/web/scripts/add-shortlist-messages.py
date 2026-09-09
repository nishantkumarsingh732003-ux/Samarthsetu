"""One-off: the shortlist card's reminder strings, in all six catalogues.

Kept in the repo, like the other `add-*-messages.py` scripts, as the record of which
strings were added together and in which languages (OPEN_ITEMS OI-4, OI-33).

`reminderHint` is the one a reviewer must not soften. Nothing in this product rings the
reminder — there is no scheduler and no push channel — so the date is handed to the
citizen's own calendar as an .ics file and that is what alerts them. The sentence has to
say so plainly. A translation along the lines of "we will remind you" is not a wording
preference, it is a promise this service cannot keep about a government application
deadline.

    python scripts/add-shortlist-messages.py
"""

from __future__ import annotations

import json
from pathlib import Path

MESSAGES = Path(__file__).resolve().parents[1] / "messages"

SHORTLIST = {
    "en": {
        "title": "My Shortlist",
        "sub": "Schemes you have saved. Set a reminder so you never miss the application window.",
        "upTo": "Up to {amount}",
        "reminder": "Reminder",
        "reminderHint": "Saved on this device. Tap the date to add it to your phone's calendar — that is what will alert you.",
        "open": "View details",
        "apply": "Apply",
        "calendarTitle": "Apply: {scheme}",
        "calendarBody": "You saved this scheme in SamarthSetu. Apply through an authorised Channel Partner.",
    },
    "hi": {
        "title": "मेरी शॉर्टलिस्ट",
        "sub": "आपकी सहेजी हुई योजनाएँ। अनुस्मारक लगाएँ ताकि आवेदन की अवधि न छूटे।",
        "upTo": "{amount} तक",
        "reminder": "अनुस्मारक",
        "reminderHint": "इसी डिवाइस पर सहेजा गया। तारीख़ दबाकर इसे अपने फ़ोन के कैलेंडर में जोड़ें — वही आपको याद दिलाएगा।",
        "open": "विवरण देखें",
        "apply": "आवेदन करें",
        "calendarTitle": "आवेदन: {scheme}",
        "calendarBody": "आपने यह योजना SamarthSetu में सहेजी थी। किसी अधिकृत चैनल पार्टनर के माध्यम से आवेदन करें।",
    },
    "mr": {
        "title": "माझी शॉर्टलिस्ट",
        "sub": "तुम्ही जतन केलेल्या योजना. स्मरणपत्र लावा म्हणजे अर्जाची मुदत चुकणार नाही.",
        "upTo": "{amount} पर्यंत",
        "reminder": "स्मरणपत्र",
        "reminderHint": "याच उपकरणावर जतन केले. तारीख दाबून ती तुमच्या फोनच्या कॅलेंडरमध्ये जोडा — तेच तुम्हाला आठवण करून देईल.",
        "open": "तपशील पाहा",
        "apply": "अर्ज करा",
        "calendarTitle": "अर्ज: {scheme}",
        "calendarBody": "तुम्ही ही योजना SamarthSetu मध्ये जतन केली होती. अधिकृत चॅनेल भागीदारामार्फत अर्ज करा.",
    },
    "bn": {
        "title": "আমার শর্টলিস্ট",
        "sub": "আপনার সংরক্ষিত প্রকল্প। একটি রিমাইন্ডার দিন যাতে আবেদনের সময় হাতছাড়া না হয়।",
        "upTo": "{amount} পর্যন্ত",
        "reminder": "রিমাইন্ডার",
        "reminderHint": "এই ডিভাইসেই সংরক্ষিত। তারিখে চাপ দিয়ে সেটি আপনার ফোনের ক্যালেন্ডারে যোগ করুন — সেটিই আপনাকে মনে করিয়ে দেবে।",
        "open": "বিবরণ দেখুন",
        "apply": "আবেদন করুন",
        "calendarTitle": "আবেদন: {scheme}",
        "calendarBody": "আপনি এই প্রকল্পটি SamarthSetu-তে সংরক্ষণ করেছিলেন। অনুমোদিত চ্যানেল পার্টনারের মাধ্যমে আবেদন করুন।",
    },
    "ta": {
        "title": "எனது சுருக்கப் பட்டியல்",
        "sub": "நீங்கள் சேமித்த திட்டங்கள். விண்ணப்பக் காலம் தவறாமல் இருக்க நினைவூட்டல் வையுங்கள்.",
        "upTo": "{amount} வரை",
        "reminder": "நினைவூட்டல்",
        "reminderHint": "இந்தச் சாதனத்தில் மட்டுமே சேமிக்கப்பட்டது. தேதியைத் தட்டி உங்கள் தொலைபேசியின் நாள்காட்டியில் சேருங்கள் — அதுவே உங்களுக்கு நினைவூட்டும்.",
        "open": "விவரங்களைப் பார்க்க",
        "apply": "விண்ணப்பிக்க",
        "calendarTitle": "விண்ணப்பம்: {scheme}",
        "calendarBody": "இத்திட்டத்தை நீங்கள் SamarthSetu-இல் சேமித்தீர்கள். அங்கீகரிக்கப்பட்ட சேனல் பங்குதாரர் வழியாக விண்ணப்பியுங்கள்.",
    },
    "te": {
        "title": "నా షార్ట్‌లిస్ట్",
        "sub": "మీరు సేవ్ చేసిన పథకాలు. దరఖాస్తు గడువు తప్పిపోకుండా రిమైండర్ పెట్టుకోండి.",
        "upTo": "{amount} వరకు",
        "reminder": "రిమైండర్",
        "reminderHint": "ఈ పరికరంలోనే సేవ్ అయింది. తేదీని నొక్కి మీ ఫోన్ క్యాలెండర్‌లో చేర్చండి — అదే మీకు గుర్తు చేస్తుంది.",
        "open": "వివరాలు చూడండి",
        "apply": "దరఖాస్తు చేయండి",
        "calendarTitle": "దరఖాస్తు: {scheme}",
        "calendarBody": "మీరు ఈ పథకాన్ని SamarthSetu లో సేవ్ చేశారు. అధీకృత ఛానెల్ భాగస్వామి ద్వారా దరఖాస్తు చేయండి.",
    },
}

# The card now leads with the agency, the ceiling and the verdict; the three-figure grid
# it used to carry is gone, and so are the labels that only that grid used.
#
# `compare`/`compareHint` went with the bar at the foot of the page. /compare is still
# reachable — from the catalogue header and from the matches page — so the route did not
# lose its way in, only its second one. `schemeCatalogue.compare` is a different key and
# stays. A key no screen reads is a key a reviewer has to go looking for.
REMOVED = ["maxLoan", "partners", "noVerdict", "compare", "compareHint"]


def main() -> None:
    for locale, block in SHORTLIST.items():
        path = MESSAGES / f"{locale}.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        shortlist = data.setdefault("shortlist", {})
        shortlist.update(block)
        dropped = [key for key in REMOVED if shortlist.pop(key, None) is not None]

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{locale}: +{len(block)} shortlist, -{len(dropped)}")


if __name__ == "__main__":
    main()
