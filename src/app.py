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
    # Load data once at the beginning
    df = pd.read_csv(latest_file)
    
    # Calculate total rental price once
    df['total_rental_price'] = df['monthly_rent'] + df['monthly_aconto']
    
    # Store the initial dataframe in session state if it doesn't exist
    if 'original_df' not in st.session_state:
        st.session_state.original_df = df.copy()
        st.session_state.filtered_df = df.copy()
        
    # Streamlit sidebar for filters
    st.sidebar.header("Filter Options")

    # Area filter with "All" option
    area_options = ['All'] + sorted(list(df['area'].unique()))
    selected_area = st.sidebar.selectbox("Select Area", options=area_options)

    # Toggle to include apartments with null "available_from"
    include_null_available_from = st.sidebar.checkbox("Include apartments with unknown Available From date", value=False)

    # Available From filter (choose from date range)
    available_from_min = pd.to_datetime(df['available_from'], errors='coerce').min()
    available_from_max = pd.to_datetime(df['available_from'], errors='coerce').max()
    selected_available_from = st.sidebar.date_input(
        "Select Available From Date",
        value=available_from_min,
        min_value=available_from_min,
        max_value=available_from_max
    )

    # Price range filter (monthly rent)
    min_price, max_price = int(df['total_rental_price'].min()), int(df['total_rental_price'].max())
    selected_price_range = st.sidebar.slider(
        "Select Price Range (monthly rent + aconto)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price)
    )

    # Number of rooms filter
    room_options = ['All'] + sorted([str(x) for x in df['rooms'].unique()])
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
    selected_energy_mark = st.sidebar.selectbox("Select Energy Mark", options=['All'] + sorted(list(energy_mark_options)))

    # Slider: what percentile you want to include (0 = cheapest only, 100 = everything)
    selected_percentile = st.sidebar.slider(
        "Show apartments up to N-th percentile of total rental price",
        min_value=0,
        max_value=100,
        value=100
    )
    
    # Apply Filters button
    if st.sidebar.button("Apply Filters"):
        # Start with the original dataset
        filtered_df = df.copy()
        
        # Apply all filters except percentile filter
        if selected_area != 'All':
            filtered_df = filtered_df[filtered_df['area'] == selected_area]
            
        if selected_rooms != 'All':
            filtered_df = filtered_df[filtered_df['rooms'] == float(selected_rooms)]
            
        if include_null_available_from:
            filtered_df = filtered_df[
                ((pd.to_datetime(filtered_df['available_from'], errors='coerce') >= pd.to_datetime(selected_available_from)) | 
                (filtered_df['available_from'].isnull()))
            ]
        else:
            # Filter out null available_from and apply date filter
            filtered_df = filtered_df[
                pd.to_datetime(filtered_df['available_from'], errors='coerce').notna() &
                (pd.to_datetime(filtered_df['available_from'], errors='coerce') >= pd.to_datetime(selected_available_from))
            ]
            
        # Apply price range filter
        filtered_df = filtered_df[
            (filtered_df['total_rental_price'] >= selected_price_range[0]) &
            (filtered_df['total_rental_price'] <= selected_price_range[1])
        ]
        
        # Apply size filter
        filtered_df = filtered_df[
            (filtered_df['size_sqm'] >= selected_size[0]) &
            (filtered_df['size_sqm'] <= selected_size[1])
        ]
        
        # Apply energy mark filter
        if selected_energy_mark != 'All':
            filtered_df = filtered_df[filtered_df['energy_mark'] == selected_energy_mark]
            
        # Apply percentile filter LAST as requested
        if selected_percentile < 100:
            # Get the threshold price at the selected percentile
            price_threshold = filtered_df['total_rental_price'].quantile(selected_percentile / 100)
            # Apply the filter
            filtered_df = filtered_df[filtered_df['total_rental_price'] <= price_threshold]
        
        # Save the filtered dataframe to session state
        st.session_state.filtered_df = filtered_df
    
    # Display the filtered data with selected columns
    st.write(f"Filtered Data ({len(st.session_state.filtered_df)} entries):")
    
    # Select the columns to display in the table
    display_columns = ['url', 'area', 'total_rental_price', 'size_sqm', 'rooms', 'available_from', 'energy_mark']
    filtered_df_display = st.session_state.filtered_df[display_columns]

    # Make the URL column clickable
    filtered_df_display['url'] = filtered_df_display['url'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

    # Display the data in the table with clickable URLs
    st.markdown(filtered_df_display.to_html(escape=False), unsafe_allow_html=True)

    # Create a table for statistics (Min, Max, Average, Std Dev) for rent and size
    current_df = st.session_state.filtered_df
    
    if not current_df.empty:
        rent_stats = {
            'min': current_df['total_rental_price'].min(),
            'max': current_df['total_rental_price'].max(),
            'avg': current_df['total_rental_price'].mean(),
            'std': current_df['total_rental_price'].std()
        }

        size_stats = {
            'min': current_df['size_sqm'].min(),
            'max': current_df['size_sqm'].max(),
            'avg': current_df['size_sqm'].mean(),
            'std': current_df['size_sqm'].std()
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
        st.write("No apartments match the selected filters.")

else:
    st.write("No data available.")