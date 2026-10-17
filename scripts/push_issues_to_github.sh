#!/usr/bin/env bash
# Push all structured issue files in .github/issues/ to GitHub repository using gh CLI.

set -e

echo "=================================================="
echo "  SupportIQ - GitHub Issues Synchronization Tool  "
echo "=================================================="

# Check gh command
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI ('gh') is not installed. Visit https://cli.github.com/"
    exit 1
fi

# Check auth
echo "[1/3] Checking GitHub CLI authentication..."
if ! gh auth status &> /dev/null; then
    echo "You are not logged into GitHub CLI. Please run: gh auth login"
    exit 1
fi
echo "Authentication confirmed."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISSUE_DIR="$SCRIPT_DIR/../.github/issues"

echo "[2/3] Reading issue files from $ISSUE_DIR..."
count=0

for file in $(find "$ISSUE_DIR" -maxdepth 1 -name "ISSUE-*.md" | sort); do
    title=$(sed -n 's/^title: "\(.*\)"/\1/p' "$file")
    if [ -z "$title" ]; then
        title=$(basename "$file" .md)
    fi

    # Extract labels
    labels_raw=$(sed -n 's/^labels: \[\(.*\)\]/\1/p' "$file" | tr -d '"' | tr -d "'")
    labels=$(echo "$labels_raw" | sed 's/ *, */,/g')

    # Extract body after second ---
    body=$(awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$file")

    echo -n "Publishing: $title... "
    if [ -n "$labels" ]; then
        gh issue create --title "$title" --body "$body" --label "$labels"
    else
        gh issue create --title "$title" --body "$body"
    fi
    count=$((count + 1))
    sleep 0.4
done

echo "=================================================="
echo "Successfully created $count issues on GitHub!"
echo "=================================================="
