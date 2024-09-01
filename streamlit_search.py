

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import streamlit as st
import zipfile
import io
import re 
import json


# Function to create a SQLAlchemy engine
def create_db_engine():
    db_user = 'moi'
    db_password = 'password'
    db_host = 'localhost'
    db_port = '5432'
    db_name = 'xenon'
    connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    return create_engine(connection_string)

# Function to fetch table rows
def fetch_table_rows(engine, table_name):
    query = f"SELECT * FROM {table_name}"
    with engine.connect() as connection:
        return pd.read_sql(query, connection)

# Function to delete rows from a table
def delete_rows(engine, table_name, selected_projects):
    try:
        column_name = '"Project"'  # Use quoted column name to handle case sensitivity

        if not selected_projects:
            st.error("No valid rows selected for deletion.")
            return 0

        # Build query to delete rows where Project is in the selected list
        # Handling the case for 'None' values separately
        none_selected = [p for p in selected_projects if p is None]
        non_none_selected = [p for p in selected_projects if p is not None]

        query_parts = []
        params = {}
        if non_none_selected:
            placeholders = ', '.join([f':project{i}' for i in range(len(non_none_selected))])
            query_parts.append(f"{column_name} IN ({placeholders})")
            params.update({f'project{i}': project for i, project in enumerate(non_none_selected)})

        if none_selected:
            query_parts.append(f"{column_name} IS NULL")

        query = f"DELETE FROM {table_name} WHERE {' OR '.join(query_parts)}"

        # Print the query and parameters for debugging
        st.write(f"Executing query: {query}")
        #st.write(f"Parameters: {params}")

        # Execute the query with parameters
        with engine.connect() as connection:
            result = connection.execute(text(query), params)
            connection.commit()  # Commit the transaction to make sure changes are saved

        st.write(f"Rows deleted: {result.rowcount}")
        return result.rowcount
    except SQLAlchemyError as e:
        st.error(f"An error occurred while deleting rows: {e}")
        return 0


def check_password(password):
    if password == CORRECT_PASSWORD:
        st.session_state.password_entered = True
    else:
        st.session_state.password_entered = False

# Function to create ZIP file with CSVs for selected rows
def create_zip_for_selected_rows(df, selected_projects):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        filtered_df = df[df['Project'].isin(selected_projects)]
        for index, row in filtered_df.iterrows():
            project_name = row['Project'] if not pd.isna(row['Project']) else 'None'
            timestamp_str = row['Timestamp'].strftime('%Y-%m-%d_%H-%M-%S')
            csv_filename = f'{sanitize_filename(project_name)}_{sanitize_filename(timestamp_str)}.csv'
            
            # Extract QandA and Timestamp
            qanda_json_str = row['QandA']  # Get the QandA data as a JSON string
            
            # Parse JSON string to dictionary
            try:
                qanda_json = json.loads(qanda_json_str)
            except json.JSONDecodeError:
                raise ValueError(f"Error decoding JSON for project: {project_name}")
            
            qanda_df = pd.DataFrame(qanda_json['data'], columns=qanda_json['columns'])
            
            # Create a CSV buffer with the QandA DataFrame
            csv_buffer = io.StringIO()
            qanda_df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            zip_file.writestr(csv_filename, csv_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# Function to create a CSV file buffer for a single row
# Function to create a CSV file buffer for a single row
def create_csv_for_single_row(df, project_name):
    # Filter the DataFrame for the given project_name
    single_row = df[df['Project'] == project_name]
    
    # Check if the DataFrame is empty
    if single_row.empty:
        raise ValueError(f"No data found for project: {project_name}")
    
    # Extract QandA and Timestamp
    qanda_json_str = single_row['QandA'].iloc[0]  # Get the QandA data as a JSON string
    
    # Parse JSON string to dictionary
    try:
        qanda_json = json.loads(qanda_json_str)
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding JSON for project: {project_name}")
    
    qanda_df = pd.DataFrame(qanda_json['data'], columns=qanda_json['columns'])
    timestamp_str = single_row['Timestamp'].iloc[0].strftime('%Y-%m-%d_%H-%M-%S')
    csv_filename = f'{sanitize_filename(project_name)}_{sanitize_filename(timestamp_str)}.csv'
    
    # Create a CSV buffer with the QandA DataFrame
    csv_buffer = io.StringIO()
    qanda_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue(), csv_filename

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)


CORRECT_PASSWORD = "password"
st.session_state.password_entered = False

# Streamlit UI
st.markdown(
    """
    <h2 style='color:#2F4F4F;'>Download & Delete Forms from Database</h2>
    """,
    unsafe_allow_html=True
)

# Create database engine
engine = create_db_engine()

table_names = inspect(engine).get_table_names()
table_name = st.selectbox("Choose data class:", table_names)

st.markdown(
    """
    <hr><h4 style='color:#9932CC;'>SELECT</h4>
    """,
    unsafe_allow_html=True
)

# Main code
if table_name:
    df = fetch_table_rows(engine, table_name)
    if df is not None and not df.empty:
        st.write(f"Forms within data class '{table_name}':")

        selected_projects = []
        for index, row in df.iterrows():
            project_name = row['Project']  # Ensure your table has a 'Project' column
            if pd.isna(project_name):
                display_name = 'None (NULL)'
            else:
                display_name = project_name

            if st.checkbox(f"Select row {index+1}: {display_name}", key=f"row_{index}"):
                selected_projects.append(project_name if not pd.isna(project_name) else None)     


        st.markdown(
            """
            <hr><h4 style='color:#D49137;'>DOWNLOAD</h4>
            """,
            unsafe_allow_html=True
        )

        if st.button("Download Selected Forms as CSVs"):
            if selected_projects:
                if len(selected_projects) > 1:
                    zip_data = create_zip_for_selected_rows(df, selected_projects)
                    st.download_button(
                        label="Download ZIP",
                        data=zip_data,
                        file_name="selected_forms.zip",
                        mime="application/zip"
                    )
                else:
                    # Download single CSV file
                    project_name = selected_projects[0]
                    try:
                        csv_data, csv_filename = create_csv_for_single_row(df, project_name)
                        sanitized_filename = sanitize_filename(csv_filename)
                        st.download_button(
                            label=f"Download {sanitized_filename}",
                            data=csv_data,
                            file_name=sanitized_filename,
                            mime="text/csv"
                        )
                    except ValueError as e:
                        st.error(str(e))
            else:
                st.error("No rows selected for download or incorrect password")

        st.markdown(
            """
            <hr><h4 style='color:#BE398D;'>DELETE</h4>
            """,
            unsafe_allow_html=True
        )
        password = st.text_input("Enter password to unlock delete button:", type='password')
        check_password(password)
        if st.session_state.password_entered:

            if st.button("Delete Selected Forms"):
                
                if selected_projects:
                    rows_deleted = delete_rows(engine, table_name, selected_projects)
                    st.success(f"Deleted {rows_deleted} rows from table '{table_name}'.")
                    # Refresh the table view
                    df = fetch_table_rows(engine, table_name)
                    if df is not None and not df.empty:
                        st.write(f"Updated rows from table '{table_name}':")
                        st.dataframe(df)
                else:
                    st.error("No rows selected for deletion or incorrect password")
        else:
            st.write("Please reach out to Anna Bird with deletion requests")

    else:
        st.write(f"No rows found in table '{table_name}'.")


