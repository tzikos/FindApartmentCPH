import requests
from bs4 import BeautifulSoup
import pandas as pd 
from datetime import datetime
from tqdm import tqdm
import time
import os
from multiprocessing import Pool, cpu_count
import logging

# Configure logging
logging.basicConfig(
    level=logging.ERROR, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"outputs/errors/scrape_errors_{datetime.today().strftime('%Y-%m-%d')}.log")
    ]
)

def fetch_html_content(link):
        full_url = f"https://www.boligportal.dk{link}"
        response = requests.get(full_url)
        if response.status_code == 200:
            return {'url': full_url, 'html_code': response.text}
        else:
            print(f"Failed to retrieve content from {full_url}")
            return None
        
def extract_apartment_info(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    apartment_info = {'url': url}  # Include the URL in the apartment info

    try:
        # Extract the breadcrumb (location) information
        breadcrumb = " > ".join([item.get_text(strip=True) for item in soup.select('.css-7kp13n a')])
        apartment_info['breadcrumb'] = breadcrumb
    except Exception as e:
        apartment_info['breadcrumb'] = None
        logging.error(f"Error extracting breadcrumb for URL {url}: {e}")

    try:
        # Extract the title of the apartment
        title = soup.select_one('h3.css-1o5zkyw').get_text(strip=True)
        apartment_info['title'] = title
    except Exception as e:
        apartment_info['title'] = None
        logging.error(f"Error extracting title for URL {url}: {e}")

    try:
        # Extract the main description
        description = soup.select_one('div.css-1f7mpex').get_text(strip=True)
        apartment_info['description'] = description
    except Exception as e:
        apartment_info['description'] = None
        logging.error(f"Error extracting description for URL {url}: {e}")

    try:
        # Extract the address
        address = soup.find_all('div', class_='css-o9y6d5')[0].get_text(strip=True) + ', ' + soup.find_all('div', class_='css-o9y6d5')[1].get_text(strip=True)
        apartment_info['address'] = address
    except Exception as e:
        apartment_info['address'] = None
        logging.error(f"Error extracting address for URL {url}: {e}")

    try:
        # Extract rent details
        monthly_rent = soup.select_one('.css-woykcw .css-1fhvb05').get_text(strip=True) + ' kr.'
        apartment_info['monthly_rent'] = monthly_rent
    except Exception as e:
        apartment_info['monthly_rent'] = None
        logging.error(f"Error extracting monthly rent for URL {url}: {e}")

    try:
        monthly_aconto = soup.select_one('.css-30nv8k').get_text(strip=True)
        apartment_info['monthly_aconto'] = monthly_aconto
    except Exception as e:
        apartment_info['monthly_aconto'] = None
        logging.error(f"Error extracting monthly aconto for URL {url}: {e}")

    try:
        move_in_price = soup.select('.css-30nv8k')[1].get_text(strip=True)
        apartment_info['move_in_price'] = move_in_price
    except Exception as e:
        apartment_info['move_in_price'] = None
        logging.error(f"Error extracting move-in price for URL {url}: {e}")

    try:
        # Extract availability
        available_from = soup.select_one('.css-2kngtw').get_text(strip=True)
        apartment_info['available_from'] = available_from
    except Exception as e:
        apartment_info['available_from'] = None
        logging.error(f"Error extracting available from for URL {url}: {e}")

    try:
        rental_period = soup.select('.css-14bctuo')[1].get_text(strip=True)
        apartment_info['rental_period'] = rental_period
    except Exception as e:
        apartment_info['rental_period'] = None
        logging.error(f"Error extracting rental period for URL {url}: {e}")

    try:
        # Extract detailed characteristics
        details = {item.select_one('.css-1td16zm').get_text(strip=True): item.select_one('.css-1f8murc').get_text(strip=True) for item in soup.select('.css-1n6wxiw') if item.select_one('.css-1f8murc')}
        apartment_info.update(details)
    except Exception as e:
        logging.error(f"Error extracting detailed characteristics for URL {url}: {e}")

    try:
        if soup.select_one('img.css-rdsunt'):
            apartment_info['energy_mark_src'] = soup.select_one('img.css-rdsunt').get('src')
        else:
            apartment_info['energy_mark_src'] = 'none'
    except Exception as e:
        apartment_info['energy_mark_src'] = None
        logging.error(f"Error extracting energy mark source for URL {url}: {e}")

    return apartment_info

def process_apartment_info(args):
    html_code, url = args
    return extract_apartment_info(html_code, url)

def main():
    # Base URL for the website
    base_url = "https://www.boligportal.dk/lejligheder/k%C3%B8benhavn/?include_units=1"

    # Dictionary to store the HTML content with page numbers as keys
    html_dict = {}

    # Iterate through the pages by modifying the offset
    i = 0
    print("Scraping pages...")
    start_time = time.time()  # Record the start time of the entire scraping process
    while True:
                
        # Construct the URL for the current page
        url = f"{base_url}&offset={18*i}"
        
        # Send a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if the element with class 'css-16snok8' exists
            if soup.find(class_='css-16snok8'):
                print(f"Stopping at page {i + 1} as 'css-16snok8' element was found.")
                break
            
            # Store the HTML content in the dictionary with the page number as the key
            html_dict[i + 1] = response.text
        else:
            print(f"Failed to retrieve page {i + 1}")
            break
        
        total_elapsed_time = time.time() - start_time  # Calculate the total elapsed time
        print(f"Page {i + 1} scraped. Total elapsed time: {total_elapsed_time:.2f} seconds", end='\r')
        
        i += 1
        
    # Optionally, you can print or save the html_dict to a file
    print(f"Scraped {len(html_dict)} pages successfully.")

    # To access the HTML content of a specific page
    # page_1_html = html_dict[1]

    links = []

    # Iterate through the HTML pages stored in html_dict
    for page_number, html_content in tqdm(html_dict.items(), desc="Extracting links from HTML pages"):
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all div elements with class "css-krvsu4"
        divs = soup.find_all('div', class_='css-krvsu4')
        
        # Extract the href from each div and store it in a list
        hrefs = [div.find('a')['href'] for div in divs if div.find('a')]
        
        for href in hrefs:
            # Store the hrefs in the dictionary with the page number as the key
            links.append(href)

    data = []

    with Pool(cpu_count()) as pool:
        results = list(tqdm(pool.imap(fetch_html_content, links), desc="Fetching HTML content for each URL", total=len(links)))

    # Filter out None results and extend the data list
    data.extend([result for result in results if result is not None])

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(data, columns=['url', 'html_code'])
    # Get today's date in YYYY-MM-DD format
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Ensure the directory exists, otherwise create it
    output_dir = 'data/raw'
    os.makedirs(output_dir, exist_ok=True)

    # Add the date to the filename
    output_path = os.path.join(output_dir, f'boligportal_pages_{today_date}.csv')

    # Save the DataFrame to a CSV file
    df.to_csv(output_path, index=False)

    with Pool(cpu_count()) as pool:
        df_list = list(tqdm(pool.imap(process_apartment_info, zip(df.html_code, df.url)), desc="Extracting apartment info", total=len(df)))

    new_df = pd.DataFrame(df_list)

    # Get today's date in YYYY-MM-DD format
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Ensure the directory exists, otherwise save in the current folder
    output_dir = 'data/raw'
    os.makedirs(output_dir, exist_ok=True)

    # Add the date to the filename
    output_path = os.path.join(output_dir, f'bolig_data_{today_date}.csv')
    new_df.to_csv(output_path, index=False, header=True, encoding='utf-8')

if __name__ == "__main__":
    main()