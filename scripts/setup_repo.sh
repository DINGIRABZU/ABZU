#!/bin/bash
# Clone a GitHub repository into /INANNA_AI/repo using GITHUB_TOKEN
set -e

REPO="$1"

if [ -z "$REPO" ]; then
    echo "Usage: $0 <owner/repo>" >&2
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN environment variable not set" >&2
    exit 1
fi

mkdir -p /INANNA_AI
rm -rf /INANNA_AI/repo

git clone https://$GITHUB_TOKEN@github.com/$REPO.git /INANNA_AI/repo

echo "Repository cloned on $(date)" > /INANNA_AI/repo/confirmation.txt
