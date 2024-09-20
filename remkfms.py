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






import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import itertools
import io
import numpy as np
import zipfile
from scipy.stats import spearmanr
from adjustText import adjust_text
from statsmodels.stats.multitest import multipletests



def create_dot_plot(data, x_col, y_col, label_param, color_col, stats_type, colormap):
    fig, ax = plt.subplots(figsize=(10, 6))

    if color_col:
        if pd.api.types.is_numeric_dtype(data[color_col]):
            # If color_col is numeric, use it directly
            norm = plt.Normalize(data[color_col].min(), data[color_col].max())
            scatter = ax.scatter(data[x_col], data[y_col], 
                                 c=data[color_col], 
                                 cmap=colormap,
                                 norm=norm,
                                 edgecolor='black', 
                                 s=70,
                                 zorder=2)
            cbar = plt.colorbar(scatter, ax=ax, label=color_col, shrink=0.5)
        else:
            # If color_col is categorical, create a mapping
            unique_colors = data[color_col].unique()
            color_mapping = {category: idx for idx, category in enumerate(unique_colors)}
            color_values = data[color_col].map(color_mapping)

            norm = plt.Normalize(color_values.min(), color_values.max())
            scatter = ax.scatter(data[x_col], data[y_col], 
                                 c=color_values, 
                                 cmap=colormap,
                                 norm=norm,
                                 edgecolor='black', 
                                 s=70,
                                 zorder=2)
            cbar = plt.colorbar(scatter, ax=ax, label=color_col, shrink=0.5)
            cbar.set_ticks(range(len(unique_colors)))
            cbar.set_ticklabels(unique_colors)  # Set color bar labels to original categories
    else:
        scatter = ax.scatter(data[x_col], data[y_col], 
                             color='black', 
                             edgecolor='black', 
                             s=70,
                             zorder=2)

    if label_param:
        texts = []
        sample_data = data.sample(n=min(20, len(data)), random_state=1)
        
        offset_x = 0.01 * (data[x_col].max() - data[x_col].min())
        offset_y = 0.01 * (data[y_col].max() - data[y_col].min())

        for index, row in sample_data.iterrows():
            text = ax.text(row[x_col] + offset_x, row[y_col] + offset_y, str(row[label_param]), fontsize=12)
            texts.append(text)

        adjust_text(texts, 
                    force_points=1.0, 
                    force_text=1.0,
                    expand_points=(5, 5), 
                    expand_text=(1.5, 1.5), 
                    arrowprops=dict(arrowstyle="-", color='black', lw=0.5)
                    )
        
        # Adjust text positions to prevent them from going off the edges
        for text in texts:
            if text.get_position()[0] > ax.get_xlim()[1]:
                text.set_x(ax.get_xlim()[1] - 0.5)
            if text.get_position()[0] < ax.get_xlim()[0]:
                text.set_x(ax.get_xlim()[0] + 0.5)
            if text.get_position()[1] > ax.get_ylim()[1]:
                text.set_y(ax.get_ylim()[1] - 0.5)
            if text.get_position()[1] < ax.get_ylim()[0]:
                text.set_y(ax.get_ylim()[0] + 0.5)

        # Expand the plot limits if needed
        buffer_x = 0.05 * (data[x_col].max() - data[x_col].min())
        buffer_y = 0.05 * (data[y_col].max() - data[y_col].min())
        ax.set_xlim(data[x_col].min() - buffer_x, data[x_col].max() + buffer_x)
        ax.set_ylim(data[y_col].min() - buffer_y, data[y_col].max() + buffer_y)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.grid(True, zorder=1)

    if stats_type != 'None':
        stats = calculate_spearman_statistics(data, x_col, y_col)
        plt.title(f"{stats_type}: ρ={stats['rho']:.2f}, p-value={stats['p_value']:.4f}")

    return fig



# Function to calculate Spearman statistics
def calculate_spearman_statistics(data, x_col, y_col):
    data = data.dropna()
    rho, p_value = spearmanr(data[x_col], data[y_col])
    r_squared = rho ** 2
    return {'rho': rho, 'p_value': p_value, 'R²': r_squared}

# Streamlit App
st.title('Dot Plot Generator')

# File uploader
uploaded_file = st.file_uploader("Upload a .xlsx or .csv file", type=['xlsx', 'csv'])

if uploaded_file is not None:
    # Load the data
    if uploaded_file.name.endswith('.xlsx'):
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Select a sheet", sheet_names)
        data = pd.read_excel(xls, sheet_name=selected_sheet)
    else:
        data = pd.read_csv(uploaded_file)

    # Show the data
    st.write(data)

    # Determine numeric columns for plotting
    numeric_columns = data.select_dtypes(include='number').columns.tolist()

    if len(numeric_columns) < 2:
        st.warning("Need at least two numeric columns for plotting.")
    else:
        # Filtering options
        filter_column = st.selectbox("Select Numeric Column for Filtering", numeric_columns)
        filter_condition = st.selectbox("Select Condition", [None, '<', '>', '<=', '>='])
        threshold_value = st.number_input("Enter Threshold Value", value=0.0)

        if filter_condition == '<':
            filtered_data = data[data[filter_column] < threshold_value]
        elif filter_condition == '>':
            filtered_data = data[data[filter_column] > threshold_value]
        elif filter_condition == '<=':
            filtered_data = data[data[filter_column] <= threshold_value]
        elif filter_condition == '>=':
            filtered_data = data[data[filter_column] >= threshold_value]
        else:
            filtered_data = data

        st.write(f"Filtered Data (showing {len(filtered_data)} rows):")
        st.write(filtered_data)

        # Common selections for both modes
        x_axis = st.selectbox("Select X-axis", numeric_columns, index=0)
        y_axis = st.selectbox("Select Y-axis", numeric_columns, index=1)
        label_param = st.selectbox("Select Point Label Parameter", data.columns.tolist(), index=2)
        color_param = st.selectbox("Select Color Parameter (or None)", ['None'] + data.columns.tolist(), index=0)
        color_param = None if color_param == 'None' else color_param

        # Radio button for colormap selection
        colormap = st.radio("Select Colormap", ['turbo', 'viridis', 'magma', 'plasma'])

        # Radio button for mode selection
        mode = st.radio("Select Plotting Mode", ('Single Plot', 'All Combinations'))

        # Choose correlation type
        stats_type = st.selectbox("Select Statistics to Show", ('None', 'Spearman'))

        if mode == 'Single Plot':
            # Plot the single dot plot
            fig = create_dot_plot(filtered_data, x_axis, y_axis, label_param, color_param, stats_type, colormap)
            st.pyplot(fig)

            # Download button for the plot
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=600)
            buf.seek(0)
            st.download_button("Download Plot as PNG", buf, "dot_plot.png", "image/png")

        elif mode == 'All Combinations':
            plot_files = []  # List to store plot files
            correlation_results = []  # List to store correlation results

            # Generate all combinations of numeric columns for plotting
            for x_col, y_col in itertools.combinations(numeric_columns, 2):
                fig = create_dot_plot(filtered_data, x_col, y_col, label_param, color_param, stats_type, colormap)
                st.pyplot(fig)

                # Save each plot to a PNG file
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=600)
                buf.seek(0)
                plot_files.append((buf, f"{y_col}_vs_{x_col}.png"))

            # Download all plots as ZIP files
            if plot_files:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zf:
                    for buf, filename in plot_files:
                        zf.writestr(filename, buf.getvalue())
                zip_buffer.seek(0)

                st.download_button("Download All Plots as ZIP", zip_buffer, "plots.zip", "application/zip")












