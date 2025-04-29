#!/bin/bash -l
conda activate find_apartment

# Change to the script's directory to ensure relative paths work
cd "$(dirname "$0")"

echo "Running the scraping script..."
echo ""
python src/scrape_boligportal.py
echo ""
echo "Running the data processing script..."
echo ""
python src/preprocess_scraped_data.py
echo ""
echo "Pushing to GitHub..."
bash push.sh