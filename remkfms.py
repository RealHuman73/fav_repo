import streamlit as st
import pandas as pd
import random
import numpy as np
from datetime import datetime

def create_page():
    st.subheader("Create a New Collab page")    

    st.session_state.page_title = st.text_input("Page Title", key = "pagetitlekey")
    page_title = st.session_state.page_title

    if len(page_title) > 0:
        st.write(f"Page Title: {page_title}")
    else:
        st.write("Title required")

    st.session_state.responses['form_password'] = st.text_input("Create form password (optional).", key = "pagepasswordkey")
    form_password = st.session_state.responses['form_password']

    if len(form_password) > 0:
        st.write(f"Form Password: {form_password}")
    else:
        st.write("Add a password (optional)")

def define_section_list():
    # Define the section types
    section_types = [
        'radio', 'multiselect', 'text_entry', 'table_entry', 'file_import', 
        'chat_thread', 'add_url', 'radio', 'multiselect', 'text_entry', 
        'table_entry', 'file_import', 'chat_thread', 'add_url'
    ]
    
    # Set the default value to an empty list for no pre-selected options
    selected_section_list = st.multiselect(
        "Choose page elements", 
        section_types,
        default=[], key = "choose page elements"
    )
    
    # Optionally, update session state or handle selected_section_list
    st.session_state.section_list['section_types'] = selected_section_list
    st.write("Selected Section List:", selected_section_list)

    num_sections = len(selected_section_list)

    # Example of initialization to ensure all lists have `num_sections` rows
    for key in ['section_titles', 'entry_opts', 'section_id', 'numeric_lists', 'tables', 'file_binaries']:
        while len(st.session_state.section_list[key]) < num_sections:
            if key in ['numeric_lists', 'tables', 'file_binaries']:
                st.session_state.section_list[key].append([])  # Or append a default value
            else:
                st.session_state.section_list[key].append('')  # Or append a default value

    for i, section in enumerate(selected_section_list):
        if section == 'radio':
            st.write("RADIO")
            create_radio_button(i)
            st.write("----")
        elif section == 'multiselect':
            st.write('MULTISELECT')
        elif section == 'text_entry':
            st.write('TEXT_ENTRY')
        elif section == 'table_entry':
            st.write('TABLE_ENTRY')
            create_table(i)
            st.write("----")
        elif section == 'file_import':
            st.write('FILE_IMPORT')
        elif section == 'chat_thread':
            st.write('CHAT_THREAD')
        elif section == 'add_url':
            st.write('ADD_URL')
        else:
            st.write("Choose section types")


def create_radio_button(section_index):
    new_section_title = st.text_input("Section Title", key=f"{section_index}_title")

    num_rows = st.number_input("Number of Rows", min_value=1, max_value=100, value=1, key=f"{section_index}_rows")

    # Initialize DataFrame with user inputs
    df = pd.DataFrame('', index=range(num_rows), columns=["Enter radio opts"])
    df = st.data_editor(df, use_container_width=True, key=f"{section_index}_radio")

    # Update the session state
    section_list = st.session_state.section_list
    if section_index < len(section_list['section_titles']):
        st.session_state.section_list['section_titles'][section_index] = new_section_title
        st.session_state.section_list['entry_opts'][section_index] = df
        st.session_state.section_list['section_id'][section_index] = section_index
    else:
        st.write("Index out of range")


def make_radio(section_index, section_title, entry_opts):
    entry_opts = pd.DataFrame(entry_opts)    
    options = entry_opts["Enter radio opts"].dropna().tolist()
    responses = st.radio(section_title, options = options, key = f"{section_index} radio")
    return responses

def create_table(section_index):
    new_section_title = st.text_input("Section Title", key=f"{section_index}_title")

    # Initialize DataFrame with user inputs
    uploaded_file = st.file_uploader("Upload Template Table (.csv only)", type="csv", key=f"{section_index}_template")
    
    if uploaded_file is not None:
        # Read CSV file into DataFrame
        uploaded_file_df = pd.read_csv(uploaded_file)
        st.session_state.section_list['tables'][section_index] = uploaded_file_df
        st.session_state.section_list['section_titles'][section_index] = new_section_title
        st.session_state.section_list['section_id'][section_index] = section_index
    else:
        st.warning("Template table upload required")

