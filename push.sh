#!/bin/bash

# --- 1. Configure SSH for GitHub ---
# Ensure GitHub's host key is trusted (prevents "authenticity" prompt)
mkdir -p ~/.ssh
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null

# Load SSH agent and key (replace with your key path)
eval "$(ssh-agent -s)" >/dev/null
ssh-add ~/.ssh/id_ed25519 2>/dev/null  # Or ~/.ssh/id_rsa if using RSA

# --- 2. Navigate to repo root ---
# More reliable than "cd ." - uses script's location as base
cd "$(dirname "$0")" || { echo "Failed to cd to script directory"; exit 1; }

# --- 3. Check for changes ---
if git diff --quiet data/latest/preprocessed_data_latest.csv; then
  echo "No changes detected in CSV. Nothing to commit."
  exit 0
fi

# --- 4. Commit changes ---
git add data/latest/preprocessed_data_latest.csv || { echo "Failed to git add"; exit 1; }
git commit -m "Auto-update CSV: $(date '+%Y-%m-%d %H:%M:%S')" || { echo "Failed to commit"; exit 1; }

# --- 5. Push with retry logic ---
max_retries=3
for ((i=1; i<=max_retries; i++)); do
  if git push origin main; then
    echo "Push successful."
    exit 0
  else
    echo "Push failed (attempt $i/$max_retries). Retrying in 5s..." >&2
    sleep 5
  fi
done

echo "Error: Push failed after $max_retries attempts." >&2
exit 1