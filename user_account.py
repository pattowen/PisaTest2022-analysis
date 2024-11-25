import streamlit as st
import plotly.graph_objects as go
import json
import pandas as pd 
import io
from db_connect import connect_to_database
from mysql.connector import Error
from query import fetch_questions


# Function to fetch saved plots from the database
def fetch_report_history(user_email):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT id, report_name, report_data, analysis_text, generated_at FROM report_history WHERE user_email = %s", (user_email,))
        reports = cursor.fetchall()  # Fetch all rows
        return reports  # Returns list of (id, report_name, report_data, generated_at)
    except Error as e:
        st.error(f"Error fetching report history: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Function to delete a plot by id
def delete_plot_from_db(plot_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM report_history WHERE id = %s", (plot_id,))
        conn.commit()
        st.success("Plot deleted successfully!")
    except Error as e:
        st.error(f"Error deleting plot: {e}")
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


def display_account_page():
    st.subheader("👤 Account Details")

    # Check if the user is logged in
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        user_email = st.session_state.get('user_email')

        st.write("### Your Saved Plots")
        reports = fetch_report_history(user_email)

        # Fetch question labels to map question codes to their text descriptions
        question_labels = fetch_questions()

        # Check if there are saved reports
        if reports:
            # Pagination controls
            items_per_page = 5
            total_reports = len(reports)
            total_pages = (total_reports + items_per_page - 1) // items_per_page
            page = st.number_input("Page", min_value=1, max_value=total_pages, step=1) - 1
            start = page * items_per_page
            end = start + items_per_page
            paginated_reports = reports[start:end]

            if not paginated_reports:
                st.info("No reports available for this page.")
                return

            # Loop over paginated reports
            for report in paginated_reports:
                report_id = report[0]
                report_name = report[1]
                report_data = report[2]
                analysis_text = report[3]  # Fetch analysis text
                generated_at = report[4]

                # Load JSON data and plot
                plot_data = json.loads(report_data)
                if not plot_data['data']:
                    st.warning(f"No data available for plot: {report_name}")
                    continue
                fig = go.Figure(plot_data)

                # Extract question code and find corresponding text description
                try:
                    question_code = report_name.split()[3]  # Ensure index exists
                except IndexError:
                    st.error(f"Unable to extract question code from report name: {report_name}")
                    question_code = "Unknown"
                question_text = question_labels.get(question_code, question_code)

                # Display report info
                st.subheader(f"Report: {report_name}")
                st.caption(f"Generated at: {generated_at}")
                st.plotly_chart(fig)
                st.write("### Analysis")
                st.write(analysis_text)  # Display the saved analysis text

                # Generate CSV data dynamically
                csv_data = create_csv_from_plot_data(plot_data, question_code)

                # Create two columns for buttons
                col1, col2 = st.columns([1, 1])
                with col1:
                    # Add download button for CSV
                    st.download_button(
                        label=f"Download CSV for {report_name}",
                        data=csv_data,
                        file_name=f"{question_text if question_text else 'plot'}.csv",
                        mime="text/csv"
                    )
                with col2:
                    if f"confirm_delete_{report_id}" not in st.session_state:
                        st.session_state[f"confirm_delete_{report_id}"] = False

                    if st.session_state[f"confirm_delete_{report_id}"]:
                        st.warning(f"Are you sure you want to delete the plot '{report_name}'?")
                        col_confirm1, col_confirm2 = st.columns([1, 1])
                        with col_confirm1:
                            if st.button("Delete", key=f"confirm_delete_yes_{report_id}"):
                                delete_plot_from_db(report_id)
                                st.rerun()  # Refresh the page after deletion
                        with col_confirm2:
                            if st.button("Cancel", key=f"confirm_delete_no_{report_id}"):
                                st.session_state[f"confirm_delete_{report_id}"] = False
                    else:
                        if st.button(f"Delete {report_name}", key=f"delete_{report_id}"):
                            st.session_state[f"confirm_delete_{report_id}"] = True

                st.markdown("---")
        else:
            st.info("You have no saved plots.")
    else:
        st.error("You are not logged in. Please log in to access this page.")
