export type Ternary = true | false | "UNKNOWN";

export type Node =
  | { op: "and"; args: Node[] }
  | { op: "or"; args: Node[] }
  | { op: "not"; arg: Node }
  | { op: "cmp"; operator: string; left: Node; right: Node }
  | { op: "field"; name: string }
  | { op: "const"; value: string | number | boolean | null }
  | { op: "list"; items: Node[] };

export type Severity = "HARD_BLOCK" | "SOFT_WARN";
export type Family = "MICRO_FINANCE" | "TERM_LOAN" | "EDUCATION_LOAN";
export type Verdict = "ELIGIBLE" | "LIKELY_ELIGIBLE" | "INELIGIBLE" | "NEED_MORE_INFO";

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

export interface Limits {
  /** Eligibility band on what the unit or course may cost. */
  min_project_cost: number | null;
  max_project_cost: number | null;
  /** Ceiling on the loan itself — always use this for the money shown to a citizen. */
  max_loan_amount: number | null;
  max_funding_pct: number | null;
  interest_rate_min: number | null;
  interest_rate_max: number | null;
  tenure_months: number | null;
  moratorium_months: number | null;
}

export interface Rule {
  id: string;
  severity: Severity;
  when: Node;
  when_source: string;
  message_i18n: Record<string, string>;
  satisfied_i18n: Record<string, string>;
  suggest_instead: string | null;
  fields: string[];
}

export interface Scheme {
  code: string;
  official_name: string;
  name_i18n: Record<string, string>;
  family: Family;
  provenance: Provenance;
  limits: Limits;
  rules: Rule[];
}

export interface RuleBundle {
  engine_version: string;
  rules_digest: string;
  schemes: Scheme[];
}

export interface Reason {
  rule_id: string;
  message: string;
  severity: Severity;
}

export interface MatchResult {
  scheme_code: string;
  official_name: string;
  family: Family;
  verdict: Verdict;
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
  provenance: Provenance | null;
  rank: number | null;
}

export interface NextQuestion {
  field: string;
  question_i18n: Record<string, string>;
  kind: string;
  choices: string[] | null;
  resolves_rules: string[];
  resolves_schemes: string[];
}

export interface MatchRun {
  engine_version: string;
  rules_digest: string;
  input_snapshot: Record<string, unknown>;
  results: MatchResult[];
  next_question: NextQuestion | null;
}

export type Profile = Record<string, string | number | boolean | null | undefined>;
