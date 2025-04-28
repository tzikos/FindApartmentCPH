import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
# Get today's date in YYYY-MM-DD format
today_date = datetime.today().strftime('%Y-%m-%d')
# Configure logging
logging.basicConfig(
    level=logging.ERROR, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'outputs/errors/preprocess_errors_{today_date}.log'),
    ]
)

# Get today's date in YYYY-MM-DD format
today_date = datetime.today().strftime('%Y-%m-%d')

# Add the date to the filename
df = pd.read_csv(f'data/raw/bolig_data_{today_date}.csv')

pcts = df.isnull().sum()/len(df)*100

# Prepare the null percentage information
null_info = []
for null_col, pct in zip(df.columns[pcts > 0], pcts[df.columns[pcts > 0]]):
    null_info.append(f'{null_col}: {pct:.2f}% null')

# Save the null percentage information to a .txt file
with open(f'outputs/stats/null_pcts_{today_date}.txt', 'w') as file:
    file.write('\n'.join(null_info))


# Drop the Danish versions if you want to keep the English ones
df.drop(['Månedlig leje', 'Ledig fra', 'Indflytningspris', 'Lejeperiode', 'Aconto','move_in_price'], axis=1, inplace=True)

df.columns = df.columns.str.strip()

# Now for easier understanding of which columns we need for our project we will translate the columns from Danish to English
# Dictionary for translating column names
translations = {
    'breadcrumb': 'breadcrumb',
    'title': 'title',
    'description': 'description',
    'address': 'address',
    'monthly_rent': 'monthly_rent',
    'monthly_aconto': 'monthly_aconto',
    'move_in_price': 'move_in_price',
    'available_from': 'available_from',
    'rental_period': 'rental_period',
    'Boligtype': 'housing_type',  # Danish: Boligtype
    'Størrelse': 'size_sqm',  # Danish: Størrelse
    'Værelser': 'rooms',  # Danish: Værelser
    'Etage': 'floor',  # Danish: Etage
    'Møbleret': 'furnished',  # Danish: Møbleret
    'Delevenlig': 'roommate_friendly',  # Danish: Delevenlig
    'Husdyr tilladt': 'pets_allowed',  # Danish: Husdyr tilladt
    'Elevator': 'elevator',  # Danish: Elevator
    'Seniorvenlig': 'senior_friendly',  # Danish: Seniorvenlig
    'Kun for studerende': 'students_only',  # Danish: Kun for studerende
    'Altan/terrasse': 'balcony_terrasse',  # Danish: Altan/terrasse
    'Parkering': 'parking',  # Danish: Parkering
    'Opvaskemaskine': 'dishwasher',  # Danish: Opvaskemaskine
    'Vaskemaskine': 'washing_machine',  # Danish: Vaskemaskine
    'Ladestander': 'charging_station',  # Danish: Ladestander
    'Tørretumbler': 'dryer',  # Danish: Tørretumbler
    'Lejeperiode': 'rental_period',  # Danish: Lejeperiode
    'Ledig fra': 'available_from',  # Danish: Ledig fra
    'Månedlig leje': 'monthly_rent',  # Danish: Månedlig leje
    'Aconto': 'aconto',  # Danish: Aconto
    'Depositum': 'deposit',  # Danish: Depositum
    'Forudbetalt husleje': 'prepaid_rent',  # Danish: Forudbetalt husleje
    'Indflytningspris': 'move_in_price',  # Danish: Indflytningspris
    'Oprettelsesdato': 'creation_date',  # Danish: Oprettelsesdato
    'Sagsnr.': 'case_number',  # Danish: Sagsnr.
    'energy_mark_src': 'energy_mark_source',
    'Energimærke': 'energy_label'  # Danish: Energimærke
}

# Apply the translations to rename columns
df.rename(columns=translations, inplace=True)

# We will now try to transform some of object data types to numeric ones. Mostly those that refer to prices.
columns_to_transform=['monthly_rent', 'monthly_aconto', 'deposit', 'prepaid_rent']
# Remove ' kr' and '.' for multiple columns
try:
    df[columns_to_transform] = df[columns_to_transform].apply(lambda x: x.str.replace('kr', '').str.replace('.', '').str.replace(',', '').str.strip() if x.str else '0')
except Exception as e:
    logging.error(f"Error cleaning currency columns: {e}")

try:
    df[columns_to_transform] = df[columns_to_transform].apply(pd.to_numeric)
except Exception as e:
    logging.error(f"Error converting currency columns to numeric: {e}")

# Assumption: set prepaid rent to 0 when it's NaN
try:
    df['prepaid_rent'] = df['prepaid_rent'].fillna('0').astype(float)
except Exception as e:
    logging.error(f"Error processing 'prepaid_rent' column: {e}")

# Replace NaN values with 0 before casting to integer
try:
    df[df.select_dtypes(include=['float']).columns] = df.select_dtypes(include=['float']).fillna(-1.0).astype(int)
except Exception as e:
    logging.error(f"Error converting float columns to int: {e}")

