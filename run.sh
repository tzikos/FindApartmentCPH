today=$(date +%F)
echo "Running the scraping script..."
echo ""
python src/scrape_boligportal.py
echo ""
echo "Running the data processing script..."
echo ""
python src/preprocess_scraped_data.py
echo ""