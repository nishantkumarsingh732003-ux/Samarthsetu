#!/usr/bin/env bash
# Prove that SamarthSetu degrades rather than dies.
#
# The claim under test is CLAUDE.md rule 1, stated as an operational property rather
# than an architectural intention: eligibility is decided by a deterministic rule
# engine, so taking the language model away must change the *wording* a citizen sees
# and nothing else. Same verdict, same rule IDs, same reference number.
#
# This is not a mock. It points the running API at a provider that does not exist,
# drives a complete citizen journey through the real HTTP surface, and compares the
# verdict against a baseline captured moments earlier with the model configured.
#
#   ./scripts/chaos.sh              # kill the LLM, run the journey, restore
#   ./scripts/chaos.sh --keep-down  # leave it broken so you can poke at it
#
# Exit code 0 means the flow completed with the model down.

set -euo pipefail

API="${API:-http://localhost:8000}"
COMPOSE="${COMPOSE:-docker compose}"
KEEP_DOWN=0
[[ "${1:-}" == "--keep-down" ]] && KEEP_DOWN=1

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$1"; }
step() { printf '\n\033[1m%s\033[0m\n' "$1"; }

FAILURES=0
check() { if [[ "$1" == "$2" ]]; then ok "$3"; else bad "$3 (expected '$2', got '$1')"; FAILURES=$((FAILURES + 1)); fi; }

# One place that knows how to talk to the API, so the journey below reads as a journey.
api() {
  local method="$1" path="$2" body="${3:-}"
  if [[ -n "$body" ]]; then
    curl -sS -X "$method" "$API$path" -H 'Content-Type: application/json' -d "$body"
  else
    curl -sS -X "$method" "$API$path"
  fi
}

jqp() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

bold "SamarthSetu chaos drill — does the service survive losing its language model?"
printf 'API: %s\n' "$API"

# --- 0. the service must be up before we can meaningfully break it -----------------
step "0. Preflight"
if ! curl -sSf "$API/health" >/dev/null 2>&1; then
  bad "API is not responding at $API. Run 'docker compose up -d' first."
  exit 1
fi
ok "API is up"

PROFILE='{"category":"SC","project_sector":"TRADE","annual_family_income":180000,"project_cost":80000}'

# --- 1. baseline, with whatever provider is configured ------------------------------
step "1. Baseline — the verdict with the model as configured"
BASELINE=$(api POST /api/v1/match "{\"profile\":$PROFILE,\"language\":\"hi\"}")
BASE_SCHEME=$(printf '%s' "$BASELINE" | jqp "d['results'][0]['scheme_code']")
BASE_VERDICT=$(printf '%s' "$BASELINE" | jqp "d['results'][0]['verdict']")
BASE_RULES=$(printf '%s' "$BASELINE" | jqp "','.join(r['rule_id'] for r in d['results'][0]['matched_because'])")
BASE_ENGINE=$(printf '%s' "$BASELINE" | jqp "d['engine_version']")
BASE_DIGEST=$(printf '%s' "$BASELINE" | jqp "d['rules_digest']")
printf '  %s / %s (engine %s, rules %s)\n' "$BASE_SCHEME" "$BASE_VERDICT" "$BASE_ENGINE" "$BASE_DIGEST"
printf '  rules fired: %s\n' "$BASE_RULES"

# --- 2. kill it ----------------------------------------------------------------------
step "2. Killing the language model"
# Pointed at a black hole rather than merely disabled: 'none' is a supported
# configuration and would prove only that the off switch works. A base URL that does
# not resolve exercises the connect-failure and timeout path a real outage produces.
#
# Settings are read at import, so the outage is applied by recreating the container
# with a broken provider in its environment.
LLM_PROVIDER=groq \
GROQ_API_KEY=chaos-not-a-real-key \
GROQ_BASE_URL=http://127.0.0.1:9/v1 \
LLM_TIMEOUT_SECONDS=2 \
  $COMPOSE up -d --force-recreate api >/dev/null 2>&1
ok "API restarted pointing at an unreachable model endpoint"

printf '  waiting for the API to come back'
for _ in $(seq 1 45); do
  if curl -sSf "$API/health" >/dev/null 2>&1; then printf ' up\n'; break; fi
  printf '.'; sleep 2
done

READY=$(api GET /readyz)
printf '  readyz: %s\n' "$(printf '%s' "$READY" | jqp "json.dumps(d['checks'])")"

# --- 3. the journey, with the model down ---------------------------------------------
step "3. A full citizen journey, model down"

