import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from query import fetch_countries, fetch_questions, fetch_data_and_count, fetch_question_response_and_scores, fetch_histogram_questions, fetch_scores, fetch_heatmap_data
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
        if 'x' in trace and 'y' in trace:  # Bar, Scatter, Histogram
            x_values = trace['x']  # Categories or values from the plot
            y_values = trace['y']  # Counts
            country = trace.get('name', 'Unknown')  # Country name (trace name)

            # Create rows for each trace
            for x, y in zip(x_values, y_values):
                rows.append({'Country': country, question_code: x, 'Count': y})
        elif 'labels' in trace and 'values' in trace:  # Pie Chart
            labels = trace['labels']  # Categories for Pie Chart
            values = trace['values']  # Counts for Pie Chart
            country = trace.get('name', 'Unknown')  # Country name (trace name)

            # Create rows for the pie chart
            for label, value in zip(labels, values):
                rows.append({'Country': country, question_code: label, 'Count': value})

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

    # Plot Type Selection
    selected_plot_type = st.sidebar.selectbox("Select Plot Type", ["Bar Plot", "Scatter Plot", "Histogram", "Pie Chart", "Heatmap"])

    if selected_plot_type in ["Scatter Plot", "Pie Chart"]:
        # Single country selection for these plot types
        selected_country = st.selectbox("Select a Country", countries)
    else:
        # Multiple countries for other plot types
        selected_countries = st.multiselect("Select Countries", countries)

    # Fetch questions based on the plot type
    if selected_plot_type == "Histogram":
        question_codes = fetch_histogram_questions()  # Fetch only columns starting with "PV"
    else:
        question_codes = fetch_questions()

    # Question Selection
    selected_question_tuple = st.selectbox("Select Question", list(question_codes.items()), format_func=lambda x: x[1])
    selected_question_code = selected_question_tuple[0]
    selected_question_text = selected_question_tuple[1]

    # Gender Filter
    gender_options = ["All", "Male", "Female"]
    selected_genders = st.pills("Filter by Gender", gender_options, selection_mode="multi")
    if not selected_genders:
        selected_genders = ["All"]

    # Filter out responses with value = 0 
    filter_zero_values = False
    if selected_plot_type in ["Bar Plot", "Scatter Plot", "Histogram"]:
        filter_zero_values = st.toggle("Filter out question responses with value = 0 (No data or Response)", value=True)


    fig = None  # Initialize the figure to use it later in the CSV session

    if selected_plot_type == "Scatter Plot" and selected_country:
        # Add subject score selection
        score_options = ["math_score", "science_score", "reading_score", "overall_score"]
        selected_score = st.selectbox("Select Subject Score for Scatter Plot", score_options, format_func=lambda x: x.replace("_", " ").title())

        # Fetch data for Scatter Plot
        scatter_data = fetch_question_response_and_scores(
            question_code=selected_question_code,
            countries=[selected_country],  # Single country
            selected_score=selected_score,  # Use dynamically selected score
            oecd_status=oecd_status,
            genders=selected_genders
        )
        # Apply filter for zero responses if enabled
        if filter_zero_values:
            scatter_data = scatter_data[scatter_data["Response"] != 0]

        if not scatter_data.empty:
            # Create Scatter Plot
            fig = px.scatter(
                scatter_data,
                x="Response",
                y="Score",
                size="Count",
                color="Score",  # Color points by Score to show intensity
                color_continuous_scale="Viridis",
                opacity=0.8,
                labels={
                    "Response": f"{selected_question_text} (Responses)",
                    "Score": f"{selected_score.replace('_', ' ').title()}",
                    "Country": "Country"
                },
                title=f"Scatter Plot: {selected_question_text} vs {selected_score.replace('_', ' ').title()} ({selected_country})",
                height=600,
                width=900
            )

            # Update marker size and layout
            fig.update_traces(
                marker=dict(
                    sizemode="area",
                    sizeref=2. * max(scatter_data["Count"]) / (30. ** 2),
                    sizemin=3  # Minimum marker size for readability
                )
            )
            fig.update_layout(
                margin=dict(l=40, r=40, t=50, b=50),
                xaxis=dict(
                    tickmode="linear",
                    dtick=1,
                    title=f"{selected_question_text} (Responses)"
                ),
                yaxis=dict(
                    title=f"{selected_score.replace('_', ' ').title()}"
                ),
                coloraxis_colorbar=dict(title="Score"),  # Add a colorbar for Score
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig)
        else:
            st.warning("No data available for the selected filters.")

    if selected_plot_type == "Bar Plot" and selected_countries:
        # Toggle for grouped or stacked bar plot
        is_stacked = st.toggle("Stacked Bar Plot", value=False)

        # Fetch and process data for Bar Plot
        data_counts = fetch_data_and_count(oecd_status, selected_genders, selected_countries, selected_question_code)

        valid_dataframes = []
        for country, data in data_counts.items():
            counts_df = data["counts_df"]
            if filter_zero_values:
                counts_df = counts_df[counts_df[selected_question_code] != 0]
            if not counts_df.empty:
                counts_df = counts_df.assign(Country=country)
                valid_dataframes.append(counts_df)

        if valid_dataframes:
            csv_data = pd.concat(valid_dataframes)

            # Fetch scores and filter for selected countries
            score_data = fetch_scores(oecd_status)
            score_data = score_data[score_data["OverallCountry"].isin(selected_countries)]

            # Merge country scores with response counts
            merged_data = pd.merge(csv_data, score_data, left_on="Country", right_on="OverallCountry", how="left")

            # Create bar plot
            fig = px.bar(
                csv_data,
                x=selected_question_code,
                y="Count",
                color="Country",
                barmode="stack" if is_stacked else "group",  # Dynamic barmode based on toggle
                labels={
                    selected_question_code: f"{selected_question_text}",
                    "Count": "Response Count",
                    "Country": "Country"
                },
                title=f"Bar Plot for {selected_question_text} by Country",
            )


            st.plotly_chart(fig)

            # Show country scores in a table
            st.subheader("Country Scores")

            # Aggregate scores and rename columns
            country_scores = merged_data.groupby("Country").agg({
                "Count": "sum",  # Total student count
                "MathematicsScore": "mean",
                "ScienceScore": "mean",
                "ReadingScore": "mean",
                "OverallScore": "mean"
            }).reset_index()

            # Rename 'Count' column to 'Total Student' and shorten score column names
            country_scores.rename(columns={
                "Count": "Total Student",
                "MathematicsScore": "Math Score",
                "ScienceScore": "Science Score",
                "ReadingScore": "Reading Score",
                "OverallScore": "Overall Score"
            }, inplace=True)

            # Display the table with all scores
            st.dataframe(country_scores)
        else:
            st.warning("No data available for the selected filters.")


    elif selected_plot_type == "Pie Chart" and selected_country:
        # Fetch data for Pie Chart
        data_counts = fetch_data_and_count(oecd_status, selected_genders, [selected_country], selected_question_code)

        if selected_country in data_counts:
            counts_df = data_counts[selected_country]["counts_df"]
            counts_df = counts_df[counts_df[selected_question_code] != 0]
            if not counts_df.empty:
                # Create Pie Chart
                fig = px.pie(
                    counts_df,
                    names=selected_question_code,
                    values="Count",
                    title=f"Pie Chart: {selected_question_text} for {selected_country}",
                )
                st.plotly_chart(fig)

    elif selected_plot_type == "Histogram" and selected_countries:
        # Fetch data for Histogram
        histogram_data = fetch_question_response_and_scores(
            question_code=selected_question_code,
            countries=selected_countries,
            selected_score=None,  # Not applicable for Histogram
            oecd_status=oecd_status,
            genders=selected_genders
        )

        # Check if data is available
        if not histogram_data.empty:
            # Filter out rows with Response = 0 (if filter_zero_values is enabled)
            if filter_zero_values:
                histogram_data = histogram_data[histogram_data["Response"] != 0]

            # Dynamic bin count slider
            bin_count = st.sidebar.slider("Number of Bins", min_value=5, max_value=50, value=10, step=1)

            # Create Histogram
            fig = px.histogram(
                histogram_data,
                x="Response",
                color="Country",  # Different colors for each country
                barmode="overlay",  # Overlap bars for better comparison
                nbins=bin_count,  # Number of bins
                labels={
                    "Response": f"{selected_question_text} (Responses)",
                    "Country": "Country"
                },
                title=f"Histogram of {selected_question_text} by Country",
            )

            fig.update_layout(
                xaxis=dict(
                    title=f"{selected_question_text} (Responses)"
                ),
                yaxis=dict(
                    title="Number of Students"  # Updated y-axis label
                ),
                legend=dict(
                    title="Countries",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                height=600,
                width=900
            )
            st.plotly_chart(fig)
        else:
            st.warning("No data available for the selected filters.")

    elif selected_plot_type == "Heatmap":
        st.header("📊 Heatmap of Correlation for Selected Country")

        # Single country selection
        selected_country = st.selectbox(
            "Select a Country",
            countries,
            help="Choose one country for the heatmap."
        )

        # Default questions (e.g., FISCED and MISCED) with ability to select others
        default_questions = ["MISCED", "FISCED"]
        default_question_labels = [question_codes[q] for q in default_questions]

        # Question 1 selection
        selected_question1_label = st.selectbox(
            "Select Question 1",
            options=list(question_codes.values()),
            index=list(question_codes.values()).index(default_question_labels[0]),
            help="Choose the first question for the heatmap."
        )

        # Question 2 selection
        selected_question2_label = st.selectbox(
            "Select Question 2",
            options=list(question_codes.values()),
            index=list(question_codes.values()).index(default_question_labels[1]),
            help="Choose the second question for the heatmap."
        )

        # Map selected labels back to their question codes
        selected_questions = [
            next(code for code, label in question_codes.items() if label == selected_question1_label),
            next(code for code, label in question_codes.items() if label == selected_question2_label)
        ]

        # Add score selection
        selected_score = st.selectbox(
            "Select a Score for Heatmap",
            ["math_score", "science_score", "reading_score", "overall_score"],
            format_func=lambda x: x.replace("_", " ").title(),
            help="Choose a score metric for the heatmap."
        )

        # Fetch data for the heatmap
        try:
            heatmap_data = fetch_heatmap_data(
                country=selected_country,
                questions=selected_questions,
                score=selected_score,
                oecd_status=oecd_status,
                genders=selected_genders
            )
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            heatmap_data = pd.DataFrame()

        if not heatmap_data.empty:
            # Rename columns for readability
            heatmap_columns = {
                selected_questions[0]: selected_question1_label,
                selected_questions[1]: selected_question2_label,
                "Score": selected_score.replace("_", " ").title()
            }
            heatmap_data.rename(columns=heatmap_columns, inplace=True)

            # Prepare pivot table for the heatmap
            pivot_table = heatmap_data.pivot_table(
                values=heatmap_columns["Score"],
                index=heatmap_columns[selected_questions[1]],
                columns=heatmap_columns[selected_questions[0]],
                aggfunc="mean"
            )

            # Plot the heatmap using matplotlib
            import matplotlib.pyplot as plt
            import seaborn as sns

            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(
                pivot_table,
                annot=False,  # Disable annotation for cleaner heatmap
                fmt=".1f",
                cmap="viridis",
                cbar_kws={'label': 'Average Score'},
                ax=ax
            )
            ax.set_title(f"{selected_score.replace('_', ' ').title()} Heatmap")
            ax.set_xlabel(selected_question1_label)
            ax.set_ylabel(selected_question2_label)
            st.pyplot(fig)

            # Provide CSV download option
            csv_buffer = io.StringIO()
            pivot_table.to_csv(csv_buffer)
            st.download_button(
                label="Download Heatmap Data as CSV",
                data=csv_buffer.getvalue(),
                file_name=f"heatmap_data_{selected_country}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data available for the selected filters.")




    if fig is not None:
        # Reference Codebook Section
        st.subheader("📖 Reference Codebook")
        st.markdown(
            """
            You can find the detailed codebook for questions here: 
            [Student Question Codebook](https://www.oecd.org/content/dam/oecd/en/data/datasets/pisa/pisa-2022-datasets/questionnaires/COMPUTER-BASED%20STUDENT%20questionnaire%20PISA%202022.pdf)
            """,
            unsafe_allow_html=True,
        )

        # CSV Download and Save Plot Section
        st.subheader("📥 Download or Save Your Plot")
        analysis_text = st.text_area("Add Your Analysis (Optional)", placeholder="Describe your insights...")

        # Prepare CSV from the plot data
        csv_buffer = create_csv_from_plot_data(fig.to_dict(), selected_question_code)
        col1, col2 = st.columns([1, 1])

        with col1:
            if selected_plot_type == "Bar Plot"  and selected_countries:
                # Prepare CSV specifically for Bar Plot
                if not valid_dataframes:
                    st.warning("No data available to download for the Bar Plot.")
                else:
                    # Use the combined CSV data from Bar Plot
                    bar_csv_data = csv_data[["Country", selected_question_code, "Count"]]
                    bar_csv_data.rename(columns={
                        selected_question_code: f"{selected_question_text}",
                        "Count": "Response Count"
                    }, inplace=True)

                    # Convert to CSV format
                    bar_csv_buffer = io.StringIO()
                    bar_csv_data.to_csv(bar_csv_buffer, index=False)

                    st.download_button(
                        label="Download Bar Plot Data as CSV",
                        data=bar_csv_buffer.getvalue(),
                        file_name=f"bar_plot_{selected_question_code}.csv",
                        mime="text/csv"
                    )
                
            elif selected_plot_type == "Scatter Plot" and selected_country:
                # Prepare CSV specifically for Scatter Plot
                scatter_csv_data = scatter_data[["Student_ID", "Response", "Score"]]
                scatter_csv_data.rename(columns={
                    "Response": f"{selected_question_text} (Responses)",
                    "Score": f"{selected_score.replace('_', ' ').title()}",
                    "Student_ID": "Student ID"
                }, inplace=True)

                # Convert to CSV format
                csv_buffer = io.StringIO()
                scatter_csv_data.to_csv(csv_buffer, index=False)

                st.download_button(
                    label="Download Scatter Plot Data as CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"scatter_plot_{selected_question_code}_{selected_country}.csv",
                    mime="text/csv"
                )

            elif selected_plot_type == "Histogram" and selected_countries:
                # Prepare CSV specifically for Histogram
                if not histogram_data.empty:
                    histogram_csv_data = histogram_data[["Student_ID", "Country", "Response"]]
                    histogram_csv_data.rename(columns={
                        "Response": f"{selected_question_text} (Responses)",
                        "Student_ID": "Student ID",
                        "Country": "Country"
                    }, inplace=True)

                    # Convert to CSV format
                    csv_buffer = io.StringIO()
                    histogram_csv_data.to_csv(csv_buffer, index=False)

                    st.download_button(
                        label="Download Histogram Data as CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"histogram_{selected_question_code}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No data available to download for the Histogram.")

            elif selected_plot_type == "Pie Chart" and selected_country:
                # Check if data is available for the selected country
                if selected_country in data_counts:
                    counts_df = data_counts[selected_country]["counts_df"]
                    counts_df = counts_df[counts_df[selected_question_code] != 0]

                        # Prepare CSV for Pie Chart Data
                    pie_csv_data = counts_df[["Country", selected_question_code, "Count"]]
                    pie_csv_data.rename(columns={
                        selected_question_code: f"{selected_question_text}",
                        "Count": "Response Count"
                    }, inplace=True)

                    pie_csv_buffer = io.StringIO()
                    pie_csv_data.to_csv(pie_csv_buffer, index=False)

                    st.download_button(
                        label="Download Pie Chart Data as CSV",
                        data=pie_csv_buffer.getvalue(),
                        file_name=f"pie_chart_{selected_question_code}_{selected_country}.csv",
                        mime="text/csv"
                        )
                else:
                    st.warning("No data available for the selected filters.")
            elif selected_plot_type == "Heatmap" and selected_country:
                # Prepare CSV for Heatmap Data
                if not heatmap_data_grouped.empty:
                    heatmap_csv_buffer = io.StringIO()
                    heatmap_data_grouped.to_csv(heatmap_csv_buffer, index=False)

                    st.download_button(
                        label="Download Heatmap Data as CSV",
                        data=heatmap_csv_buffer.getvalue(),
                        file_name=f"heatmap_data_{selected_country}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No data available to download for the Heatmap.")

        with col2:
            if st.button("Save Plot and Analysis to History"):
                plot_json = fig.to_json()
                user_email = st.session_state.get("user_email")
                plot_name = f"{selected_plot_type} of {selected_question_text} ({', '.join(selected_genders)})"
                try:
                    save_plot_to_db_as_json(user_email, plot_name, plot_json, analysis_text if analysis_text.strip() else None)
                except Exception as e:
                    st.error(f"Failed to save: {e}")
