/**
 * The seeded demo persona, as the sign-in page needs to name it.
 *
 * The button that loads this account has to say whose account it is *before* anyone is
 * signed in, so it cannot ask the API — the facts have to live in the client bundle. That
 * makes them the same kind of hazard as the scheme ceilings in `schemeFacts.ts`: a copy of
 * data whose real home is elsewhere. So they are pinned the same way, by
 * `demoAccount.test.ts`, against `apps/api/app/services/citizen_accounts.py`, which is
 * where `DEMO_CITIZEN` and `DEMO_PROFILE` are actually defined.
 *
 * Rahul Kumar is not a stand-in for a real person and not a beneficiary of anything. He is
 * a set of answers chosen to land inside the published ceilings — income under Rs 5,00,000,
 * a project cost a Term Loan covers and Micro Finance does not — so that a reviewer sees
 * the engine *distinguish* the scheme families rather than agree with everything.
 */

export const DEMO_ACCOUNT = {
  /** Proper nouns. Not translated, in any locale. */
  name: "Rahul Kumar",
  district: "Jaipur",
  /** The category code the rule engine matches on, shown verbatim as it is everywhere. */
  category: "SC",
} as const;
