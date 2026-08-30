/**
 * Thin client for the SETU API.
 *
 * Every call is wrapped so a network failure surfaces as a typed result rather than a
 * thrown error the UI has to guess at. On a 2G connection and a Rs 6,000 phone, requests
 * failing is normal operation, not an exception.
 */
import type { Locale } from "@/i18n/config";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface Reason {
  rule_id: string;
  message: string;
  severity: string;
}

export interface MatchResult {
  scheme_code: string;
  official_name: string;
  family: string;
  verdict: "ELIGIBLE" | "LIKELY_ELIGIBLE" | "INELIGIBLE" | "NEED_MORE_INFO";
  confidence: number;
  matched_because: Reason[];
  blocked_because: Reason[];
  warnings: Reason[];
  missing_fields: string[];
  indicative_amount: number | null;
  indicative_interest_band: [number, number] | null;
  max_funding_pct: number | null;
  redirect_suggestion: string | null;
  needs_verification: boolean;
  rank: number | null;
  translation_status: string;
}

export interface NextQuestion {
  field: string;
  question_i18n: Record<string, string>;
  kind: string;
  choices: string[] | null;
  resolves_rules: string[];
  resolves_schemes: string[];
}

export interface Explanation {
  scheme_code: string;
  verdict: string;
  rule_ids: string[];
  language: string;
  explanation: string;
  source: "llm" | "template";
}

export interface TurnResponse {
  session_id: string;
  language: string;
  stage: "ASKING" | "CONFIRMING" | "DECIDED" | "QUESTION_LIMIT_REACHED";
  question: string | null;
  question_field: string | null;
  question_choices?: string[] | null;
  questions_asked: number;
  max_questions: number;
  profile: Record<string, unknown>;
  context?: Record<string, unknown>;
  extraction: {
    accepted: { field: string; value: unknown; confidence: number }[];
    needs_confirmation: { field: string; value: unknown; confidence: number }[];
    llm_used: boolean;
  };
  results: MatchResult[] | null;
  explanations?: Explanation[] | null;
  match_run_id?: string | null;
}

export interface ScoreComponent {
  value: unknown;
  unit: string;
  score: number;
  weight: number;
  contribution: number;
}

export interface RoutedPartner {
  partner_id: string;
  name: string;
  type: string;
  district: string;
  state: string;
  contact: Record<string, unknown>;
  lat: number | null;
  lng: number | null;
  distance_km: number | null;
  avg_turnaround_days: number | null;
  active_load: number | null;
  score: number;
  score_breakdown: Record<string, ScoreComponent>;
  rank: number | null;
}

export interface WhyNot {
  partner_id: string;
  name: string;
  type: string;
  district: string;
  distance_km: number | null;
  reason_code: string;
  reason: string;
}

export interface RouteResponse {
  routing_version: string;
  scheme_code: string;
  scheme_name: string;
  amount_requested: number;
  origin: { lat: number; lng: number } | null;
  weights: Record<string, number>;
  candidates_considered: number;
  eligible_partner_count: number;
  partners: RoutedPartner[];
  why_not: WhyNot[];
  data_disclaimer: string;
  cached: boolean;
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: "offline" | "server" | "notfound"; status?: number };

async function post<T>(path: string, body: unknown): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (response.status === 404) return { ok: false, error: "notfound", status: 404 };
    if (!response.ok) return { ok: false, error: "server", status: response.status };
    return { ok: true, data: (await response.json()) as T };
  } catch {
    // fetch only rejects on a network-level failure, which on this audience's
    // connection means "offline" far more often than it means "broken".
    return { ok: false, error: "offline" };
  }
}

export function sendTurn(
  utterance: string,
  language: Locale,
  sessionId: string | null,
): Promise<ApiResult<TurnResponse>> {
  return post<TurnResponse>("/conversation/turn", {
    utterance,
    language,
    ...(sessionId ? { session_id: sessionId } : {}),
  });
}

export function routePartners(input: {
  schemeCode: string;
  amount: number;
  lat?: number;
  lng?: number;
  district?: string;
}): Promise<ApiResult<RouteResponse>> {
  return post<RouteResponse>("/partners/route", {
    scheme_code: input.schemeCode,
    amount: input.amount,
    ...(input.lat !== undefined ? { lat: input.lat } : {}),
    ...(input.lng !== undefined ? { lng: input.lng } : {}),
    ...(input.district ? { district: input.district } : {}),
  });
}

