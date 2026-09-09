/**
 * Typed client for the optional citizen account, the scheme catalogue and partner
 * coverage.
 *
 * Same contract as `lib/api.ts`: every call returns a typed `ApiResult` rather than
 * throwing, because on this audience's connection a failed request is normal operation
 * and not an exception. The extra error here is `"unauthorised"` — a token that has
 * expired or been revoked, which the UI answers by sending the citizen to sign in
 * rather than by showing them a stack of red text.
 *
 * Nothing in this file is required to check eligibility. The anonymous journey in
 * `lib/api.ts` remains the front door; this is the layer that remembers.
 */
import { apiBase } from "@/lib/apiBase";

import type { ApiResult, MatchResult, NextQuestion } from "@/lib/api";
import type { Locale } from "@/i18n/config";

const BASE = () => apiBase();

/** Where the bearer token lives. Versioned so a shape change can invalidate it. */
export const TOKEN_KEY = "setu.token.v1";

export function readToken(): string | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY);
  } catch {
    // Private mode and blocked site data throw on access, not on use.
    return null;
  }
}

export function writeToken(token: string | null): void {
  try {
    if (token === null) window.localStorage.removeItem(TOKEN_KEY);
    else window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // A citizen with site data blocked simply stays signed out for the session. That
    // degrades to the anonymous journey, which works, so it must not throw.
  }
}

export type AuthedResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: "offline" | "server" | "notfound" | "unauthorised" | "conflict"; status?: number; detail?: string };

async function request<T>(
  path: string,
  init: RequestInit & { auth?: boolean } = {},
): Promise<AuthedResult<T>> {
  const { auth = true, headers, ...rest } = init;
  const token = auth ? readToken() : null;

  try {
    const response = await fetch(`${BASE()}${path}`, {
      ...rest,
      headers: {
        ...(rest.body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
    });

    if (response.status === 401 || response.status === 403) {
      return { ok: false, error: "unauthorised", status: response.status };
    }
    if (response.status === 404) return { ok: false, error: "notfound", status: 404 };
    if (response.status === 409) {
      return { ok: false, error: "conflict", status: 409, detail: await detailOf(response) };
    }
    if (!response.ok) {
      return { ok: false, error: "server", status: response.status, detail: await detailOf(response) };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, error: "offline" };
  }
}

/** The API's own message, when it has one worth showing. */
async function detailOf(response: Response): Promise<string | undefined> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return typeof body.detail === "string" ? body.detail : undefined;
  } catch {
    return undefined;
  }
}

// --- account ------------------------------------------------------------------------

export interface CitizenProfile {
  display_name: string | null;
  preferred_language: string;
  district: string | null;
  state: string | null;
  city: string | null;
  pincode: string | null;

  category: "SC" | "ST" | "OBC" | "GENERAL" | null;
  sub_category: string | null;
  gender: "FEMALE" | "MALE" | "OTHER" | "UNDISCLOSED" | null;
  age: number | null;
  annual_family_income: number | null;
  occupation_type: string | null;
  education_level: string | null;
  existing_loans: number | null;
  project_cost: number | null;
  project_sector: string | null;
  is_pwd: boolean | null;
  is_safai_karamchari: boolean | null;
  has_caste_certificate: boolean | null;
  admission_confirmed: boolean | null;
  course_start_date: string | null;

  business_name: string | null;
  business_description: string | null;
  business_status: "NEW" | "EXISTING" | null;
  own_contribution: number | null;
  loan_required: number | null;

  completed: boolean;
  completion_pct: number;
  /** The exact dictionary handed to the rule engine. Shown, not hidden. */
  engine_profile: Record<string, unknown>;
}

export interface CitizenAccount {
  id: string;
  email: string;
  display_name: string;
  role: string;
  citizen_id: string;
  profile: CitizenProfile;
}

interface TokenResponse {
  access_token: string;
  expires_in_minutes: number;
  user: CitizenAccount;
}

interface LoginResponse {
  access_token: string;
  expires_in_minutes: number;
  user: { id: string; email: string; display_name: string; role: string };
}

export async function signUp(input: {
  email: string;
  password: string;
  displayName: string;
  language: Locale;
}): Promise<AuthedResult<CitizenAccount>> {
  const result = await request<TokenResponse>("/citizen/signup", {
    method: "POST",
    auth: false,
    body: JSON.stringify({
      email: input.email,
      password: input.password,
      display_name: input.displayName,
      preferred_language: input.language,
      // The checkbox the citizen ticked. This call is what records the consent row.
      consent: true,
    }),
  });
  if (!result.ok) return result;
  writeToken(result.data.access_token);
  return { ok: true, data: result.data.user };
}

