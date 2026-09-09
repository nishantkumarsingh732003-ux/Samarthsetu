/**
 * Console API client and session handling.
 *
 * Separate from `lib/api.ts` on purpose. That file serves the citizen route, which has
 * a hard JS budget and no authentication at all; this one is for signed-in staff on a
 * desk. Keeping them apart means a console dependency can never leak into a citizen
 * bundle.
 *
 * The token lives in `sessionStorage`, not `localStorage`: closing the tab ends the
 * session, which is the right default for a shared branch terminal. It is deliberately
 * not a cookie — there is no CSRF surface to defend if the browser never attaches
 * credentials on its own.
 */
import { apiBase } from "@/lib/apiBase";

// Resolved per call: it depends on `window.location`, absent at module load during SSR.
const BASE = () => apiBase();

const TOKEN_KEY = "setu.console.token";
const USER_KEY = "setu.console.user";

export interface ConsoleUser {
  id: string;
  email: string;
  display_name: string;
  role: "CITIZEN" | "PARTNER" | "ADMIN";
  partner_id: string | null;
  partner_name: string | null;
}

export type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number };

function store(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    // Blocked site data throws on access, not on use.
    return null;
  }
}

export function getToken(): string | null {
  try {
    return store()?.getItem(TOKEN_KEY) ?? null;
  } catch {
    return null;
  }
}

export function getUser(): ConsoleUser | null {
  try {
    const raw = store()?.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as ConsoleUser) : null;
  } catch {
    return null;
  }
}

export function signOut(): void {
  try {
    store()?.removeItem(TOKEN_KEY);
    store()?.removeItem(USER_KEY);
  } catch {
    /* nothing to clear */
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<Result<T>> {
  const token = getToken();
  try {
    const response = await fetch(`${BASE()}${path}`, {
      ...init,
      headers: {
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.headers ?? {}),
      },
    });
    if (!response.ok) {
      let detail = `Request failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: string };
        if (body?.detail) detail = body.detail;
      } catch {
        /* keep the status-code message */
      }
      return { ok: false, error: detail, status: response.status };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, error: "Could not reach the SamarthSetu API." };
  }
}

export async function signIn(email: string, password: string): Promise<Result<ConsoleUser>> {
  const result = await request<{ access_token: string; user: ConsoleUser }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!result.ok) return result;
  try {
    store()?.setItem(TOKEN_KEY, result.data.access_token);
    store()?.setItem(USER_KEY, JSON.stringify(result.data.user));
  } catch {
    // A browser refusing storage still gets a working session for this page load.
  }
  return { ok: true, data: result.data.user };
}

// --- partner console -------------------------------------------------------------

export interface Readiness {
  score: number;
  uploaded: number;
  required: number;
  missing: string[];
  warnings: number;
  unmasked_documents: number;
}

export interface QueueItem {
  reference_no: string;
  status: string;
  scheme_code: string;
  scheme_name: string;
  family: string;
  amount_requested: number | null;
  submitted_at: string | null;
  days_open: number;
  sla_days: number | null;
  sla_state: "ON_TRACK" | "DUE" | "BREACHED" | "UNKNOWN";
  applicant: {
    display_name: string | null;
    gov_id_type: string | null;
    gov_id_last4: string | null;
    phone_last4: string | null;
    district: string | null;
    state: string | null;
    preferred_language: string;
  };
  readiness: Readiness;
  verdict: string | null;
  matched_because: { rule_id: string; message: string; severity: string }[];
  engine_version: string | null;
}

export interface QueueResponse {
  partner_id: string;
  partner_name: string;
  is_currently_accepting: boolean;
  total: number;
  items: QueueItem[];
  counts_by_status: Record<string, number>;
}

export interface CapacityRow {
  scheme_code: string;
  scheme_name: string;
  family: string;
  is_currently_accepting: boolean;
  min_ticket: number | null;
  max_ticket: number | null;
  avg_turnaround_days: number | null;
  active_load: number | null;
}

export interface CapacityResponse {
  partner_id: string;
  partner_name: string;
  rows: CapacityRow[];
}

export function getQueue(status?: string): Promise<Result<QueueResponse>> {
  const query = new URLSearchParams();
  if (status) query.set("status", status);
  return request<QueueResponse>(`/partner/queue${query.size ? `?${query}` : ""}`);
}

export function actOnApplication(
  reference: string,
  action: string,
  reason?: string,
): Promise<Result<QueueItem>> {
  return request<QueueItem>(`/partner/applications/${encodeURIComponent(reference)}/action`, {
    method: "POST",
    body: JSON.stringify({ action, ...(reason ? { reason } : {}) }),
  });
}

export function getCapacity(): Promise<Result<CapacityResponse>> {
  return request<CapacityResponse>("/partner/capacity");
}

export function setCapacity(body: {
  scheme_code?: string;
  is_currently_accepting?: boolean;
  max_ticket?: number;
}): Promise<Result<CapacityResponse>> {
  return request<CapacityResponse>("/partner/capacity", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

// --- admin dashboard -------------------------------------------------------------

export interface Analytics {
  generated_at: string;
  engine_version: string;
  funnel: {
    stages: {
      stage: string;
      label: string;
      count: number;
      conversion_from_previous: number | null;
    }[];
    largest_drop_off: string | null;
    largest_drop_off_pct: number | null;
  };
  misrouting: {
    redirects_suggested: number;
    partners_filtered_for_authorisation: number;
    partners_filtered_for_distance: number;
    partners_filtered_for_ticket_size: number;
    routing_calls: number;
    total_prevented: number;
  };
  coverage: {
    radius_km: number;
    districts_with_demand: number;
    underserved: {
      district: string;
      state: string;
      demand: number;
      partners_within_25km: number;
      nearest_authorised_km: number | null;
      families_unserved: string[];
    }[];
    points: Record<string, unknown>[];
  };
  scheme_mix: { key: string; label: string; count: number; share: number }[];
  language_mix: { key: string; label: string; count: number; share: number }[];
  status_mix: { key: string; label: string; count: number; share: number }[];
  turnaround: {
    partner_type: string;
    applications: number;
    median_days: number | null;
    p90_days: number | null;
  }[];
}

export function getAnalytics(): Promise<Result<Analytics>> {
  return request<Analytics>("/admin/analytics");
}

/** Fetches with the bearer token, then hands the browser a Blob — an <a href> cannot
 *  carry an Authorization header, so a plain link would 401. */
export async function downloadCsv(section: string): Promise<string | null> {
  const token = getToken();
  try {
    const response = await fetch(`${BASE()}/admin/export.csv?section=${section}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) return `Export failed (${response.status})`;
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `setu-${section}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    return null;
  } catch {
    return "Could not reach the SamarthSetu API.";
  }
}