def make_table(section_index, section_title, table):    
    st.write(section_title)
    responses = st.data_editor(table, key = f"{section_index}_data_editor")
    return responses

def display_page():
    page_title = st.session_state.page_title

    entry_opts = st.session_state.section_list['entry_opts']
    section_titles = st.session_state.section_list['section_titles']
    section_types = st.session_state.section_list['section_types']
    section_index = st.session_state.section_list['section_id']
    numeric_lists = st.session_state.section_list['numeric_lists']
    tables = st.session_state.section_list['tables']
    file_binaries = st.session_state.section_list['file_binaries']

    # Check if all lists have the same length
    if (len(entry_opts) == len(section_titles) == len(section_types) == len(section_index) and
        all(title.strip() for title in section_titles) and  # Ensure no empty titles
        len(section_titles) == len(set(section_titles))): 
        st.session_state.assembled_page = pd.DataFrame({
            'Index': section_index,
            'Section Title': section_titles,
            'Section Type': section_types,
            'Entry Options': entry_opts,
            'Numeric_lists': numeric_lists,
            'Tables': [pd.DataFrame(table) if not isinstance(table, pd.DataFrame) else table for table in tables],
            'Binaries': file_binaries
        })

        assembled_page = st.session_state.assembled_page

        st.subheader(f"Page: {page_title}")
        st.write(section_types)    
        st.write(section_titles)  

        for index, row in assembled_page.iterrows():
            st.write(f"Index: {row['Index']}")
            st.write(f"Section Title: {row['Section Title']}")
            st.write(f"Section Type: {row['Section Type']}")
            if row['Section Type'] == 'radio':
                user_choices = make_radio(row['Index'], row['Section Title'], row['Entry Options'])
                st.write(row['Index'])
                st.write(row['Section Title'])
                st.write(row['Entry Options'])
                st.write("----")
            elif row['Section Type'] == 'table_entry':
                user_choices = make_table(row['Index'], row['Section Title'], row['Tables'])        
                st.write("----")
            else:
                pass
    else:
        st.markdown(
            """
            <h5 style='color: #007BA7;'>Error: All sections must have section titles &<br>All section titles must be unique.</h5>
            """,
            unsafe_allow_html=True
        )

def initialize_responses():
    if 'responses' not in st.session_state:
        st.session_state.responses = {
            'form_titles': [],
            'form_passwords': [],
            'form_dictionaries': {},
            'time_stamps': [] 
        }

def add_empty_row_responses(row_index):
    if 'responses' in st.session_state:
        st.session_state.responses['form_titles'].insert(row_index, '')
        st.session_state.responses['form_passwords'].insert(row_index, '')
        st.session_state.responses['form_dictionaries'].insert(row_index, {})
        st.session_state.responses['time_stamps'].insert(row_index, datetime.min)

def initialize_section_list():
    if 'section_list' not in st.session_state:
        st.session_state.section_list = {
            'entry_opts': [],   
            'section_titles': [],
            'section_types': [],
            'section_id': [],
            'numeric_lists': [],  
            'tables': [], 
            'file_binaries': []
        }

# Set the page layout to wide
st.set_page_config(layout="wide")

# Initialize top-level session state variables
if 'page_title' not in st.session_state:
    st.session_state.page_title = ''

if 'assembled_page' not in st.session_state:
    st.session_state.assembled_page = {
    }

if 'section_list' not in st.session_state:
    initialize_section_list()

if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False


initialize_responses()
initialize_section_list()


col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("Create Page")
    create_page()
    st.write("Add sections to the page")
    define_section_list()
    if st.button('Update Content'):
        st.session_state.button_clicked = True

with col2:
    st.subheader("Display Page")
    if st.session_state.button_clicked:
        display_page()
