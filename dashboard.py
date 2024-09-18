import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sb
from main import *
from database import *
from PlotColor import *


def home_page():
    st.subheader("🌐 Pisa2022 Data Analytics")
    score_type = st.selectbox('Select Score Type', ('Mathematics', 'Science', 'Reading', 'Overall'))
    oecd_status = st.sidebar.radio('Select OECD Status', ('All', 'OECD', 'NON-OECD'))   
    scores_df = fetch_scores(oecd_status)
    
    if not scores_df.empty:
        st.subheader(f'{score_type} Performance by score')
        score_column = f'{score_type}Score'
        country_column = f'{score_type}Country'
        ranking_column = f'{score_type}Ranking'

        if country_column not in scores_df.columns:
            st.error(f"Column '{country_column}' not found in the DataFrame.")
            return
        
        sorted_df = scores_df.sort_values(by=score_column)
        sorted_df_desc = sorted_df.sort_values(by=ranking_column,ascending=False)

        # Define colors based on OECD status for home page plot
        colors_home_page = {'OECD': '#3498db', 'NON-OECD': '#e74c3c'}
        
        if oecd_status == 'All':
            # If 'All' is selected, color all data points based on OECD status
            color_column = [colors_home_page[status] for status in sorted_df['OverallOECD']]
        else:
            # If a specific OECD status is selected, color data points accordingly
            color_column = [colors_home_page[oecd_status] for _ in range(len(sorted_df))]
        
        plt.figure(figsize=(15, 15))
        plt.scatter(sorted_df[score_column], sorted_df[country_column], c=color_column, label=f'{score_type} Score')
        plt.xlabel(f'{score_type} Score')
        plt.ylabel('Country')
        
        # Add legend with custom labels for OECD and NON-OECD colors
        legend_labels = {'OECD': f'OECD', 'NON-OECD': f'NON_OECD '}
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors_home_page[key], markersize=10, label=label) for key, label in legend_labels.items()]
        plt.legend(handles=legend_elements)
        
        st.pyplot()


        # Create a dashboard to show scores for each country
        st.subheader(f"{score_type} Performance Dashboard")
        sorted_df_desc = sorted_df_desc.reset_index(drop=True)  # Reset index and drop the old index column
        st.write(sorted_df_desc[[ranking_column, country_column, score_column]])        


         # Calculate overall scores and display top performers
        scores_df['OverallScore'] = scores_df[['MathematicsScore', 'ScienceScore', 'ReadingScore']].mean(axis=1)
        
         # Filter top performers for each subject
        top_math_df = scores_df.nlargest(10, 'MathematicsScore').sort_values(by='MathematicsScore')
        top_science_df = scores_df.nlargest(10, 'ScienceScore').sort_values(by='ScienceScore')
        top_reading_df = scores_df.nlargest(10, 'ReadingScore').sort_values(by='ReadingScore')
        
        # Display top performers for each subject in separate horizontal bar charts
        st.subheader("Top Performing Countries/Regions")
        
        plt.figure(figsize=(10, 6))
        bars = plt.barh(top_math_df['MathematicsCountry'], top_math_df['MathematicsScore'], color='skyblue')
        plt.xlabel('Mathematics Score')
        plt.ylabel('Country/Region')
        plt.title('Top Performing Countries/Regions in Mathematics')

        # Add score annotations to the bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}', ha='left', va='center')

        st.pyplot()

        plt.figure(figsize=(10, 6))
        bars = plt.barh(top_science_df['ScienceCountry'], top_science_df['ScienceScore'], color='lightgreen')
        plt.xlabel('Science Score')
        plt.ylabel('Country/Region')
        plt.title('Top Performing Countries/Regions in Science')

        # Add score annotations to the bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}', ha='left', va='center')

        st.pyplot()

        plt.figure(figsize=(10, 6))
        bars = plt.barh(top_reading_df['ReadingCountry'], top_reading_df['ReadingScore'], color='salmon')
        plt.xlabel('Reading Score')
        plt.ylabel('Country/Region')
        plt.title('Top Performing Countries/Regions in Reading')

        # Add score annotations to the bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}', ha='left', va='center')

        st.pyplot()

        plt.figure(figsize=(10, 6))
        bars = plt.barh(top_reading_df['OverallCountry'], top_reading_df['OverallScore'], color='purple')
        plt.xlabel('Overall Score')
        plt.ylabel('Country/Region')
        plt.title('Top Performing Countries/Regions in Overall')

        # Add score annotations to the bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}', ha='left', va='center')


        st.pyplot()
       


# Progress Page Function with modified color generation
def analytics_page():
    global country_colors

    oecd_status = st.sidebar.radio('Select OECD Status', ('All', 'OECD', 'NON-OECD'))   
    countries = fetch_countries(oecd_status)
    question_codes = fetch_questions()

    selected_countries = st.multiselect('Select Countries', countries)
    selected_question_code = st.sidebar.selectbox('Select Question', list(question_codes.items()), format_func=lambda x: x[1])
    selected_plot_type = st.sidebar.selectbox('Select Plot Type', ['Bar Plot', 'Scatter Plot', 'Box Plot', 'Histogram'])

    # Generate random colors for new countries and store them persistently
    for country in selected_countries:
        if country not in country_colors:
            country_colors[country] = generate_random_color()

    ensure_visual_distinctness()  # Ensure visual distinctness of colors

    if selected_countries and selected_question_code:
        selected_question_code = selected_question_code[0]  # Get the selected question code from the tuple

        data_counts = fetch_data_and_count(oecd_status, selected_countries, selected_question_code)

        if selected_plot_type == 'Bar Plot':
            plt.figure(figsize=(10, 6))
            for i, (country, data) in enumerate(data_counts.items()):
                label = data['label']
                counts_df = data['counts_df']
                plt.bar(counts_df[selected_question_code], counts_df['Count'], label=f"{country}", color=country_colors[country], alpha=0.7)
            plt.xlabel(f"{selected_question_code} ({question_codes[selected_question_code]})")
            plt.ylabel('Count')
            plt.legend()
            plt.title(f'Count of {selected_question_code} for Selected Countries')
            st.pyplot()

        elif selected_plot_type == 'Scatter Plot':
            plt.figure(figsize=(10, 6))
            for i, (country, data) in enumerate(data_counts.items()):
                label = data['label']
                counts_df = data['counts_df']
                plt.scatter(counts_df[selected_question_code], counts_df['Count'], label=f"{country}", color=country_colors[country])
            plt.xlabel(f"{selected_question_code} ({question_codes[selected_question_code]})")
            plt.ylabel('Count')
            plt.legend()
            plt.title(f'Scatter Plot of {selected_question_code} for Selected Countries')
            st.pyplot()


        elif selected_plot_type == 'Histogram':
            plt.figure(figsize=(10, 6))
            for i, (country, data) in enumerate(data_counts.items()):
                label = data['label']
                counts_df = data['counts_df']
                plt.hist(counts_df['Count'], bins=10, alpha=0.5, label=f"{country}", color=country_colors[country])
            plt.xlabel('Count')
            plt.ylabel('Frequency')
            plt.legend()
            plt.title(f'Histogram of {selected_question_code} Count for Selected Countries')
            st.pyplot()