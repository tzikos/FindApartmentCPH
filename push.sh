#!/bin/bash

# Force SSH to use full domain name
export GIT_SSH_COMMAND="ssh -o HostName=github.com"

# Load SSH agent
eval "$(ssh-agent -s)" >/dev/null
ssh-add ~/.ssh/id_ed25519 2>/dev/null

cd "$(dirname "$0")" || exit 1

# --- 3. Check for changes ---
if git diff --quiet data/latest/preprocessed_data_latest.csv; then
  echo "✅ No changes detected."
  exit 0
fi

# --- 4. Commit changes ---
git add data/latest/preprocessed_data_latest.csv || {
  echo "❌ Failed to 'git add'" >&2
  exit 1
}

git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M:%S')" || {
  echo "❌ Failed to commit" >&2
  exit 1
}

# --- 5. Push with retries ---
max_retries=3
for ((i=1; i<=max_retries; i++)); do
  if git push origin main; then
    echo "✅ Push succeeded."
    exit 0
  else
    echo "⚠️ Push failed (attempt $i/$max_retries)" >&2
    sleep 5
  fi
done

echo "❌ Error: Push failed after $max_retries attempts" >&2
exit 1