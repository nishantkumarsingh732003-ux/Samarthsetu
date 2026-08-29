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