// --- applications and documents (Phase 5) -----------------------------------------

export interface RequiredDocument {
  id: string;
  name: string;
  why: string;
  issued_by: string | null;
  validity_months: number | null;
  /** True where the window is common partner practice, not a published rule. */
  validity_is_practice_not_rule: boolean;
  contains_government_id: boolean;
  uploaded: boolean;
}

export interface DocumentWarning {
  code: string;
  message: string;
}

export interface UploadedDocument {
  id: string;
  doc_type: string;
  validation_status: "PENDING" | "PASSED" | "WARNING" | "FAILED";
  redaction_applied: boolean;
  warnings: DocumentWarning[];
  detected_type: string | null;
  uploaded_at: string | null;
}

export interface TimelineEntry {
  status: string;
  actor: string;
  at: string;
  reason: string | null;
}

export interface ApplicationResponse {
  reference_no: string;
  status: string;
  scheme_code: string;
  scheme_name: string;
  family: string;
  partner: {
    id: string;
    name: string;
    type: string;
    address: string | null;
    district: string;
    state: string;
    contact: Record<string, unknown>;
  } | null;
  amount_requested: number | null;
  submitted_at: string | null;
  engine_version: string | null;
  match_run_id: string | null;
  timeline: TimelineEntry[];
  documents: UploadedDocument[];
  required_documents: RequiredDocument[];
  documents_outstanding: number;
  checklist_needs_verification: boolean;
}

export interface ChecklistResponse {
  family: string;
  partner_type: string | null;
  language: string;
  documents: RequiredDocument[];
  checklist_digest: string;
  needs_verification: boolean;
  verification_note: string | null;
}

export interface DocumentUploadResponse {
  document: UploadedDocument;
  extract: Record<string, unknown>;
  masked_ids: { id_type: string; last4: string; salted_hash: string }[];
}

async function get<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${BASE}${path}`);
    if (response.status === 404) return { ok: false, error: "notfound", status: 404 };
    if (!response.ok) return { ok: false, error: "server", status: response.status };
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, error: "offline" };
  }
}

export function submitApplication(input: {
  schemeCode: string;
  partnerId?: string;
  amount?: number;
  matchRunId?: string | null;
  language: Locale;
  applicant: {
    display_name?: string;
    phone?: string;
    gov_id_type?: "AADHAAR" | "PAN" | "VOTER_ID" | "OTHER";
    gov_id?: string;
    district?: string;
    state?: string;
  };
}): Promise<ApiResult<ApplicationResponse>> {
  return post<ApplicationResponse>("/applications", {
    scheme_code: input.schemeCode,
    ...(input.partnerId ? { partner_id: input.partnerId } : {}),
    ...(input.amount ? { amount_requested: input.amount } : {}),
    ...(input.matchRunId ? { match_run_id: input.matchRunId } : {}),
    applicant: { ...input.applicant, preferred_language: input.language },
    // The citizen ticked the box on the previous screen; this call is what records it.
    consent: { granted: true },
    language: input.language,
  });
}

export function getApplication(
  reference: string,
  language: Locale,
): Promise<ApiResult<ApplicationResponse>> {
  return get<ApplicationResponse>(
    `/applications/${encodeURIComponent(reference)}?language=${language}`,
  );
}

export function getChecklist(
  family: string,
  language: Locale,
  partnerType?: string,
): Promise<ApiResult<ChecklistResponse>> {
  const query = new URLSearchParams({ family, language });
  if (partnerType) query.set("partner_type", partnerType);
  return get<ChecklistResponse>(`/documents/checklist?${query.toString()}`);
}

export async function uploadDocument(
  reference: string,
  docType: string,
  file: File,
  validityMonths?: number | null,
): Promise<ApiResult<DocumentUploadResponse>> {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  if (validityMonths) form.append("validity_months", String(validityMonths));
  try {
    const response = await fetch(
      `${BASE}/applications/${encodeURIComponent(reference)}/documents`,
      { method: "POST", body: form },
    );
    if (response.status === 404) return { ok: false, error: "notfound", status: 404 };
    if (!response.ok) return { ok: false, error: "server", status: response.status };
    return { ok: true, data: (await response.json()) as DocumentUploadResponse };
  } catch {
    return { ok: false, error: "offline" };
  }
}
