#!/usr/bin/env bash
# generate-secrets.sh
# Generates cryptographically random secrets for a new deployment.
#
# Usage:
#   ./generate-secrets.sh              # writes to .env (asks before overwriting)
#   ./generate-secrets.sh --stdout     # prints to stdout (for piping)
#
# Safe to commit — no secrets leaked.

set -euo pipefail

OUTPUT_FILE=".env"
WRITE_MODE="file"

# Parse flags
for arg in "$@"; do
    case "$arg" in
        --stdout) WRITE_MODE="stdout" ;;
        --help|-h)
            echo "Usage: $0 [--stdout]"
            echo "  (no flag)   Write secrets to .env in current directory"
            echo "  --stdout    Print secrets to stdout (no file write)"
            exit 0
            ;;
    esac
done

if [[ "$WRITE_MODE" == "file" && -f "$OUTPUT_FILE" ]]; then
    read -p "$OUTPUT_FILE already exists. Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Generate secrets
DB_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

OUTPUT=$(cat <<EOF
# WhereInTheWorld — Auto-generated secrets
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Treat these like passwords. Never commit them.

WITW_DB_PASSWORD=${DB_PASS}
WITW_API_KEY=${API_KEY}
EOF
)

if [[ "$WRITE_MODE" == "stdout" ]]; then
    echo "$OUTPUT"
else
    echo "$OUTPUT" > "$OUTPUT_FILE"
    echo "✅ Wrote secrets to $OUTPUT_FILE"
    echo ""
    echo "   Copy these now or store in a password manager:"
    echo "   DB Password: ${DB_PASS}"
    echo "   API Key:     ${API_KEY}"
fi