MATCH=$(api POST /api/v1/match "{\"profile\":$PROFILE,\"language\":\"hi\"}")
SCHEME=$(printf '%s' "$MATCH" | jqp "d['results'][0]['scheme_code']")
VERDICT=$(printf '%s' "$MATCH" | jqp "d['results'][0]['verdict']")
RULES=$(printf '%s' "$MATCH" | jqp "','.join(r['rule_id'] for r in d['results'][0]['matched_because'])")
DIGEST=$(printf '%s' "$MATCH" | jqp "d['rules_digest']")
RUN_ID=$(printf '%s' "$MATCH" | jqp "d['match_run_id']")

check "$SCHEME"  "$BASE_SCHEME"  "Same scheme matched"
check "$VERDICT" "$BASE_VERDICT" "Same verdict"
check "$RULES"   "$BASE_RULES"   "Same rules fired, in the same order"
check "$DIGEST"  "$BASE_DIGEST"  "Same rules digest — policy did not shift"

# The conversational path is the one that actually calls the model.
TURN=$(api POST /api/v1/conversation/turn \
  '{"utterance":"mujhe sabzi ka thela lagana hai, 80 hazaar chahiye","language":"hi"}')
LLM_USED=$(printf '%s' "$TURN" | jqp "d['extraction']['llm_used']")
STAGE=$(printf '%s' "$TURN" | jqp "d['stage']")
check "$LLM_USED" "False" "Extraction fell back to the deterministic reader"
[[ -n "$STAGE" ]] && ok "Conversation still advanced (stage: $STAGE)"

# The feature-phone channel too.
WA=$(api POST /api/v1/webhook/whatsapp \
  '{"simulate":true,"sender":"chaos-drill","text":"mujhe sabzi ka thela lagana hai","language":"hi"}')
WA_TEXT=$(printf '%s' "$WA" | jqp "d['text'][:60]")
[[ -n "$WA_TEXT" ]] && ok "WhatsApp channel still replies: ${WA_TEXT}..."

ROUTE=$(api POST /api/v1/partners/route \
  "{\"scheme_code\":\"$SCHEME\",\"amount\":72000,\"district\":\"Nagpur\",\"match_run_id\":\"$RUN_ID\"}")
PARTNER=$(printf '%s' "$ROUTE" | jqp "d['partners'][0]['partner_id']")
PARTNER_NAME=$(printf '%s' "$ROUTE" | jqp "d['partners'][0]['name']")
[[ -n "$PARTNER" ]] && ok "Routing still works: $PARTNER_NAME"

APP=$(api POST /api/v1/applications "{
  \"scheme_code\":\"$SCHEME\",\"partner_id\":\"$PARTNER\",\"amount_requested\":72000,
  \"match_run_id\":\"$RUN_ID\",
  \"applicant\":{\"display_name\":\"Chaos Drill\",\"district\":\"Nagpur\",\"state\":\"Maharashtra\",\"preferred_language\":\"hi\"},
  \"consent\":{\"granted\":true},\"language\":\"hi\"}")
REF=$(printf '%s' "$APP" | jqp "d['reference_no']")
if [[ -n "$REF" && "$REF" != "None" ]]; then ok "Application submitted: $REF"; else bad "No reference number issued"; FAILURES=$((FAILURES + 1)); fi

TRACK=$(api GET "/api/v1/applications/$REF")
TRACK_STATUS=$(printf '%s' "$TRACK" | jqp "d['status']")
check "$TRACK_STATUS" "SUBMITTED" "Tracking page renders"

# The notification is written by the same transition that issued the reference.
NOTES=$($COMPOSE exec -T postgres psql -U "${POSTGRES_USER:-saarthi}" -d "${POSTGRES_DB:-saarthi}" -A -t \
  -c "select count(*) from notifications where context->>'ref' = '$REF';" 2>/dev/null | tr -d '[:space:]')
if [[ "${NOTES:-0}" -ge 1 ]]; then ok "Citizen was notified ($NOTES message)"; else bad "No notification written"; FAILURES=$((FAILURES + 1)); fi

# --- 4. restore -----------------------------------------------------------------------
if [[ $KEEP_DOWN -eq 0 ]]; then
  step "4. Restoring the model"
  $COMPOSE up -d --force-recreate api >/dev/null 2>&1
  for _ in $(seq 1 45); do curl -sSf "$API/health" >/dev/null 2>&1 && break; sleep 2; done
  ok "API restarted with the configured provider"
else
  step "4. Leaving the model down (--keep-down)"
  printf '  Restore with: %s up -d --force-recreate api\n' "$COMPOSE"
fi

# --- verdict ---------------------------------------------------------------------------
printf '\n'
if [[ $FAILURES -eq 0 ]]; then
  bold "PASS — the core service degrades, it does not die."
  printf 'The language model was unreachable for every call above. The verdict, the rule\n'
  printf 'IDs and the rules digest were byte-identical to the baseline, because no model\n'
  printf 'was ever involved in deciding them. Only the wording changes.\n'
  exit 0
fi
bold "FAIL — $FAILURES check(s) did not hold."
exit 1
