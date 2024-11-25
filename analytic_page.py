import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from query import fetch_countries, fetch_questions, fetch_data_and_count
from db_connect import connect_to_database
from mysql.connector import Error
import io
import json

# Ensure users are logged in
def check_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Please log in to access this feature.")
        st.stop()  # Stop further execution if not logged in

# Function to save plot as JSON to the database
def save_plot_to_db_as_json(user_email, plot_name, plot_json, analysis_text=None):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        # Save the plot JSON data to the database
        cursor.execute("""
            INSERT INTO report_history (user_email, report_name, report_data, analysis_text, generated_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (user_email, plot_name, plot_json, analysis_text))
        conn.commit()
        st.success("Plot saved to your history!")
    except Error as e:
        st.error(f"Error saving plot: {e}")
    finally:
        cursor.close()
        conn.close()

def create_csv_from_plot_data(plot_data, question_code):
    # Extract data from the plot's traces
    rows = []
    for trace in plot_data['data']:
        x_values = trace['x']  # Categories or values from the plot
        y_values = trace['y']  # Counts
        country = trace['name']  # Country name (trace name)

        # Create rows for each trace
        for x, y in zip(x_values, y_values):
            rows.append({'Country': country, question_code: x, 'Count': y})

    # Convert rows to a DataFrame
    df = pd.DataFrame(rows)

    # Prepare CSV in-memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return csv_buffer.getvalue()

def analytics_page():
    check_login()

    st.title("📊 Analyze Student Performance")

    # Sidebar Filters
    oecd_status = st.sidebar.radio("Select OECD Status", ("All", "OECD", "NON-OECD"))
    countries = fetch_countries(oecd_status)
    selected_countries = st.multiselect("Select Countries", countries)

    # Question Selection
    question_codes = fetch_questions()
    selected_question_tuple = st.selectbox("Select Question", list(question_codes.items()), format_func=lambda x: x[1])

    # Gender Filter
    gender_options = ["All", "Male", "Female"]
    selected_genders = st.pills("Filter by Gender", gender_options, selection_mode="multi")
    if not selected_genders:
        selected_genders = ["All"]

    # Plot Type Selection
    selected_plot_type = st.sidebar.selectbox("Select Plot Type", ["Bar Plot", "Scatter Plot", "Histogram"])

    # Toggle for Filtering Values = 0
    filter_zero_values = st.toggle("Filter out question responses with value = 0 (No data or Response)", value=True)

    if selected_countries and selected_question_tuple:
        selected_question_code = selected_question_tuple[0]
        selected_question_text = selected_question_tuple[1]

        # Fetch Data
        data_counts = fetch_data_and_count(oecd_status, selected_genders, selected_countries, selected_question_code)

        # Process Data Based on Toggle
        valid_dataframes = []
        for country, data in data_counts.items():
            counts_df = data["counts_df"]

            # Filter rows based on the toggle for question values
            if  filter_zero_values:
                counts_df = counts_df[counts_df[selected_question_code] != 0]

            if not counts_df.empty:
                counts_df = counts_df.assign(Country=country)
                valid_dataframes.append(counts_df)

        if valid_dataframes:
            csv_data = pd.concat(valid_dataframes)
            fig = go.Figure()

            for country, data in data_counts.items():
                counts_df = data["counts_df"]

                # Apply the same filter here
                if filter_zero_values:
                    counts_df = counts_df[counts_df[selected_question_code] != 0]

                if not counts_df.empty:
                    fig.add_trace(go.Bar(
                        x=counts_df[selected_question_code],
                        y=counts_df["Count"],
                        name=country,  # Ensure the country name is displayed
                        showlegend=True  # Explicitly show the legend even if there's only one trace
                    ))

             # Configure the layout to show only integers on the x-axis
            fig.update_layout(
                title=f"Counts of {selected_question_text} ({selected_question_code}) for Selected Countries",
                xaxis=dict(
                    title=f"{selected_question_code} ({selected_question_text})",
                    tickmode="linear",  # Ensure ticks are evenly spaced
                    dtick=1  # Set tick increment to 1
                ),
                yaxis=dict(
                    title="Count"
                ),
                barmode="group"
            )
            st.plotly_chart(fig)


            # Add codebook reference
            st.subheader("📖 Reference Codebook")
            st.markdown(
                """
                You can find the detailed codebook for questions here: 
                [Student Question Codebook](https://www.oecd.org/content/dam/oecd/en/data/datasets/pisa/pisa-2022-datasets/questionnaires/COMPUTER-BASED%20STUDENT%20questionnaire%20PISA%202022.pdf)
                """,
                unsafe_allow_html=True,
            )

            # User Analysis Input
            st.subheader("📝 Add Your Analysis (Optional)")
            analysis_text = st.text_area("Write your analysis here (optional)", placeholder="Describe your insights...")

            # Download CSV Button
            csv_buffer = create_csv_from_plot_data(fig.to_dict(), selected_question_code)
            # Download CSV and Save Plot Buttons
            col1, col2 = st.columns([1, 1])

            with col1:
                st.download_button(
                    label="Download Plot Data as CSV",
                    data=csv_buffer,
                    file_name=f"{selected_question_text}.csv",
                    mime="text/csv"
                )

            with col2:
                if st.button("Save Plot and Analysis to History"):
                    plot_json = fig.to_json()
                    user_email = st.session_state.get("user_email")
                    plot_name = f"{selected_plot_type} of {selected_question_text} ({', '.join(selected_genders)})"
                    save_plot_to_db_as_json(user_email, plot_name, plot_json, analysis_text if analysis_text.strip() else None)

        else:
            st.warning("No data available for the selected filters.")
    else:
        st.info("Please select at least one country and a question to generate the plot.")