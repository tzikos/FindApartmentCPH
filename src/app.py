import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Set up page config and custom CSS for left alignment
st.set_page_config(page_title="Apartment Finder", layout="wide")

# Custom CSS for left alignment and table styling
st.markdown("""
<style>
    .dataframe th {
        text-align: left !important;
    }
    .dataframe td {
        text-align: left !important;
    }
    thead tr th {
        text-align: left !important;
    }
    tbody tr td {
        text-align: left !important;
    }
    div.row-widget.stRadio > div {
        flex-direction: row;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* Make sidebar wider */
    [data-testid="stSidebar"] {
        width: 500px; /* Or whatever width you want */
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

# Function to get the latest CSV file from the 'data/preprocessed' folder
def get_latest_file():
    folder = 'data/latest'
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
    # Get the modification time of the latest file
    latest_file_mtime = os.path.getmtime(latest_file)
    latest_file_date = (datetime.fromtimestamp(latest_file_mtime) + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Big title with small last update text
    st.markdown(f"# Find apartment in CPH  \n<Large>Last update {latest_file_date} CET</Large>", unsafe_allow_html=True)
    # Load data once at the beginning
    df = pd.read_csv(latest_file)
    
    # Calculate total rental price once
    df['total_rental_price'] = df['monthly_rent'] + df['monthly_aconto']
    
    # Store the initial dataframe in session state if it doesn't exist
    if 'original_df' not in st.session_state:
        st.session_state.original_df = df.copy()
        st.session_state.filtered_df = df.copy()
        # Initialize sorting state
        st.session_state.sort_column = None
        st.session_state.sort_direction = True  # True for ascending, False for descending
        
    # Streamlit sidebar for filters
    st.sidebar.header("Filter Options")

    # Area filter with "All" option
    area_options = ['All'] + sorted(list(df['area'].unique()))
    selected_area = st.sidebar.selectbox("Select Area", options=area_options)

    # Toggle to include apartments with null "available_from"
    include_null_available_from = st.sidebar.checkbox("Include apartments with unknown Available From date", value=True)
    # st.sidebar.date_input("Range, no date", [])
    # Available From filter (choose from date range)
    available_from_min = pd.to_datetime(df['available_from'], errors='coerce').min()
    available_from_max = pd.to_datetime(df['available_from'], errors='coerce').max()
    selected_available_from = st.sidebar.date_input(
        "Select Availability Date Range", [available_from_min, available_from_max], min_value=available_from_min, max_value=available_from_max
    )

    # Price range filter (monthly rent)
    min_price, max_price = int(df['total_rental_price'].min()), int(df['total_rental_price'].max())

    # Divide by 1000 for thousands
    min_price_thousands = min_price / 1000
    # Force the max of slider to be 45k
    slider_max_thousands = 45.0

    selected_price_range_thousands = st.sidebar.slider(
        "Select Price Range (monthly rent + aconto)",
        min_value=min_price_thousands,
        max_value=slider_max_thousands,
        value=(min_price_thousands, slider_max_thousands),
        format="%.1fk DKK"
    )
    st.sidebar.markdown("<small>in thousands DKK, max shown as 45k+</small>", unsafe_allow_html=True)

    # Multiply back after selection
    selected_price_range = (selected_price_range_thousands[0] * 1000, selected_price_range_thousands[1] * 1000)

    # Number of rooms filter
    room_options = ['All'] + sorted([str(x) for x in df['rooms'].unique()])
    selected_rooms = st.sidebar.selectbox("Select min. Number of Rooms", options=room_options)

    # Size filter (square meters)
    min_size, max_size = int(df['size_sqm'].min()), int(df['size_sqm'].max())
    selected_size = st.sidebar.slider(
        "Select Size Range (in sqm)",
        min_value=min_size,
        max_value=max_size,
        value=(min_size, max_size)
    )

    # Energy mark filter
    energy_mark_options = df['energy_mark'].dropna().unique()
    selected_energy_mark = st.sidebar.selectbox("Select Energy Mark", options=['All'] + sorted(list(energy_mark_options)))

    # Slider: what percentile you want to include (0 = cheapest only, 100 = everything)
    selected_percentile = st.sidebar.slider(
        "Show apartments up to N-th percentile of total rental price",
        min_value=0,
        max_value=100,
        value=100
    )

    # Add a filter for furnished status
    selected_furnished = st.sidebar.selectbox("Select Furnished", options=['All'] + df['furnished'].unique().tolist())
    # Apply Filters button
    if st.sidebar.button("Apply Filters"):
        # Start with the original dataset
        filtered_df = df.copy()
        
        # Apply all filters except percentile filter
        if selected_area != 'All':
            filtered_df = filtered_df[filtered_df['area'] == selected_area]
        
        if selected_furnished != 'All':
            filtered_df = filtered_df[filtered_df['furnished'] == selected_furnished]
        if selected_rooms != 'All':
            filtered_df = filtered_df[filtered_df['rooms'] >= float(selected_rooms)]
            
        if include_null_available_from:
            filtered_df = filtered_df[
                ((pd.to_datetime(filtered_df['available_from'], errors='coerce') >= pd.to_datetime(selected_available_from[0])) | 
                (filtered_df['available_from'].isnull())) &
                (pd.to_datetime(filtered_df['available_from'], errors='coerce') <= pd.to_datetime(selected_available_from[1]))
            ]
        else:
            # Filter out null available_from and apply date filter
            filtered_df = filtered_df[
                pd.to_datetime(filtered_df['available_from'], errors='coerce').notna() &
                (pd.to_datetime(filtered_df['available_from'], errors='coerce') >= pd.to_datetime(selected_available_from))
            ]
            
        # Apply price range filter
        # If user selects 45k as maximum, treat it as "no maximum"
        if selected_price_range[1] >= 45000:
            filtered_df = filtered_df[
                (filtered_df['total_rental_price'] >= selected_price_range[0])
            ]
        else:
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
        
        # Reset sorting when applying new filters
        st.session_state.sort_column = None
        st.session_state.sort_direction = True
        
        # Save the filtered dataframe to session state
        st.session_state.filtered_df = filtered_df
    
    # Display the filtered data with selected columns
    # st.write(f"### Filtered Data ({len(st.session_state.filtered_df)} entries)")
    
    # Select the columns to display in the table and create a clean display dataframe
    display_columns = ['url', 'area', 'total_rental_price', 'size_sqm', 'rooms', 'available_from', 'energy_mark', 'furnished']
    filtered_df_display = st.session_state.filtered_df[display_columns].copy()
    
    # Convert available_from to datetime for better display
    filtered_df_display['available_from'] = pd.to_datetime(filtered_df_display['available_from'], errors='coerce')
    
    # Format columns for better display
    filtered_df_display['total_rental_price'] = filtered_df_display['total_rental_price'].round(0).astype(int)
    filtered_df_display['size_sqm'] = filtered_df_display['size_sqm'].round(1)
    
    # Rename columns for display
    filtered_df_display = filtered_df_display.rename(columns={
        'url': 'URL',
        'area': 'Area',
        'total_rental_price': 'Total Rent',
        'size_sqm': 'Size (m²)',
        'rooms': 'Rooms',
        'available_from': 'Available From',
        'energy_mark': 'Energy Mark',
        'furnished': 'Furnished'
    })
    
    
    # Display dataframe with clickable links using st.dataframe
    if not filtered_df_display.empty:
        
         # Create a table for statistics (Min, Max, Average, Std Dev) for rent and size
        current_df = st.session_state.filtered_df
        
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
            'Min': [f"{rent_stats['min']:.0f} kr", f"{size_stats['min']:.1f} m²"],
            'Max': [f"{rent_stats['max']:.0f} kr", f"{size_stats['max']:.1f} m²"],
            'Average': [f"{rent_stats['avg']:.0f} kr", f"{size_stats['avg']:.1f} m²"],
            'Std Dev': [f"{rent_stats['std']:.0f} kr", f"{size_stats['std']:.1f} m²"]
        }

        # Create the DataFrame for the statistics table
        stats_df = pd.DataFrame(stats_data, index=['Rent', 'Size'])

        # Display the statistics table
        st.write(f"### Statistics on Filtered Data ({len(st.session_state.filtered_df)} entries):")
        st.dataframe(stats_df, use_container_width=True, hide_index=False)
        # Display with st.dataframe for interactive sorting
        st.write(f"### Listings")
        st.dataframe(
        filtered_df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn(label="View Listing", display_text="View Listing"),
            "Total Rent": st.column_config.NumberColumn(format="kr %d"),
            "Size (m²)": st.column_config.NumberColumn(format="%.1f m²"),
            "Available From": st.column_config.DateColumn(format="MMM DD, YYYY")
        }
    )

    else:
        st.write("No apartments match the selected filters.")

else:
    st.write("No data available.")