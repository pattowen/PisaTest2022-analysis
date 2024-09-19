import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database import fetch_scores

def home_page():
    st.subheader("🌐 Pisa2022 Data Analytics")
    st.markdown("""
        ### What is PISA?
        The **Programme for International Student Assessment (PISA)** is a worldwide study conducted by the Organisation for Economic Co-operation and Development (OECD) to evaluate the educational systems of various countries by measuring 15-year-old students' scholastic performance on mathematics, science, and reading.
        
        PISA 2022 is the latest cycle in this ongoing assessment, focusing on students' ability to apply knowledge and skills to real-life challenges. It includes participation from both **OECD** and **non-OECD countries**. The results are used to benchmark educational standards globally and to identify trends in students' abilities.
        
        PISA assesses students in three key areas:
        - **Mathematics**
        - **Science**
        - **Reading**

        Additionally, PISA provides an overall performance indicator that averages these areas.
        """)
    # Sidebar radio button to select OECD status (this controls the data shown)
    oecd_status = st.sidebar.radio('Select OECD Status', ('All', 'OECD', 'NON-OECD'))
    # Add Thai Students Information Section
    st.markdown("""
        ### Thai Students' Performance in PISA 2022
        In PISA 2022, **Thai students** participated along with many other countries. Historically, Thai students have shown improving performance across the years, but there are still areas for growth, particularly in **reading** and **mathematics**.
        
        The performance of Thai students reflects both strengths and areas of improvement:
        - **Strengths**: Thai students showed progress in science and demonstrated a good understanding of practical applications.
        - **Challenges**: There is room for improvement in reading comprehension and mathematical problem-solving skills.
        
        The following analysis compares Thailand's performance with other countries and highlights their standing in different subjects.
        """)
    # Dropdown to select score type (e.g., Mathematics, Science, Reading, Overall)
    score_type = st.selectbox('Select Score Type', ('Mathematics', 'Science', 'Reading', 'Overall'))

    # Fetch the scores based on the selected OECD status
    scores_df = fetch_scores(oecd_status)

    if not scores_df.empty:
        st.subheader(f'{score_type} Performance by Score')

        score_column = f'{score_type}Score'
        country_column = f'{score_type}Country'
        ranking_column = f'{score_type}Ranking'

        if country_column not in scores_df.columns:
            st.error(f"Column '{country_column}' not found in the DataFrame.")
            return

        # Sort the data by score (descending)
        sorted_df = scores_df.sort_values(by=score_column, ascending=True)

        # Plot interactive scatter plot with Plotly
        fig = px.scatter(
            sorted_df,
            x=score_column,
            y=country_column,
            color='OverallOECD',  # Color points by OECD status
            color_discrete_map={'OECD': '#3498db', 'NON-OECD': '#e74c3c'},  # Use different colors for OECD vs NON-OECD
            hover_name=country_column,
            hover_data={score_column: True, ranking_column: True, 'OverallOECD': True},
            title=f'{score_type} Score by Country (OECD Status: {oecd_status})',
            labels={score_column: f'{score_type} Score', country_column: 'Country'},
            height=800
        )

        fig.update_layout(
            xaxis_title=f'{score_type} Score',
            yaxis_title='Country',
            legend_title='OECD Status',
            legend=dict(x=0.85, y=0.05),
            yaxis_categoryorder='total ascending'
        )

        # Display the scatter plot
        st.plotly_chart(fig)

        # Display the sorted data in a table
        st.subheader(f"{score_type} Performance Dashboard")
        st.write(sorted_df[[ranking_column, country_column, score_column]])

        # Calculate the overall score and display the top performers
        scores_df['OverallScore'] = scores_df[['MathematicsScore', 'ScienceScore', 'ReadingScore']].mean(axis=1)

        # Plot top performers by subject using Plotly bar charts
        def plot_top_performers(df, score_col, country_col, title, color):
            fig = go.Figure(go.Bar(
                x=df[score_col],
                y=df[country_col],
                orientation='h',
                text=df[score_col],
                textposition='auto',
                marker=dict(color=color),
            ))

            fig.update_layout(
                title=title,
                xaxis_title=score_col,
                yaxis_title='Country/Region',
                height=400
            )

            st.plotly_chart(fig)

        # Get the top performers for each subject and plot them
        top_math_df = scores_df.nlargest(10, 'MathematicsScore').sort_values(by='MathematicsScore')
        top_science_df = scores_df.nlargest(10, 'ScienceScore').sort_values(by='ScienceScore')
        top_reading_df = scores_df.nlargest(10, 'ReadingScore').sort_values(by='ReadingScore')
        top_overall_df = scores_df.nlargest(10, 'OverallScore').sort_values(by='OverallScore')

        # Plot for Mathematics
        plot_top_performers(top_math_df, 'MathematicsScore', 'MathematicsCountry', 'Top Performing Countries in Mathematics', 'skyblue')

        # Plot for Science
        plot_top_performers(top_science_df, 'ScienceScore', 'ScienceCountry', 'Top Performing Countries in Science', 'lightgreen')

        # Plot for Reading
        plot_top_performers(top_reading_df, 'ReadingScore', 'ReadingCountry', 'Top Performing Countries in Reading', 'salmon')

        # Plot for Overall performance
        plot_top_performers(top_overall_df, 'OverallScore', 'OverallCountry', 'Top Performing Countries Overall', 'purple')
    else:
        st.error("No data available for the selected OECD status.")
