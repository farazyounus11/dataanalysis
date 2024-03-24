import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import re

st.set_page_config(layout="wide")
st.title("Sales Data Analysis")
st.header('By Faraz Younus | M.S. Stats & Data Science', divider='gray')
st.header('Select month for Visualization!')
files = os.listdir('.')
csv_files = [file for file in files if file.endswith('.csv')]
if not csv_files:
    st.write("No CSV files found in the current directory.")
else:
    selected_file = st.selectbox('Select A Month', csv_files)
    
    if st.button('Select'):
        st.session_state['selected_file'] = selected_file

if 'selected_file' in st.session_state:
    # Reading the selected CSV file from session state
    df = pd.read_csv(st.session_state['selected_file'])
    
    df.rename(columns={'Quantity Ordered': 'Count'}, inplace=True)
    zip_code_pattern = r'\b\d{5}(?:-\d{4})?\b'


    ## Code helps get total
    df['Count'] = pd.to_numeric(df['Count'], errors='coerce')
    df['Price Each'] = pd.to_numeric(df['Price Each'], errors='coerce')
    df['Total'] = df['Count'] * df['Price Each']

    ## Extracts ZIP form adress
    df['Zip'] = df['Purchase Address'].apply(lambda x: re.search(zip_code_pattern, str(x)).group() if pd.notnull(x) and re.search(zip_code_pattern, str(x)) else None)
    df = df.dropna()
    df['Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%y %H:%M', errors='coerce')
    df = df.drop(columns=['Order Date'])
    df['Day'] = df['Date'].dt.day



    hour_range = st.sidebar.slider(
        "Filter the Hour of Day",
        0, 24, (0, 24),
        step=1,  # Hour steps
        format="%d hours"
    )

    # Further filtering DataFrame based on selected hour range
    df['Hour'] = df['Date'].dt.hour
    df = df[df['Hour'].between(hour_range[0], hour_range[1], inclusive='both')]

    # Sidebar price range slider
    df['Price Each'] = pd.to_numeric(df['Price Each'], errors='coerce')

    # Get the minimum and maximum values for the 'Price Each' column
    min_price = df['Price Each'].min()
    max_price = df['Price Each'].max()

    # Create a price range slider on the sidebar
    price_range = st.sidebar.slider(
        'Filter Product Price',
        min_value=float(min_price),
        max_value=float(max_price),
        value=(float(min_price), float(max_price)),
        step=0.01,  # Assuming price can have cents; adjust step if needed
        format="%.2f"  # Format as a float with two decimal places
    )

    # Filter the DataFrame based on the selected price range
    df = df[(df['Price Each'] >= price_range[0]) & (df['Price Each'] <= price_range[1])]
    
    st.markdown("# Filtered data")    
    st.write(df)

    st.markdown("# Important Zip Codes")    

    # Group by 'Zip' column and calculate the sum of 'Total' and 'Count' columns separately
    total_sales_df = df.groupby('Zip')['Total'].sum().reset_index().sort_values(by='Total', ascending=False)
    total_count_df = df.groupby('Zip')['Count'].sum().reset_index().sort_values(by='Count', ascending=False)

    # Calculate total sum of sales and count across all zip codes
    total_sales_all = total_sales_df['Total'].sum()
    total_count_all = total_count_df['Count'].sum()

    # Calculate the percentage of total sales and total count for each zip code
    total_sales_df['Percentage'] = (total_sales_df['Total'] / total_sales_all) * 100
    total_count_df['Percentage'] = (total_count_df['Count'] / total_count_all) * 100

    # Create four columns for displaying DataFrames side by side
    col1, col2 = st.columns(2)

    # Display total sales by zip code in the first column
    with col1:
        st.write("Total Sales by Zip:")
        st.write(total_sales_df)

    # Display total count by zip code in the second column
    with col2:
        st.write("Total Number Sold by Zip:")
        st.write(total_count_df)





    daily_sales = df.groupby('Day')['Total'].sum()

    st.markdown("# Line Graph of Daily Sales")    
    st.line_chart(daily_sales)




    grouped_sum_df = df.groupby('Product')['Price Each'].sum().reset_index()
    sorted_grouped_sum_df = grouped_sum_df.sort_values(by='Price Each', ascending=False)
    sorted_grouped_sum_df['Price Each'] = sorted_grouped_sum_df['Price Each'].round()

    # Create three columns
    left_column, middle_column, right_column = st.columns(3)

    # Display sorted grouped sum DataFrame and address input in the left column
    with left_column:
        st.markdown("## Big ticket items")
        st.write(sorted_grouped_sum_df)


    # Display product value counts DataFrame in the middle column
    with middle_column:
        st.markdown("## Most sold items")
        st.write(df.Product.value_counts())

    # Display sum of 'Price Each' grouped by 'Purchase Address' in the right column
    with right_column:
        st.markdown("## Favorite Customers")
        address_grouped_sum_df = df.groupby('Purchase Address')['Price Each'].sum().reset_index()
        address_grouped_sum_df = address_grouped_sum_df.sort_values(by='Price Each', ascending=False)
        address_grouped_sum_df['Price Each'] = address_grouped_sum_df['Price Each'].round()
        st.write(address_grouped_sum_df)

    # Group by 'Zip' column and calculate the sum of 'Total' and 'Count' columns




    
    st.markdown("## Filter by Product")

    search_item = st.text_input("Enter Item", "")

    # Filter the DataFrame based on the search input
    filtered_df = df[df['Product'].str.contains(search_item, case=False, na=False)]

    # Display the filtered DataFrame
    st.write(filtered_df)

    st.markdown("## Filter by Address or ZIP")

    # Get user input for address search
    search_address = st.text_input("Enter Address", "")

    # Filter the DataFrame based on the search input
    filtered_df = df[df['Purchase Address'].str.contains(search_address, case=False, na=False)]

    # Display the filtered DataFrame
    st.write(filtered_df)
