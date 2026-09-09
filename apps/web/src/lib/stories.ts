/**
 * The three journeys the landing page carousel shows.
 *
 * These are not invented testimonials. They are the three personas
 * `scripts/seed/demo.py` builds the demo world from — same names, same districts, same
 * amounts, same scheme families — and the seed script asserts that the rule engine still
 * routes each of them where it says, so a rule change that broke one of these stories
 * fails the seed rather than leaving a false claim on the front page. The district,
 * category, occupation, amount and scheme on each card are the ones a reviewer will find
 * in the database after `make demo`.
 *
 * What *is* written rather than measured is the sentence each person says. Nobody said
 * it; it is there to explain the journey in a human voice. That is why the section
 * carries an "Illustrative · Demo data" badge in every language, exactly as the design
 * drop did — see `stories.test.ts`, which fails if the badge key goes missing.
 *
 * The quote in the persona's own language is held here rather than in the message
 * catalogues on purpose. It is the source utterance, not a string to be translated six
 * ways: Sunita and Ramesh speak Hindi and Anjali speaks Tamil, and a Bengali reader
 * should see the Tamil line with an English gloss beside it, not a Bengali sentence
 * attributed to a Tamil speaker.
 *
 * Photographs are hotlinked from Wikimedia Commons, CC BY-SA 4.0, credited under the
 * carousel. They are stock images of the trades, not photographs of these people —
 * nobody in them is a beneficiary of anything.
 */

import type { Locale } from "@/i18n/config";

export interface PhotoCredit {
  /** Absolute URL. Wikimedia only serves the widths it has already rendered. */
  url: string;
  width: number;
  height: number;
  author: string;
  license: string;
  licenseUrl: string;
  pageUrl: string;
}

export interface Story {
  /** Message-key suffix: `landing.story<id>Quote`, `landing.story<id>Trade`. */
  id: "sunita" | "ramesh" | "anjali";
  name: string;
  district: string;
  state: string;
  /** Every NSFDC scheme is Scheduled Caste only, so every persona is SC. */
  category: "SC";
  schemeCode: string;
  /** Rupees actually sought, from the seed. Not "disbursed" — none of these is closed. */
  amount: number;
  /** The language this person speaks, and the script the source quote is in. */
  language: Locale;
  quoteNative: string;
  photo: PhotoCredit;
}

export const STORIES: readonly Story[] = [
  {
    id: "sunita",
    name: "Sunita Devi",
    district: "Nagpur",
    state: "Maharashtra",
    category: "SC",
    schemeCode: "NSFDC_MICRO_FINANCE",
    amount: 72000,
    language: "hi",
    quoteNative: "गाड़ी अब मेरी है। उसी महीने साहूकार को देना बंद कर दिया।",
    photo: {
      url: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/An_elderly_woman_selling_vegetables_at_Chanditala_bazaar.jpg/1280px-An_elderly_woman_selling_vegetables_at_Chanditala_bazaar.jpg",
      width: 1280,
      height: 960,
      author: "Billjones94",
      license: "CC BY-SA 4.0",
      licenseUrl: "https://creativecommons.org/licenses/by-sa/4.0",
      pageUrl:
        "https://commons.wikimedia.org/wiki/File:An_elderly_woman_selling_vegetables_at_Chanditala_bazaar.jpg",
    },
  },
  {
    id: "ramesh",
    name: "Ramesh Kumar",
    district: "Patna",
    state: "Bihar",
    category: "SC",
    schemeCode: "NSFDC_TERM_LOAN",
    amount: 1080000,
    language: "hi",
    quoteNative:
      "मैं वही छोटी योजना माँगने गया था जिसकी सब बात करते हैं। इसने बताया कि वह मेरी वर्कशॉप के लिए कम पड़ेगी — और सही वाली का नाम दिया।",
    photo: {
      url: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Skilled_Carpenter_Working_on_Wood_in_a_Workshop.jpg/1280px-Skilled_Carpenter_Working_on_Wood_in_a_Workshop.jpg",
      width: 1280,
      height: 853,
      author: "The open draft",
      license: "CC BY-SA 4.0",
      licenseUrl: "https://creativecommons.org/licenses/by-sa/4.0",
      pageUrl:
        "https://commons.wikimedia.org/wiki/File:Skilled_Carpenter_Working_on_Wood_in_a_Workshop.jpg",
    },
  },
  {
    id: "anjali",
    name: "Anjali R",
    district: "Coimbatore",
    state: "Tamil Nadu",
    category: "SC",
    schemeCode: "NSFDC_EDUCATION_LOAN",
    amount: 540000,
    language: "ta",
    quoteNative:
      "நான் போவதற்கு முன்பே தேவையான ஆவணங்களை வரிசைப்படுத்தியது; கிளையில் திருப்பி அனுப்ப எதுவும் இல்லை.",
    photo: {
      url: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Media_Studies_in_Christ_Nagar_College%2C_Trivandrum%2C_Kerala%2C_India_%282020%29.jpg/1280px-Media_Studies_in_Christ_Nagar_College%2C_Trivandrum%2C_Kerala%2C_India_%282020%29.jpg",
      width: 1280,
      height: 856,
      author: "Juby.eipe",
      license: "CC BY-SA 4.0",
      licenseUrl: "https://creativecommons.org/licenses/by-sa/4.0",
      pageUrl:
        "https://commons.wikimedia.org/wiki/File:Media_Studies_in_Christ_Nagar_College,_Trivandrum,_Kerala,_India_(2020).jpg",
    },
  },
];

/**
 * The worked example in the hero. Ramesh, because he is the one who carries the
 * problem statement: he asked about the scheme everyone has heard of and the engine
 * sent him to the one that actually fits, before he walked anywhere.
 */
export const WORKED_EXAMPLE = STORIES[1];

/** Annual family income on the seeded profile, in rupees. Under the Rs 5,00,000 ceiling. */
export const WORKED_EXAMPLE_INCOME = 420000;