/** Sign-in is the shared `/auth/login` every role uses; `/citizen/me` then loads the
 *  profile. Two calls rather than one, and worth it: one password path in the API. */
export async function signIn(
  email: string,
  password: string,
): Promise<AuthedResult<CitizenAccount>> {
  const login = await request<LoginResponse>("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, password }),
  });
  if (!login.ok) return login;

  writeToken(login.data.access_token);
  const me = await getAccount();
  if (!me.ok) writeToken(null);
  return me;
}

export function signOut(): void {
  writeToken(null);
}

export function getAccount(): Promise<AuthedResult<CitizenAccount>> {
  return request<CitizenAccount>("/citizen/me");
}

/** A partial update: keys you omit are left alone, an explicit null clears a field. */
export function saveProfile(
  patch: Partial<Record<keyof CitizenProfile, unknown>> & { completed?: boolean },
): Promise<AuthedResult<CitizenAccount>> {
  return request<CitizenAccount>("/citizen/profile", {
    method: "PUT",
    body: JSON.stringify(patch),
  });
}

export function loadDemoProfile(): Promise<AuthedResult<CitizenAccount>> {
  return request<CitizenAccount>("/citizen/profile/demo", { method: "POST" });
}

export interface CitizenMatches {
  match_run_id: string;
  engine_version: string;
  rules_digest: string;
  input_snapshot: Record<string, unknown>;
  results: MatchResult[];
  next_question: NextQuestion | null;
  profile_is_usable: boolean;
}

export function getMatches(language: Locale): Promise<AuthedResult<CitizenMatches>> {
  return request<CitizenMatches>(`/citizen/matches?language=${language}`);
}

export interface CitizenApplication {
  reference_no: string;
  status: string;
  scheme_code: string;
  scheme_name: string;
  family: string;
  partner_name: string | null;
  amount_requested: number | null;
  submitted_at: string | null;
  documents_outstanding: number;
}

export function getMyApplications(): Promise<AuthedResult<CitizenApplication[]>> {
  return request<CitizenApplication[]>("/citizen/applications");
}

/**
 * What this service has actually told the citizen, newest first.
 *
 * The bell in the top bar reads this and nothing else. It is a record of sent messages,
 * not a generated to-do list: `body` is the text as it went out, in the language it went
 * out in, so the feed can be shown to someone who says they were never told. The row
 * carries a masked `recipient_hint` in the database and the API does not project it —
 * see `CitizenNotificationOut`.
 */
export interface CitizenNotification {
  id: string;
  /** The trigger, e.g. `APPLICATION_SUBMITTED`. Stable across template rewrites, which
   *  is what lets the UI choose an icon without parsing the body. */
  event: string;
  channel: string;
  language: string;
  body: string;
  status: string;
  /** Null while queued or after a failed send. The row still exists, and a citizen is
   *  entitled to see that we tried. */
  sent_at: string | null;
  created_at: string;
  application_reference: string | null;
}

export function getMyNotifications(): Promise<AuthedResult<CitizenNotification[]>> {
  return request<CitizenNotification[]>("/citizen/notifications");
}

// --- public catalogue ----------------------------------------------------------------

export interface OpenQuestion {
  field: string;
  question: string;
}

export interface Provenance {
  source: string | null;
  source_url: string | null;
  circular_ref: string | null;
  effective_from: string | null;
  last_verified_on: string | null;
  needs_verification: boolean;
  verification_note: string | null;
  open_questions: OpenQuestion[];
}

export interface SchemeLimits {
  min_project_cost: number | null;
  max_project_cost: number | null;
  max_loan_amount: number | null;
  max_funding_pct: number | null;
  interest_rate_min: number | null;
  interest_rate_max: number | null;
  tenure_months: number | null;
  moratorium_months: number | null;
}

export interface SchemeSummary {
  code: string;
  official_name: string;
  name_gloss: string | null;
  family: string;
  limits: SchemeLimits;
  provenance: Provenance;
  rule_count: number;
  hard_block_count: number;
  authorised_partner_count: number;
  translation_status: string;
}

export interface SchemeRule {
  rule_id: string;
  severity: string;
  when_source: string;
  message: string;
  satisfied_message: string | null;
  suggest_instead: string | null;
  fields: string[];
}