try:
    df['energy_mark_source'] = df['energy_mark_source'].fillna('')
    df['energy_mark'] = df['energy_mark_source'].apply(lambda x: x.split('/')[-1].split('_')[0])
except Exception as e:
    logging.error(f"Error processing 'energy_mark' column: {e}")

try:
    df = df[df['size_sqm'].notna()]
    df['size_sqm'] = df['size_sqm'].apply(lambda x: x.replace('m²','').strip().split('.')[0]).astype(int)
except Exception as e:
    logging.error(f"Error processing 'size_sqm' column: {e}")

# df.drop(columns=['energy_mark_source','energy_label','breadcrumb','title','description','rental_period', 'case_number'], inplace=True)

# Dictionary to map Danish month names to numbers
danish_months = {
    " januar ": "1.",
    " februar ": "2.",
    " marts ": "3.",
    " april ": "4.",
    " maj ": "5.",
    " juni ": "6.",
    " juli ": "7.",
    " august ": "8.",
    " september ": "9.",
    " oktober ": "10.",
    " november ": "11.",
    " december ": "12."
}

def format_date(date_str):
    # Try to parse the date with the Danish month name
    for month, number in danish_months.items():
        if month in date_str:
            # Replace the month name with the corresponding number
            date_str = date_str.replace(month, number)
            # Parse the date to a datetime object
            #date_obj = datetime.datetime.strptime(date_str, "%d. %m. %Y")
            #return date_obj.strftime("%d.%m.%Y")
            return date_str
    # If it's already in the correct format
    #date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y")
    return date_str

try:
    df['available_from'] = df['available_from'].replace('Snarest muligt', datetime.today().strftime('%d.%m.%Y'))
    df['available_from'] = df['available_from'].apply(format_date)
    df['available_from'] = pd.to_datetime(df['available_from'], format='%d.%m.%Y', dayfirst=True)
except Exception as e:
    logging.error(f"Error processing 'available_from' column: {e}")

try:
    df['creation_date'] = pd.to_datetime(df['creation_date'], dayfirst=True)
except Exception as e:
    logging.error(f"Error processing 'creation_date' column: {e}")

try:
    df['area'] = df['address'].apply(lambda x: x.split('-')[0].split(',')[-1].strip() if '-' in x else x.split(',')[-1].strip())
except Exception as e:
    logging.error(f"Error processing 'area' column: {e}")

# We want to make floor a numeric var so we have to make assumptions: Stuen (=living room) is ground floor, Kælder (=cellar) is -1, - is translated to 0 as there is no floor
try:
    df['floor'] = df['floor'].apply(lambda x: x.replace('Stuen','0').replace('Kælder','-1').replace('-','0').replace('.','')).astype(int)
except Exception as e:
    logging.error(f"Error processing 'floor' column: {e}")

with open(f'outputs/stats/unique_values_{today_date}.txt', 'w') as file:
    for dtype, columns in df.columns.to_series().groupby(df.dtypes):
        file.write(f"Type: {dtype}\n")
        file.write(f"Columns: {list(columns)}\n\n")
    
    for col in df.columns:
        if df.dtypes[col] == 'O':
            file.write('-------------------------------\n')
            file.write(f'{col}\n')
            file.write(f'{df[col].unique()}\n\n')

# create new column availability_in: buckets of <1 month, 1-3 months, 3+ months
try:
    df['available_from'] = pd.to_datetime(df['available_from'], errors='coerce')
except Exception as e:
    logging.error(f"Error processing 'available_from' column: {e}")

# Now apply the availability categorization
try:
    df['availability_in'] = df.apply(
        lambda x: '<1 month' if (x['available_from'] - x['creation_date']).days < 30
                  else ('1-3 months' if (x['available_from'] - x['creation_date']).days < 90
                        else '3+ months'), axis=1)
except Exception as e:
    logging.error(f"Error processing 'availability_in' column: {e}")

scrape_date = pd.to_datetime(today_date, format='%Y-%m-%d')
df['days_on_website'] = df['creation_date'].apply(lambda x: (scrape_date - x).days)

try:
    df['total_monthly_rent'] = df['monthly_rent'] + df['monthly_aconto']
except Exception as e:
    logging.error(f"Error processing 'total_monthly_rent' column: {e}")

continuous_vars = ['monthly_rent','monthly_aconto','size_sqm','deposit','prepaid_rent','total_monthly_rent','days_on_website']
df[continuous_vars] = df[continuous_vars].astype(float)

try:
    df['months_on_website'] = df['days_on_website'].apply(lambda x: '<1 month' if x<30 else ('1-3 months' if x<90 else ('3-6 months' if x <180 else '6+ months')))
except Exception as e:
    logging.error(f"Error processing 'months_on_website' column: {e}")

# Save the dataframe with today's date in the filename
df.to_csv(f'data/processed/preprocessed_data_{today_date}.csv', index=False, header=True, encoding='utf-8')

# Save it also under latest folder
df.to_csv(f'data/latest/preprocessed_data_latest.csv', index=False, header=True, encoding='utf-8')