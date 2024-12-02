import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from query import  *

def home_page():
    st.subheader("🌐 Pisa2022 Data Analytics")

    
    col1, col2 = st.columns(2)
    with col1:
            st.metric("Total Students ", "613744")
        
    with col2:
            st.metric("Total Participating Countries","81")

    # Sidebar radio button to select OECD status
    oecd_status = st.sidebar.radio('Select OECD Status', ('All', 'OECD', 'NON-OECD'))
    
    # Dropdown to select score type (e.g., Mathematics, Science, Reading, Overall)
    score_type = st.selectbox('Select Score Type', ('Mathematics', 'Science', 'Reading', 'Overall'))

    # Fetch the scores based on the selected OECD status
    scores_df = fetch_scores(oecd_status)
    oecd_avg_data = fetch_oecd_average()

    if not scores_df.empty and oecd_avg_data:
        st.subheader(f'{score_type} Performance by Score')

        score_column = f'{score_type}Score'
        country_column = f'{score_type}Country'
        ranking_column = f'{score_type}Ranking'

        if country_column not in scores_df.columns:
            st.error(f"Column '{country_column}' not found in the DataFrame.")
            return

        # Sort the data by score (ascending order)
        sorted_df = scores_df.sort_values(by=score_column, ascending=True)

        # Retrieve the OECD average for the selected score type
        oecd_avg = {
            'Mathematics': oecd_avg_data[0],
            'Science': oecd_avg_data[1],
            'Reading': oecd_avg_data[2],
            'Overall': oecd_avg_data[3]
        }[score_type]



        plot_height = max(700, len(sorted_df) * 10)
        # Plot interactive scatter plot with Plotly
        fig = px.scatter(
            sorted_df,
            x=score_column,
            y=country_column,
            color='OverallOECD',  # Color points by OECD status
            color_discrete_map={'OECD': '#3498db', 'NON-OECD': '#e74c3c'},  # Color map for OECD and non-OECD
            hover_name=country_column,
            hover_data={score_column: True, ranking_column: True, 'OverallOECD': True},
            title=f'{score_type} Score by Country (OECD Status: {oecd_status})',
            labels={score_column: f'{score_type} Score', country_column: 'Country'},
            height=plot_height,
            width=800
        )

        # Add a vertical dashed line for the OECD average
        fig.add_shape(
            type='line',
            x0=oecd_avg, x1=oecd_avg, y0=0, y1=1,  # x0 and x1 are the x-values for the line; y0 and y1 are relative positions
            line=dict(color="green", width=2, dash="dash"),  # Dashed line with green color
            xref='x', yref='paper'  # xref and yref ensure the line spans across the entire y-axis
        )

        # Add annotation for the OECD average line
        fig.add_annotation(
            x=oecd_avg, y=1, xref='x', yref='paper',
            text=f"OECD Average: {oecd_avg:.2f}",
            showarrow=False,
            xanchor='left',
            font=dict(color="green")
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

        # Calculate the overall score and display the top performers
    scores_df['OverallScore'] = scores_df[['MathematicsScore', 'ScienceScore', 'ReadingScore']].mean(axis=1).round(2)

    # Function to plot top performers by subject using Plotly bar charts and add summary for 1st place
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
        
        # Summarize who got 1st rank
        top_country = df.iloc[-1][country_col]
        top_score = df.iloc[-1][score_col]
        st.write(f"The top performer for {title} is **{top_country}** with a score of **{top_score:.2f}**.")

    # Get the top performers for each subject
    top_math_df = scores_df.nlargest(10, 'MathematicsScore').drop_duplicates(subset=['MathematicsCountry']).sort_values(by='MathematicsScore')
    top_science_df = scores_df.nlargest(10, 'ScienceScore').drop_duplicates(subset=['ScienceCountry']).sort_values(by='ScienceScore')
    top_reading_df = scores_df.nlargest(10, 'ReadingScore').drop_duplicates(subset=['ReadingCountry']).sort_values(by='ReadingScore')
    top_overall_df = scores_df.nlargest(10, 'OverallScore').drop_duplicates(subset=['OverallCountry']).sort_values(by='OverallScore')

    # Dynamically display the top performers based on the selected score type
    if score_type == 'Mathematics':
        plot_top_performers(
            top_math_df, 'MathematicsScore', 'MathematicsCountry',
            'Top Performing Countries in Mathematics', 'skyblue'
        )
    elif score_type == 'Science':
        plot_top_performers(
            top_science_df, 'ScienceScore', 'ScienceCountry',
            'Top Performing Countries in Science', 'lightgreen'
        )
    elif score_type == 'Reading':
        plot_top_performers(
            top_reading_df, 'ReadingScore', 'ReadingCountry',
            'Top Performing Countries in Reading', 'salmon'
        )
    elif score_type == 'Overall':
        plot_top_performers(
            top_overall_df, 'OverallScore', 'OverallCountry',
            'Top Performing Countries Overall', 'purple'
        )
