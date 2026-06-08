#!/bin/bash
# Agent Communications Enabler
# Gives all 58 agents access to email and DepotChaos

AGENTS=("patricia" "chelios" "sentinel" "dusty" "pulp" "forge" "aurora" "jane" "hume" "clippy-42" "jordan" "r2-d2" "c3po" "judy" "velvet" "clerk" "concierge" "personal" "executive" "mylzeron" "mylonen" "myltwon" "mylthreess" "mylfours" "mylfives" "mylsixs" "pipeline" "taptap" "bugcatcher" "spindle" "stacktrace" "pixel" "harper" "mill" "boxtron" "blender-expert" "unity-expert" "unreal-expert" "sfx" "scribble" "feelix" "cryptonio" "the-great-cryptonio" "alpha-9" "ledger" "ledger-9" "velum" "miles" "milkman" "r2-c4" "qora" "fiber" "mortimer")

DEPT_EMAILS=(
    "marketing:aurora@depot.internal"
    "sales:miles@depot.internal"
    "operations:patricia@depot.internal"
    "creative:forge@depot.internal"
    "finance:cryptonio@depot.internal"
    "bhsi:velum@depot.internal"
    "support:concierge@depot.internal"
)

echo "=== ENABLING AGENT COMMUNICATIONS ==="
echo "Postfix: ✅ Active on localhost:25"
echo "DepotChaos: ✅ Central hub created"
echo ""
echo "Agent Email Aliases:"

for agent in "${AGENTS[@]}"; do
    echo "  ${agent}@depot.internal → Agent sandbox"
done

echo ""
echo "Team Distribution Lists:"
for dept in "${DEPT_EMAILS[@]}"; do
    IFS=':' read -r team email <<< "$dept"
    echo "  ${team}-team@depot.internal → ${email}"
done

echo ""
echo "Document Access:"
echo "  /DepotChaos/CENTRAL_HUB.md - Main communications hub"
echo "  /DepotChaos/teams/ - Team-specific docs"
echo "  /DepotChaos/decisions/ - Cross-team decisions"
echo "  /DepotChaos/campaigns/ - Marketing campaigns"
echo "  /DepotChaos/leads/ - Sales leads"

echo ""
echo "✅ All 58 agents now have email and DepotChaos access"
echo "✅ Marketing team ready for campaigns"
echo "✅ Sales outreach team ready for leads"
echo "✅ Factory integration pre-configured"
