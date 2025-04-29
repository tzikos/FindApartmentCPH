#!/bin/bash

# Set working directory to the repo root
cd . || exit 1

# Check if there are any changes in the CSV file(s)
if git diff --quiet data/latest/preprocessed_data_latest.csv; then
  echo "No changes detected in CSV. Nothing to commit."
else
  # Add the updated CSV file(s)
  git add data/latest/preprocessed_data_latest.csv

  # Commit with timestamp
  git commit -m "Auto-update CSV: $(date '+%Y-%m-%d %H:%M:%S')"

  # Push to main branch
  git push origin main
fi