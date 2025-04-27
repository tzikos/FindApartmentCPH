import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Function to get the latest CSV file from the 'data/preprocessed' folder
def get_latest_file():
    folder = 'data/processed'
    files = [f for f in os.listdir(folder) if f.endswith('.csv')]
    if files:
        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder, f)))
        return os.path.join(folder, latest_file)
    else:
        st.error("No preprocessed CSV files found.")
        return None

# Load the latest CSV file
latest_file = get_latest_file()

if latest_file:
    df = pd.read_csv(latest_file)

    # Streamlit sidebar for filters
    st.sidebar.header("Filter Options")

    # Area filter with "All" option
    area_options = ['All'] + list(df['area'].unique())
    selected_area = st.sidebar.selectbox("Select Area", options=area_options)

    # Toggle to include apartments with null "available_from"
    include_null_available_from = st.sidebar.checkbox("Include apartments with unknown Available From date", value=False)

    # Available From filter (choose from date range)
    available_from_min = pd.to_datetime(df['available_from']).min()
    available_from_max = pd.to_datetime(df['available_from']).max()
    selected_available_from = st.sidebar.date_input(
        "Select Available From Date",
        value=available_from_min,
        min_value=available_from_min,
        max_value=available_from_max
    )

    # Price range filter (monthly rent)
    min_price, max_price = int(df['monthly_rent'].min()), int(df['monthly_rent'].max())
    selected_price_range = st.sidebar.slider(
        "Select Price Range (monthly rent + aconto)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price)
    )

    # Number of rooms filter
    room_options = ['All'] + sorted(list(df['rooms'].unique()))
    selected_rooms = st.sidebar.selectbox("Select Number of Rooms", options=room_options)

    # Size filter (square meters)
    min_size, max_size = int(df['size_sqm'].min()), int(df['size_sqm'].max())
    selected_size = st.sidebar.slider(
        "Select Size Range (in sqm)",
        min_value=min_size,
        max_value=max_size,
        value=(min_size, max_size)
    )

    # Energy mark filter
    energy_mark_options = df['energy_mark'].unique()
    selected_energy_mark = st.sidebar.selectbox("Select Energy Mark", options=['All'] + list(energy_mark_options))

    # Slider for filtering apartments within nth IQR of total rental price
    total_rental_price = df['monthly_rent'] + df['monthly_aconto']
    q1 = total_rental_price.quantile(0.25)
    q3 = total_rental_price.quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + iqr
    lower_bound = q1 - iqr
    selected_iqr = st.sidebar.slider(
        "Select IQR (upper bound for total rental price)",
        min_value=0,
        max_value=100,  # Use 100% of the IQR range
        value=100
    )

    # Apply IQR filter
    upper_limit = lower_bound + (selected_iqr / 100) * iqr
    df['total_rental_price'] = total_rental_price
    filtered_df = df[df['total_rental_price'] <= upper_limit]

    # Apply other filters
    if selected_area != 'All':
        filtered_df = filtered_df[filtered_df['area'] == selected_area]
    if selected_rooms != 'All':
        filtered_df = filtered_df[filtered_df['rooms'] == selected_rooms]

    if include_null_available_from:
        filtered_df = filtered_df[
            ((pd.to_datetime(filtered_df['available_from'], errors='coerce') >= pd.to_datetime(selected_available_from)) | 
             (filtered_df['available_from'].isnull()))
        ]
    else:
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['available_from'], errors='coerce') >= pd.to_datetime(selected_available_from))
        ]

    filtered_df = filtered_df[
        (filtered_df['total_rental_price'] >= selected_price_range[0]) &
        (filtered_df['total_rental_price'] <= selected_price_range[1]) &
        (filtered_df['size_sqm'] >= selected_size[0]) &
        (filtered_df['size_sqm'] <= selected_size[1])
    ]
    if selected_energy_mark != 'All':
        filtered_df = filtered_df[filtered_df['energy_mark'] == selected_energy_mark]

    # Display the filtered data with selected columns
    st.write(f"Filtered Data ({len(filtered_df)} entries):")
    
    # Select the columns to display in the table
    display_columns = ['url', 'area', 'total_rental_price', 'size_sqm', 'rooms', 'available_from', 'energy_mark']
    filtered_df_display = filtered_df[display_columns]

    # Make the URL column clickable
    filtered_df_display['url'] = filtered_df_display['url'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

    # Display the data in the table with clickable URLs
    st.markdown(filtered_df_display.to_html(escape=False), unsafe_allow_html=True)

    # Create a table for statistics (Min, Max, Average, Std Dev) for rent and size
    rent_stats = {
        'min': filtered_df['total_rental_price'].min(),
        'max': filtered_df['total_rental_price'].max(),
        'avg': filtered_df['total_rental_price'].mean(),
        'std': filtered_df['total_rental_price'].std()
    }

    size_stats = {
        'min': filtered_df['size_sqm'].min(),
        'max': filtered_df['size_sqm'].max(),
        'avg': filtered_df['size_sqm'].mean(),
        'std': filtered_df['size_sqm'].std()
    }

    # Create a DataFrame to display the statistics
    stats_data = {
        'Min': [rent_stats['min'], size_stats['min']],
        'Max': [rent_stats['max'], size_stats['max']],
        'Average': [rent_stats['avg'], size_stats['avg']],
        'Std Dev': [rent_stats['std'], size_stats['std']]
    }

    # Create the DataFrame for the statistics table
    stats_df = pd.DataFrame(stats_data, index=['Rent', 'Size (sqm)'])

    # Display the statistics table
    st.write("### Statistics on Filtered Data:")
    st.dataframe(stats_df)

else:
    st.write("No data available.")