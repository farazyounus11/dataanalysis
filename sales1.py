import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import re

st.set_page_config(layout="wide")
st.title("Sales Data Analysis")
st.header('By Faraz Younus | M.S. Stats & Data Science', divider='gray')
st.header('Select month for Visualization!')


## This code Imports Monthly Sales Data
files = os.listdir('.')
csv_files = [file for file in files if file.endswith('.csv')]
if not csv_files:
    st.write("No CSV files found in the current directory.")
else:
    selected_file = st.selectbox('Month', csv_files)
    if st.button('Select'):
        st.session_state['selected_file'] = selected_file



if 'selected_file' in st.session_state:
    # Reading the selected CSV file from session state
    df = pd.read_csv(st.session_state['selected_file'])
    df.rename(columns={'Quantity Ordered': 'Count'}, inplace=True)


    ## Code helps get total
    df['Count'] = pd.to_numeric(df['Count'], errors='coerce')
    df['Price Each'] = pd.to_numeric(df['Price Each'], errors='coerce')
    df['Total'] = df['Count'] * df['Price Each']


    zip_code_pattern = r'\b\d{5}(?:-\d{4})?\b'
    df['Zip'] = df['Purchase Address'].apply(lambda x: re.search(zip_code_pattern, str(x)).group() if pd.notnull(x) and re.search(zip_code_pattern, str(x)) else None)
    df['Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%y %H:%M', errors='coerce')
    df = df.drop(columns=['Order Date'])
    df['Day'] = df['Date'].dt.day



    hour_range = st.sidebar.slider(
        "Filter the Hour of Day",
        0, 24, (0, 24),
        step=1,  # Hour steps
        format="%d hours")

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
    
    st.markdown("## Filtered data")    
    st.write(df)

    daily_sales = df.groupby('Day')['Total'].sum()
    average_daily_sales = daily_sales.mean()
    std_daily_sales = daily_sales.std()

    # Calculate average hourly sales
    hourly_sales = df.groupby('Hour')['Total'].sum()
    average_hourly_sales = hourly_sales.mean()
    std_hourly_sales = hourly_sales.std()

    # Create two columns
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average Daily Sales", average_daily_sales.round(-1), f"Std Dev: {std_daily_sales.round(-1)}")
    with col2:
        st.metric("Average Hourly Sales", average_hourly_sales.round(-1), f"Std Dev: {std_hourly_sales.round(-1)}")

    st.markdown("### Notice the high Std Dev of Hourly sales. You will see that in the plot!")    



    st.markdown("## Plot of Daily Sales")
    st.line_chart(daily_sales)

    st.markdown("## Plot of Hourly Sales")    
    st.line_chart(hourly_sales)
    st.markdown("#### The above plot shows that it's optimized to have call center open after 8A.M.!!")    



    st.markdown("## Important Zip Codes")    

    total_sales_df = df.groupby('Zip')['Total'].sum().reset_index().sort_values(by='Total', ascending=False)
    total_count_df = df.groupby('Zip')['Count'].sum().reset_index().sort_values(by='Count', ascending=False)

    # Calculate total sum of sales and count across all zip codes
    total_sales_all = total_sales_df['Total'].sum()
    total_count_all = total_count_df['Count'].sum()

    # Calculate the percentage of total sales and total count for each zip code
    total_sales_df['Percentage'] = (total_sales_df['Total'] / total_sales_all) * 100
    total_count_df['Percentage'] = (total_count_df['Count'] / total_count_all) * 100

    total_sales_df.reset_index(drop=True, inplace=True)
    total_count_df.reset_index(drop=True, inplace=True)
    total_count_df.index += 1 
    total_sales_df.index += 1
    col1, col2 = st.columns(2)
    with col1:
        st.write("Total Sales by Zip:")
        st.write(total_sales_df)
    with col2:
        st.write("Total Numbers Sold by Zip:")
        st.write(total_count_df)

    def format_dataframe(df, max_cell_length):
        formatted_df = df.copy()
        for column in formatted_df.columns:
            formatted_df[column] = formatted_df[column].astype(str).str.slice(0, max_cell_length)
        return formatted_df
    grouped_sum_df = df.groupby('Product')['Price Each'].sum().reset_index()
    sorted_grouped_sum_df = grouped_sum_df.sort_values(by='Price Each', ascending=False)
    sorted_grouped_sum_df['Price Each'] = sorted_grouped_sum_df['Price Each'].round()
    sorted_grouped_sum_df.reset_index(drop=True, inplace=True)
    address_grouped_sum_df = df.groupby('Purchase Address')['Price Each'].sum().reset_index()
    address_grouped_sum_df = address_grouped_sum_df.sort_values(by='Price Each', ascending=False)
    address_grouped_sum_df['Price Each'] = address_grouped_sum_df['Price Each'].round()
    address_grouped_sum_df.reset_index(drop=True, inplace=True)

    max_cell_length = 16  # Adjust this value as needed
    formatted_sorted_grouped_sum_df = format_dataframe(sorted_grouped_sum_df, max_cell_length)
    formatted_address_grouped_sum_df = format_dataframe(address_grouped_sum_df, max_cell_length)

    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.markdown("### Big ticket items")
        st.write(formatted_sorted_grouped_sum_df)
    with middle_column:
        st.markdown("### Most sold items")
        st.write(df.Product.value_counts())
    with right_column:
        st.markdown("### Valued Customers")
        st.write(formatted_address_grouped_sum_df)

    
    def filter_dataframe(df, filter_type, search_input):
        if filter_type == "Product Name":
            filtered_df = df[df['Product'].str.contains(search_input, case=False, na=False)]
        elif filter_type == "Address or ZIP":
            filtered_df = df[df['Purchase Address'].str.contains(search_input, case=False, na=False)]
        else:
            filtered_df = df  # No filtering if filter_type is not recognized
        return filtered_df

    # Main code
    st.markdown("## Filter Table by Product Name or Address")
    filter_type = st.selectbox("Select Filter Type", ["Product Name", "Address or ZIP"])
    search_input = st.text_input("Enter Search Term", "")
    filtered_df = filter_dataframe(df, filter_type, search_input)
    st.write(filtered_df)
