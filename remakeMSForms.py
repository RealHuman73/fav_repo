import streamlit as st
import pandas as pd
import json
from sqlalchemy import Table, MetaData, insert, update, create_engine, text, select


def json_to_dataframe(json_str):
    if isinstance(json_str, str):  # Ensure json_str is a string
        return pd.read_json(json_str, orient='split')
    return pd.DataFrame()  # Return an empty DataFrame if input is not a string

def dataframe_to_json(df):
    return df.to_json(orient='split')

def load_questionnaire_data():
    sql_data = pd.read_sql('initial_blank_table', engine)

    if 'Project' not in sql_data.columns:
        seed_data = pd.DataFrame({
            'Project': ["New Project (Default)"],
            'QandA': [df0_json],
            'Timestamp': [pd.Timestamp.now()]
            })
        seed_data.to_sql('initial_blank_table', engine, if_exists='replace', index=False)

    questionnaire_data_dict = {
        'Project': sql_data['Project'].tolist(),
        'QandA': sql_data['QandA'].tolist(),
        'Timestamp': sql_data['Timestamp'].tolist()
    }
    questionnaire_data = pd.DataFrame(questionnaire_data_dict)
    questionnaire_data['QandA'] = questionnaire_data['QandA'].apply(json_to_dataframe)
    return questionnaire_data

def json_to_dataframe(json_str):
    if isinstance(json_str, str):  # Ensure json_str is a string
        return pd.read_json(json_str, orient='split')
    return pd.DataFrame()  # Return an empty DataFrame if input is not a string

def reset_session_state():
    if 'questionnaire_data' in st.session_state:
        del st.session_state['questionnaire_data']
    if 'active_index' in st.session_state:
        del st.session_state['active_index']
    if 'responses' in st.session_state:
        del st.session_state['responses']
    if 'project_title' in st.session_state:
        del st.session_state['project_title']

def remove_duplicates():
    df_existing = pd.read_sql('initial_blank_table', engine)    
    df_cleaned = df_existing.drop_duplicates(subset=['QandA', 'Project'], keep='last')    
    df_cleaned.to_sql('initial_blank_table', engine, if_exists='replace', index=False)    


# Create DataFrame for each project
df0 = pd.DataFrame({'Question': ['How?', 'Why?', 'Who?'], 'Answer': ['', '', '']})
df0_json = df0.to_json(orient='split')

# Database connection parameters
db_user = 'moi'
db_password = 'password'
db_host = 'localhost'
db_port = '5432'
db_name = 'xenon'

# Create a db connection
connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(connection_string)

remove_duplicates()

# Load the data
df = load_questionnaire_data()
st.session_state.questionnaire_data = df

# Dropdown to select a project
project_title = st.selectbox("Select Form:", st.session_state.questionnaire_data['Project'])
st.session_state.project_title = project_title

# Use selected project to find active_index
project_title_list = st.session_state.questionnaire_data['Project'].tolist()
active_index = project_title_list.index(project_title)
st.session_state.active_index = active_index

# Get the corresponding QandA DataFrame
selected_QandA = st.session_state.questionnaire_data['QandA'][active_index]
st.session_state.responses = st.session_state.questionnaire_data['QandA'][active_index]['Answer']

# show new Project Title text entry box
if active_index == 0:
    project_title = st.text_input("Enter New Project Title", key="newproject")
    st.session_state.project_title = project_title
else:
    pass

# Create or update responses
for index, row in selected_QandA.iterrows():
    user_input = st.text_input(
        f"Q{index + 1} of {len(selected_QandA)}",
        value=row['Answer'],
        key=f"answer_{index}"
    )
    if index < len(st.session_state.responses):
        st.session_state.responses[index] = user_input
    else:
        st.session_state.responses.append(user_input)


if st.button("Populate Form", key="newform"):
    active_index = st.session_state.active_index
    if active_index == 0:
        if project_title and project_title not in st.session_state.questionnaire_data['Project']:
            active_index = len(project_title_list) 
            st.session_state.active_index = active_index
            st.success("Form Updated")
        else:
            st.warning("Please enter a valid project title.")

    else:
        st.success("Form Updated")


test_df = pd.DataFrame({
    'Question': df0['Question'],
    'Answer': st.session_state.responses
})

st.write("Please double-check form below before clicking \'Save\':")
st.write(test_df)

test_df_json = test_df.to_json(orient='split')

new_row = {
    'Project': project_title,
    'QandA': test_df_json,
    'Timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
}

metadata = MetaData()
table = Table('initial_blank_table', metadata, autoload_with=engine)


if st.button("Save", key="save_to_db"):
    if isinstance(new_row, dict) and project_title != "New Project (Default)":
        try:
            with engine.connect() as connection:
                # Check if the project already exists
                query = select(table).where(table.c.Project == project_title)
                result = connection.execute(query).fetchone()

                if result:
                    # If project exists, update the row
                    update_stmt = update(table).where(table.c.Project == project_title).values(QandA=new_row['QandA'], Timestamp=new_row['Timestamp'])
                    with engine.connect() as connection:
                        with connection.begin():
                            connection.execute(update_stmt)
                    st.success("Form updated in the database.")
                else:
                    # If project does not exist, insert a new row
                    insert_stmt = insert(table).values(new_row)
                    with engine.connect() as connection:
                        with connection.begin():          
                            connection.execute(insert_stmt)
                    st.success("Form saved to the database.")
                    
        except Exception as e:
            st.error(f"Error saving to the database: {e}")
    elif project_title == "New Project (Default)":
        st.write("Form not saved. Project title required for new project requests.")
    else:
        st.error("Active form is not in the correct format.")
