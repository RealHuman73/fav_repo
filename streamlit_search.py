

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import streamlit as st

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


CORRECT_PASSWORD = "password"

st.session_state.password_entered = False

# Streamlit UI
st.title("Database Table Management")

# Create database engine
engine = create_db_engine()

table_names = inspect(engine).get_table_names()
table_name = st.selectbox("Choose data type:", table_names)

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


        password = st.text_input("Enter password to unlock the button:", type='password')
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
            st.write("Deletion allowed with correct pw")

    else:
        st.write(f"No rows found in table '{table_name}'.")


