#!/bin/bash

# Set full paths
export PATH="/Users/tzikos/opt/anaconda3/bin:$PATH"

# Source conda.sh to properly initialize conda in a non-interactive shell
source /Users/tzikos/opt/anaconda3/etc/profile.d/conda.sh

# Activate environment using full path
conda activate find_apartment

echo "Running the scraping script..."
echo ""
/Users/tzikos/opt/anaconda3/envs/find_apartment/bin/python /Users/tzikos/Desktop/other/python\ tasks/FindApartmentCPH/src/scrape_boligportal.py
echo ""
echo "Running the data processing script..."
echo ""
/Users/tzikos/opt/anaconda3/envs/find_apartment/bin/python /Users/tzikos/Desktop/other/python\ tasks/FindApartmentCPH/src/preprocess_scraped_data.py
echo ""
echo "Pushing to GitHub..."
cd /Users/tzikos/Desktop/other/python\ tasks/FindApartmentCPH
/usr/bin/git add .
/usr/bin/git commit -m "Automated data update $(date)"
/usr/bin/git push origin main