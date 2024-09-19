import streamlit as st
import plotly.graph_objects as go
from database import fetch_countries, fetch_questions, fetch_data_and_count
from PlotColor import generate_random_color, ensure_visual_distinctness

# Initialize global variable
country_colors = {}

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

        # Plot using Plotly
        if selected_plot_type == 'Bar Plot':
            fig = go.Figure()
            for country, data in data_counts.items():
                counts_df = data['counts_df']
                fig.add_trace(go.Bar(
                    x=counts_df[selected_question_code], 
                    y=counts_df['Count'], 
                    name=country,
                    marker_color=country_colors[country],
                    hovertemplate=f"<b>{country}</b><br>Score: %{selected_question_code}<br>Count: %{selected_question_code}"
                ))
            fig.update_layout(
                title=f'Count of {selected_question_code} for Selected Countries',
                xaxis_title=f"{selected_question_code} ({question_codes[selected_question_code]})",
                yaxis_title="Count",
                barmode='group'
            )
            st.plotly_chart(fig)

        elif selected_plot_type == 'Scatter Plot':
            fig = go.Figure()
            for country, data in data_counts.items():
                counts_df = data['counts_df']
                fig.add_trace(go.Scatter(
                    x=counts_df[selected_question_code], 
                    y=counts_df['Count'], 
                    mode='markers',
                    name=country,
                    marker=dict(color=country_colors[country]),
                    hovertemplate=f"<b>{country}</b><br>Score: %{selected_question_code}<br>Count: %{selected_question_code}"
                ))
            fig.update_layout(
                title=f'Scatter Plot of {selected_question_code} for Selected Countries',
                xaxis_title=f"{selected_question_code} ({question_codes[selected_question_code]})",
                yaxis_title="Count"
            )
            st.plotly_chart(fig)

        elif selected_plot_type == 'Histogram':
            fig = go.Figure()
            for country, data in data_counts.items():
                counts_df = data['counts_df']
                fig.add_trace(go.Histogram(
                    x=counts_df['Count'],
                    name=country,
                    marker_color=country_colors[country],
                    hovertemplate=f"<b>{country}</b><br>Score: %{selected_question_code}<br>Count: %{selected_question_code}"
                ))
            fig.update_layout(
                title=f'Histogram of {selected_question_code} Count for Selected Countries',
                xaxis_title="Count",
                yaxis_title="Frequency",
                barmode='overlay'
            )
            fig.update_traces(opacity=0.75)
            st.plotly_chart(fig)
