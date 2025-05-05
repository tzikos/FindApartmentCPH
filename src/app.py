import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Set up page config and custom CSS for left alignment
st.set_page_config(page_title="🏠 Apartment Finder", layout="wide")

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
""" <style>
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
        st.error("⚠️ No preprocessed CSV files found.")
        return None

# Initialize session state flags if they don't exist
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.apply_filters = False
    st.session_state.reset_filters = False
    st.session_state.apply_preset = False

# Load the latest CSV file
latest_file = get_latest_file()

if latest_file:
    # Get the modification time of the latest file
    latest_file_mtime = os.path.getmtime(latest_file)
    latest_file_date = (datetime.fromtimestamp(latest_file_mtime) + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")

    # Big title with small last update text
    st.markdown(f"# 🏙️ Find apartment in CPH  \n<Large>🕒 Last update {latest_file_date} CET</Large>", unsafe_allow_html=True)
    
    # Load data once at the beginning
    df = pd.read_csv(latest_file)

    # Calculate total rental price once
    df['total_rental_price'] = df['monthly_rent'] + df['monthly_aconto']
    
    # Create a new column 'move_in_price' by summing 'monthly_rent', 'monthly_aconto', 'deposit', and 'prepaid_rent'
    try:
        df['move_in_price'] = df[['monthly_rent', 'monthly_aconto', 'deposit', 'prepaid_rent']].sum(axis=1)
    except Exception as e:
        print(f"Error calculating move_in_price: {e}")
        # Fallback if calculation fails
        df['move_in_price'] = df['monthly_rent'] * 3  # Simple approximation

    # Get available areas from the dataset
    areas = sorted(list(df['area'].unique()))
    
    # Parse available dates once
    available_dates = pd.to_datetime(df['available_from'], errors='coerce')
    
    # Calculate min/max dates for filters
    if not available_dates.isna().all():
        available_from_min = available_dates.min().date()
        available_from_max = available_dates.max().date()
    else:
        # Default dates if no valid dates in dataset
        today = datetime.now().date()
        available_from_min = today
        available_from_max = today + timedelta(days=90)
    
    # Calculate price ranges
    min_price = int(df['total_rental_price'].min())
    max_price = int(df['total_rental_price'].max())
    min_price_thousands = min_price / 1000
    max_price_thousands = 45.0  # Fixed max value for slider
    
    # Calculate move-in price ranges
    min_move_in_price = int(df['move_in_price'].min())
    max_move_in_price = int(df['move_in_price'].max())
    min_move_in_price_thousands = min_move_in_price / 1000
    max_move_in_price_thousands = 100.0  # Fixed max value for slider
    
    # Size ranges
    min_size = int(df['size_sqm'].min())
    max_size = int(df['size_sqm'].max())
    
    # Room options
    room_options = ['All'] + sorted([str(x) for x in df['rooms'].dropna().unique()])
    
    # Energy mark options
    energy_mark_options = ['All'] + sorted(list(df['energy_mark'].dropna().unique()))
    
    # Furnished options
    furnished_options = ['All'] + sorted(df['furnished'].dropna().unique().tolist())

    # Initialize session state only once
    if not st.session_state.initialized:
        st.session_state.original_df = df.copy()
        st.session_state.filtered_df = df.copy()
        
        # Initialize sorting state
        st.session_state.sort_column = None
        st.session_state.sort_direction = True  # True for ascending, False for descending
        
        # Initialize all filter values
        st.session_state.selected_area = []
        st.session_state.include_null_available_from = True
        st.session_state.selected_available_from = [available_from_min, available_from_max]
        st.session_state.selected_price_range_thousands = (min_price_thousands, max_price_thousands)
        st.session_state.selected_rooms = 'All'
        st.session_state.selected_size = (min_size, max_size)
        st.session_state.selected_energy_mark = 'All'
        st.session_state.selected_percentile = 100
        st.session_state.selected_furnished = 'All'
        st.session_state.selected_days_on_website = (0, 90)
        st.session_state.selected_move_in_price_thousands = (min_move_in_price_thousands, max_move_in_price_thousands)
        
        st.session_state.initialized = True
    
    # Streamlit sidebar for filters
    st.sidebar.header("🔍 Filter Options")

    # --- Pre-saved Filters Section ---
    st.sidebar.subheader("🧠 Pre-saved Filters")

    # Button to apply pre-saved filter
    preset_clicked = st.sidebar.button("🎯 Apply 'Large Apartments in CPH' Preset")
    if preset_clicked:
        st.session_state.apply_preset = True
        st.rerun()
    
    # Handle preset application
    if st.session_state.apply_preset:
        # Store preset values
        st.session_state.selected_area = [
            'Frederiksberg C', 'Frederiksberg', 'København K', 'København NV', 
            'København N', 'København SV', 'København V', 'København Ø', 
            'Nordhavn', 'Valby'
        ]
        st.session_state.include_null_available_from = True
        st.session_state.selected_available_from = [datetime(2025, 8, 1).date(), datetime(2025, 9, 1).date()]
        st.session_state.selected_price_range_thousands = (4.6, 20.1)
        st.session_state.selected_rooms = '4'
        st.session_state.selected_size = (80, 363)
        st.session_state.selected_energy_mark = 'All'
        st.session_state.selected_percentile = 100
        st.session_state.selected_furnished = 'All'
        st.session_state.selected_days_on_website = (0, 10)
        st.session_state.selected_move_in_price_thousands = (6.4, 85.8)
        
        # Reset flag and trigger filter application
        st.session_state.apply_preset = False
        st.session_state.apply_filters = True
    
    # Area filter
    selected_area = st.sidebar.multiselect(
        "📍 Select Area", 
        options=areas,
        default=st.session_state.selected_area
    )
    
    # Include null available_from checkbox
    include_null_available_from = st.sidebar.checkbox(
        "Include apartments with unknown Available From date", 
        value=st.session_state.include_null_available_from
    )
    
    # Available From date range
    selected_available_from = st.sidebar.date_input(
        "📅 Select Availability Date Range", 
        st.session_state.selected_available_from, 
        min_value=available_from_min, 
        max_value=available_from_max
    )
    
    # Price range slider
    selected_price_range_thousands = st.sidebar.slider(
        "💰 Select Price Range (monthly rent + aconto)",
        min_value=min_price_thousands,
        max_value=max_price_thousands,
        value=st.session_state.selected_price_range_thousands,
        format="%.1fk DKK"
    )
    st.sidebar.markdown("<small>in thousands DKK, max shown as 45k+</small>", unsafe_allow_html=True)
    
    # Rooms selectbox
    selected_rooms = st.sidebar.selectbox(
        "🛏️ Select min. Number of Rooms", 
        options=room_options,
        index=room_options.index(st.session_state.selected_rooms) if st.session_state.selected_rooms in room_options else 0
    )
    
    # Size slider
    selected_size = st.sidebar.slider(
        "📐 Select Size Range (in sqm)",
        min_value=min_size,
        max_value=max_size,
        value=st.session_state.selected_size
    )
    
    # Energy mark selectbox
    selected_energy_mark = st.sidebar.selectbox(
        "⚡ Select Energy Mark", 
        options=energy_mark_options,
        index=energy_mark_options.index(st.session_state.selected_energy_mark) if st.session_state.selected_energy_mark in energy_mark_options else 0
    )
    
    # Percentile slider
    selected_percentile = st.sidebar.slider(
        "📊 Show apartments up to N-th percentile of total rental price",
        min_value=0,
        max_value=100,
        value=st.session_state.selected_percentile
    )
    
    # Furnished selectbox
    selected_furnished = st.sidebar.selectbox(
        "🛋️ Select Furnished", 
        options=furnished_options,
        index=furnished_options.index(st.session_state.selected_furnished) if st.session_state.selected_furnished in furnished_options else 0
    )
    
    # Days on website slider
    selected_days_on_website = st.sidebar.slider(
        "⏳ Select Days on Website",
        min_value=0,
        max_value=90,
        value=st.session_state.selected_days_on_website
    )
    
    # Move-in price slider
    selected_move_in_price_thousands = st.sidebar.slider(
        "💵 Select Move-in Price Range",
        min_value=min_move_in_price_thousands,
        max_value=max_move_in_price_thousands,
        value=st.session_state.selected_move_in_price_thousands,
        format="%.1fk DKK"
    )
    st.sidebar.markdown("<small>in thousands DKK, max shown as 100k+</small>", unsafe_allow_html=True)
    
    # Apply Filters button
    apply_clicked = st.sidebar.button("✅ Apply Filters")
    if apply_clicked:
        # Store current filter values in session state
        st.session_state.selected_area = selected_area
        st.session_state.include_null_available_from = include_null_available_from
        st.session_state.selected_available_from = selected_available_from
        st.session_state.selected_price_range_thousands = selected_price_range_thousands
        st.session_state.selected_rooms = selected_rooms
        st.session_state.selected_size = selected_size
        st.session_state.selected_energy_mark = selected_energy_mark
        st.session_state.selected_percentile = selected_percentile
        st.session_state.selected_furnished = selected_furnished
        st.session_state.selected_days_on_website = selected_days_on_website
        st.session_state.selected_move_in_price_thousands = selected_move_in_price_thousands
        
        # Set flag to apply filters and rerun
        st.session_state.apply_filters = True
        st.rerun()
    
    # Add a horizontal line to separate buttons
    st.sidebar.markdown("---")
    
    # Reset Filters button
    reset_clicked = st.sidebar.button("🔄 Reset All Filters")
    if reset_clicked:
        st.session_state.reset_filters = True
        st.rerun()
    
    # Handle reset filters action
    if st.session_state.reset_filters:
        # Reset all filter values to defaults
        st.session_state.selected_area = []
        st.session_state.include_null_available_from = True
        st.session_state.selected_available_from = [available_from_min, available_from_max]
        st.session_state.selected_price_range_thousands = (min_price_thousands, max_price_thousands)
        st.session_state.selected_rooms = 'All'
        st.session_state.selected_size = (min_size, max_size)
        st.session_state.selected_energy_mark = 'All'
        st.session_state.selected_percentile = 100
        st.session_state.selected_furnished = 'All'
        st.session_state.selected_days_on_website = (0, 90)
        st.session_state.selected_move_in_price_thousands = (min_move_in_price_thousands, max_move_in_price_thousands)
        
        # Reset flag and trigger filter application
        st.session_state.reset_filters = False
        st.session_state.apply_filters = True
    
    # Apply filters when necessary
    if st.session_state.apply_filters:
        # Start with the original dataset
        filtered_df = df.copy()
        
        # Apply area filter
        if st.session_state.selected_area:
            filtered_df = filtered_df[filtered_df['area'].isin(st.session_state.selected_area)]
        
        # Apply furnished filter
        if st.session_state.selected_furnished != 'All':
            filtered_df = filtered_df[filtered_df['furnished'] == st.session_state.selected_furnished]
        
        # Apply rooms filter
        if st.session_state.selected_rooms != 'All':
            filtered_df = filtered_df[filtered_df['rooms'] >= float(st.session_state.selected_rooms)]
        
        # Apply days on website filter
        filtered_df = filtered_df[
            (filtered_df['days_on_website'] >= st.session_state.selected_days_on_website[0]) &
            (filtered_df['days_on_website'] <= st.session_state.selected_days_on_website[1])
        ]

        # Handle available_from filtering
        try:
            available_from_min = pd.to_datetime(st.session_state.selected_available_from[0])
            available_from_max = pd.to_datetime(st.session_state.selected_available_from[1])
            
            if st.session_state.include_null_available_from:
                filtered_df = filtered_df[
                    ((pd.to_datetime(filtered_df['available_from'], errors='coerce') >= available_from_min) | 
                    (filtered_df['available_from'].isnull())) &
                    ((pd.to_datetime(filtered_df['available_from'], errors='coerce') <= available_from_max) | 
                    (filtered_df['available_from'].isnull()))
                ]
            else:
                # Filter out null available_from and apply date filter
                filtered_df = filtered_df[
                    pd.to_datetime(filtered_df['available_from'], errors='coerce').notna() &
                    (pd.to_datetime(filtered_df['available_from'], errors='coerce') >= available_from_min) &
                    (pd.to_datetime(filtered_df['available_from'], errors='coerce') <= available_from_max)
                ]
        except Exception as e:
            st.warning(f"Date filtering error: {e}")
            # If date filtering fails, keep all rows
            pass
            
        # Apply price range filter
        price_min = st.session_state.selected_price_range_thousands[0] * 1000
        price_max = st.session_state.selected_price_range_thousands[1] * 1000
        
        # If user selects max value, treat it as "no maximum"
        if price_max >= 45000:
            filtered_df = filtered_df[filtered_df['total_rental_price'] >= price_min]
        else:
            filtered_df = filtered_df[(filtered_df['total_rental_price'] >= price_min) & 
                                      (filtered_df['total_rental_price'] <= price_max)]
        
        # Apply move-in price filter
        move_in_min = st.session_state.selected_move_in_price_thousands[0] * 1000
        move_in_max = st.session_state.selected_move_in_price_thousands[1] * 1000
        
        if move_in_max >= 100000:
            filtered_df = filtered_df[filtered_df['move_in_price'] >= move_in_min]
        else:
            filtered_df = filtered_df[(filtered_df['move_in_price'] >= move_in_min) & 
                                     (filtered_df['move_in_price'] <= move_in_max)]

        # Apply size filter
        filtered_df = filtered_df[
            (filtered_df['size_sqm'] >= st.session_state.selected_size[0]) &
            (filtered_df['size_sqm'] <= st.session_state.selected_size[1])
        ]
        
        # Apply energy mark filter
        if st.session_state.selected_energy_mark != 'All':
            filtered_df = filtered_df[filtered_df['energy_mark'] == st.session_state.selected_energy_mark]
            
        # Apply percentile filter LAST
        if st.session_state.selected_percentile < 100:
            # Get the threshold price at the selected percentile
            price_threshold = filtered_df['total_rental_price'].quantile(st.session_state.selected_percentile / 100)
            # Apply the filter
            filtered_df = filtered_df[filtered_df['total_rental_price'] <= price_threshold]
        
        # Reset sorting
        st.session_state.sort_column = None
        st.session_state.sort_direction = True
        
        # Save the filtered dataframe to session state
        st.session_state.filtered_df = filtered_df
        
        # Reset flag
        st.session_state.apply_filters = False
        
    # Select the columns to display in the table
    display_columns = ['url', 'area', 'total_rental_price', 'size_sqm', 'rooms', 'available_from', 
                      'energy_mark', 'furnished', 'creation_date', 'move_in_price']
    
    # Create display dataframe
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
        'furnished': 'Furnished',
        'creation_date': 'Listing Date',
        'move_in_price': 'Move-in Price'
    })

    # Display dataframe with clickable links using st.dataframe
    if not filtered_df_display.empty:
        
        # Create a table for statistics
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
        st.write(f"### 📊 Statistics on Filtered Data ({len(st.session_state.filtered_df)} entries):")
        st.dataframe(stats_df, use_container_width=True, hide_index=False)
        
        # Display listings
        st.write(f"### 🏘️ Listings")
        st.dataframe(
            filtered_df_display,
            height=600,
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn(label="🔗 View Listing", display_text="View Listing"),
                "Total Rent": st.column_config.NumberColumn(format="kr %d"),
                "Size (m²)": st.column_config.NumberColumn(format="%.1f m²"),
                "Available From": st.column_config.DateColumn(format="MMM DD, YYYY"),
                "Listing Date": st.column_config.DateColumn(format="MMM DD, YYYY"),
                "Move-in Price": st.column_config.NumberColumn(format="kr %d"),
            }
        )

    else:
        st.write("❌ No apartments match the selected filters.")

else:
    st.write("❌ No data available.")