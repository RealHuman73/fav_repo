import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")

def load_csv(uploaded_file):
    """Load CSV file from the uploaded file."""
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    else:
        return None

def load_excel(uploaded_file):
    """Load all sheets from an Excel file."""
    if uploaded_file is not None:
        excel_file = pd.ExcelFile(uploaded_file)
        return {sheet_name: excel_file.parse(sheet_name) for sheet_name in excel_file.sheet_names}
    else:
        return {}

def display_dimensions(df, title):
    """Display the dimensions of a DataFrame."""
    st.write(f"**{title}**")
    st.write(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

def convert_df_to_csv(df):
    """Convert DataFrame to CSV."""
    return df.to_csv(index=False).encode('utf-8')

st.title('Table Join Tool')
st.subheader('Join 2 or more tables based on shared columns')

# Upload files
uploaded_files = st.file_uploader("Choose CSV or Excel files", accept_multiple_files=True)

dfs_dict = {}
if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.csv'):
            df = load_csv(uploaded_file)
            if df is not None:
                dfs_dict[uploaded_file.name] = df
        elif uploaded_file.name.endswith('.xlsx'):
            sheets = load_excel(uploaded_file)
            for sheet_name, df in sheets.items():
                dfs_dict[f"{uploaded_file.name} - {sheet_name}"] = df

    # Show the tables and their dimensions in an expandable section
    st.markdown(f"<h4 style='color: #C83D95;'>View Uploaded Tables</h4>", unsafe_allow_html=True)
    with st.expander("Dropdown:"):
        for name, df in dfs_dict.items():
            display_dimensions(df, name)
            st.dataframe(df, use_container_width=True)

    # Column pairings
    st.markdown(f"<h4 style='color: #480091;'>Choose Tables to Join</h4>", unsafe_allow_html=True)

    if len(dfs_dict) > 1:
        # Dynamic table joining
        num_tables = st.slider("Select the number of input tables to join", min_value=2, max_value=10, value=2)

        selected_tables = [st.selectbox(f"Select table {i+1}", options=list(dfs_dict.keys()), key=f"table_{i}") for i in range(num_tables)]

        column_mappings = []
        for i in range(num_tables - 1):
            df1_name = selected_tables[i]
            df2_name = selected_tables[i + 1]

            if df1_name in dfs_dict and df2_name in dfs_dict:
                df1 = dfs_dict[df1_name]
                df2 = dfs_dict[df2_name]

                df1_cols = df1.columns
                df2_cols = df2.columns

                st.markdown(f"<h4 style='color: #007BA7;'>Select columns to join between {df1_name} and {df2_name}</h4>", unsafe_allow_html=True)
                left_col = st.selectbox(f"Select column from {df1_name}", options=[''] + list(df1_cols), key=f"left_col_{i}")
                right_col = st.selectbox(f"Select column from {df2_name}", options=[''] + list(df2_cols), key=f"right_col_{i}")
                if left_col and right_col:
                    column_mappings.append((df1_name, left_col, df2_name, right_col))
            else:
                st.write("Please select valid tables from the uploaded data.")

        # Join type selection
        st.markdown(f"<h4 style='color: #E66C27;'>Select Join type</h4>", unsafe_allow_html=True) 
        st.markdown(f"<h6 style='color: #094782;'>About join types:<br>- Inner joins the intersection of common columns<br>- Outer gives the union of common columns<br>- Left joins all items in the first table, but drops values joining values unique to the second table<br>- Right does the opposite of left</h6>", unsafe_allow_html=True)
        join_type = st.selectbox(
            "Select",
            options=['inner', 'left', 'right', 'outer']
        )

        # Perform join operation
        if st.button('Perform Joins'):
            if not column_mappings:
                st.write("No valid columns selected for joining.")
            else:
                result_df = None
                pre_join_dimensions = []

                for df1_name, left_col, df2_name, right_col in column_mappings:
                    df1 = dfs_dict[df1_name]
                    df2 = dfs_dict[df2_name]
                    
                    # Record dimensions before join
                    pre_join_dimensions.append((df1_name, df1.shape))
                    pre_join_dimensions.append((df2_name, df2.shape))
                    
                    if result_df is None:
                        result_df = pd.merge(df1, df2, left_on=left_col, right_on=right_col, how=join_type)
                    else:
                        result_df = pd.merge(result_df, df2, left_on=left_col, right_on=right_col, how=join_type)
                
                if result_df is not None:
                    st.write("### Joined Data")
                    display_dimensions(result_df, "Resulting DataFrame")
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Provide download link for the CSV file
                    csv = convert_df_to_csv(result_df)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name='resulting_dataframe.csv',
                        mime='text/csv'
                    )
                else:
                    st.write("No valid joins were made.")
                
                # Display dimensions of each DataFrame before the join
                st.write("### Dimensions Before Join")
                for name, shape in pre_join_dimensions:
                    st.write(f"**{name}**: {shape[0]} rows x {shape[1]} columns")
    else:
        st.write("Please upload at least two tables to join.")