export interface RequiredDocumentSpec {
  id: string;
  name: string;
  why: string;
  issued_by: string | null;
  validity_months: number | null;
  validity_is_practice_not_rule: boolean;
  contains_government_id: boolean;
}

export interface SchemeDetail extends SchemeSummary {
  rules: SchemeRule[];
  required_documents: RequiredDocumentSpec[];
  checklist_digest: string;
}

export interface SchemeCatalogue {
  engine_version: string;
  rules_digest: string;
  language: string;
  schemes: SchemeSummary[];
}

export function getCatalogue(language: Locale): Promise<AuthedResult<SchemeCatalogue>> {
  return request<SchemeCatalogue>(`/schemes?language=${language}`, { auth: false });
}

export function getScheme(
  code: string,
  language: Locale,
): Promise<AuthedResult<SchemeDetail>> {
  return request<SchemeDetail>(
    `/schemes/${encodeURIComponent(code)}?language=${language}`,
    { auth: false },
  );
}

// --- partner coverage ----------------------------------------------------------------

export interface StateCoverage {
  state: string;
  partner_count: number;
  district_count: number;
  by_type: Record<string, number>;
  scheme_codes: string[];
}

export interface DistrictCoverage {
  district: string;
  state: string;
  partner_count: number;
  by_type: Record<string, number>;
  scheme_codes: string[];
}

export interface Coverage {
  states: StateCoverage[];
  total_partners: number;
  data_disclaimer: string;
}

export interface StateDrilldown {
  state: string;
  districts: DistrictCoverage[];
  total_partners: number;
  data_disclaimer: string;
}

export interface DirectoryPartner {
  partner_id: string;
  name: string;
  type: string;
  parent_org: string | null;
  district: string;
  state: string;
  pincode: string | null;
  address: string | null;
  contact: Record<string, unknown>;
  lat: number | null;
  lng: number | null;
  scheme_codes: string[];
  is_accepting: boolean;
}

export interface PartnerDirectory {
  partners: DirectoryPartner[];
  total: number;
  truncated: boolean;
  data_disclaimer: string;
}

export function getCoverage(): Promise<AuthedResult<Coverage>> {
  return request<Coverage>("/partners/coverage", { auth: false });
}

export function getStateCoverage(state: string): Promise<AuthedResult<StateDrilldown>> {
  return request<StateDrilldown>(
    `/partners/coverage/${encodeURIComponent(state)}`,
    { auth: false },
  );
}

export function getDirectory(filters: {
  state?: string;
  district?: string;
  schemeCode?: string;
  q?: string;
}): Promise<AuthedResult<PartnerDirectory>> {
  const query = new URLSearchParams();
  if (filters.state) query.set("state", filters.state);
  if (filters.district) query.set("district", filters.district);
  if (filters.schemeCode) query.set("scheme_code", filters.schemeCode);
  if (filters.q) query.set("q", filters.q);
  const suffix = query.toString();
  return request<PartnerDirectory>(
    `/partners/directory${suffix ? `?${suffix}` : ""}`,
    { auth: false },
  );
}

export type { ApiResult };

// --- the assistant ---------------------------------------------------------------

/** What the assistant may suggest the citizen does next. The client turns each into a
 *  button; an action it cannot render is dropped rather than shown as a dead control. */
export type AssistantAction =
  | "open_scheme"
  | "find_partners"
  | "start_application"
  | "upload_documents"
  | "plan_repayment";

export interface AssistantAnswer {
  answer: string;
  /** Rule ids the answer leans on, so it stays checkable against /schemes. */
  rule_ids: string[];
  action: AssistantAction | null;
  action_scheme_code: string | null;
  /** False when no model was configured and the deterministic reply was used. */
  grounded: boolean;
}

/**
 * Ask a question against the rule pack and this citizen's own record.
 *
 * Distinct from `sendTurn`, which is the *intake*: it extracts facts and advances the
 * profile one question at a time. This one answers. The model never decides
 * eligibility — the verdicts it restates come from the deterministic engine and carry
 * the rule ids that produced them.
 */
export function askAssistant(
  question: string,
  language: Locale,
  /** Recent turns, oldest first, so a follow-up like "and the interest?" resolves. */
  history: { role: "citizen" | "assistant"; text: string }[] = [],
): Promise<AuthedResult<AssistantAnswer>> {
  return request<AssistantAnswer>("/conversation/ask", {
    method: "POST",
    // The API caps this too; trimming here keeps the request small on a 2G connection.
    body: JSON.stringify({ question, language, history: history.slice(-8) }),
  });
}
