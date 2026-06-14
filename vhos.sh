#!/usr/bin/env bash
# VHOS v2.4 — Interactive CLI
# Usage: ./vhos.sh

BASE="http://localhost:8000"
SID=""
AUTH="medium"

RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

die() { echo -e "${RED}$1${RESET}" >&2; exit 1; }

check_server() {
    curl -sf "$BASE/health" >/dev/null 2>&1
}

start_server() {
    echo -e "${YELLOW}Starting VHOS server...${RESET}"
    cd "$(dirname "$0")"
    python demo_data/generate.py >/dev/null 2>&1
    nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /tmp/vhos.log 2>&1 &
    echo $! > /tmp/vhos.pid
    for i in $(seq 1 10); do
        sleep 1
        check_server && break
        echo -n "."
    done
    echo ""
    check_server || die "Server failed to start. Check /tmp/vhos.log"
    echo -e "${GREEN}Server started (PID $(cat /tmp/vhos.pid))${RESET}"
}

stop_server() {
    if [ -f /tmp/vhos.pid ]; then
        kill "$(cat /tmp/vhos.pid)" 2>/dev/null && rm /tmp/vhos.pid
        echo -e "${YELLOW}Server stopped.${RESET}"
    else
        echo "No PID file found."
    fi
}

create_session() {
    local level="${1:-medium}"
    local resp
    resp=$(curl -sf -X POST "$BASE/session" \
        -H "Content-Type: application/json" \
        -d "{\"patient_id\":\"UHID-1001\",\"auth_level\":\"$level\"}")
    SID=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
    local greeting
    greeting=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['greeting'])")
    echo -e "\n${CYAN}Session: $SID  [auth: $level]${RESET}"
    echo -e "${GREEN}VHOS:${RESET} $greeting\n"
}

send_message() {
    local msg="$1"
    local resp
    resp=$(curl -sf -X POST "$BASE/session/$SID/message" \
        -H "Content-Type: application/json" \
        -d "{\"message\":$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$msg")}")

    local text agent intent outcome confirm
    text=$(echo "$resp"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('text',''))")
    agent=$(echo "$resp"   | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_id',''))")
    intent=$(echo "$resp"  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('intent',''))")
    outcome=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('outcome',''))")
    confirm=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('requires_confirmation','False'))")

    # Colour outcome
    local oc_color="$GREEN"
    [[ "$outcome" == "escalate" ]] && oc_color="$RED"
    [[ "$outcome" == "error"    ]] && oc_color="$YELLOW"

    echo -e "${CYAN}[${agent} · ${intent} · ${oc_color}${outcome}${CYAN}]${RESET}"
    echo -e "${GREEN}VHOS:${RESET} $text"
    [[ "$confirm" == "True" ]] && echo -e "${YELLOW}⚠  Confirmation required before this takes effect.${RESET}"
    echo ""
}

show_audit() {
    echo -e "\n${BOLD}=== Audit Log ===${RESET}"
    curl -sf "$BASE/session/$SID/audit" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for e in d['entries'][-5:]:
    print(f\"  #{e['seq']}  {e['event_type']:<28} agent={e['agent_id']}\")
"
    echo ""
}

show_agents() {
    echo -e "\n${BOLD}=== Loaded Agents ($(curl -sf $BASE/agents | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))')) total) ===${RESET}"
    curl -sf "$BASE/agents" | python3 -c "
import sys, json
agents = json.load(sys.stdin)
by_pillar = {}
for a in agents:
    by_pillar.setdefault(a['pillar'], []).append(a['agent_id'])
for pillar, ids in sorted(by_pillar.items()):
    print(f'  {pillar}')
    for aid in ids:
        print(f'    · {aid}')
"
    echo ""
}

chat_loop() {
    echo -e "${BOLD}Commands:  /quit  /audit  /agents  /new [auth_level]  /stop${RESET}\n"
    while true; do
        read -r -p "$(echo -e "${BOLD}You:${RESET} ")" input
        [[ -z "$input" ]] && continue
        case "$input" in
            /quit|/exit) echo "Bye."; break ;;
            /audit)      show_audit ;;
            /agents)     show_agents ;;
            /stop)       stop_server; break ;;
            /new*)
                level=$(echo "$input" | awk '{print $2}')
                create_session "${level:-medium}"
                ;;
            /demo)
                echo -e "${YELLOW}Running quick demo...${RESET}"
                send_message "hello"
                send_message "I need to book an appointment"
                send_message "I have severe chest pain"
                send_message "What are the cardiology department timings?"
                ;;
            *) send_message "$input" ;;
        esac
    done
}

main() {
    echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║   VHOS v2.4 — Virtual Hospital OS       ║${RESET}"
    echo -e "${BOLD}║   Graviton Systems · 43 AI Agents        ║${RESET}"
    echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}\n"

    case "${1:-}" in
        stop)   stop_server; exit 0 ;;
        agents) check_server || start_server; show_agents; exit 0 ;;
        demo)
            check_server || start_server
            AUTH="medium"
            create_session "$AUTH"
            send_message "hello"
            send_message "I need to book an appointment with a cardiologist"
            send_message "I have chest pain and I can't breathe"
            send_message "I've been feeling very hopeless and depressed"
            send_message "What is my insurance coverage?"
            show_audit
            exit 0
            ;;
    esac

    check_server || start_server

    echo -e "Auth levels: ${CYAN}none  low  medium  high  provider${RESET}"
    echo -n "Select auth level [medium]: "
    read -r level
    AUTH="${level:-medium}"

    create_session "$AUTH"
    chat_loop
}

main "$@"
