import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from query import fetch_thai_student_data, fetch_thai_student_performance, fetch_asean_countries_performance, fetch_oecd_average

def thai_student_performance():
    st.title("Thai Student Performance Dashboard")

    # Fetching the Thai student data
    thai_data = fetch_thai_student_data()
    thai_perfomance = fetch_thai_student_performance()
    asean_data = fetch_asean_countries_performance()  # Fetching ASEAN countries' data
    oecd_avg = fetch_oecd_average()  # Fetching OECD average

    if not thai_perfomance or len(thai_perfomance) == 0:
        st.error("No data available for Thailand.")
        return

    if not oecd_avg:
        st.error("No data available for OECD average.")
        return

    # Create a DataFrame for Thai student data
    columns = ['MathematicsRanking', 'MathematicsScore',
               'ScienceRanking', 'ScienceScore',
               'ReadingRanking', 'ReadingScore',
               'OverallRanking', 'OverallScore']
    
    thai_df = pd.DataFrame(thai_perfomance, columns=columns)

    # Display Thai student performance (Swap Rank and Score in metrics)
    st.markdown("### Thai Students' Rankings and Scores")

    # Extracting rankings and scores
    math_ranking = thai_df['MathematicsRanking'].values[0]
    math_score = thai_df['MathematicsScore'].values[0]
    science_ranking = thai_df['ScienceRanking'].values[0]
    science_score = thai_df['ScienceScore'].values[0]
    reading_ranking = thai_df['ReadingRanking'].values[0]
    reading_score = thai_df['ReadingScore'].values[0]
    overall_ranking = thai_df['OverallRanking'].values[0]
    overall_score = thai_df['OverallScore'].values[0]

    # Create 4 columns for the metrics (Swapped: Rank and Score)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Mathematics", f"Score: {math_score}", f"Rank: {math_ranking}")

    with col2:
        st.metric("Science", f"Score: {science_score}", f"Rank: {science_ranking}")

    with col3:
        st.metric("Reading", f"Score: {reading_score}", f"Rank: {reading_ranking}")

    with col4:
        st.metric("Overall", f"Score: {overall_score}", f"Rank: {overall_ranking}")

    col1 = st.columns(1)
    
    # Prepare comparison data with ASEAN countries and OECD average
    asean_df = pd.DataFrame(asean_data, columns=['Country', 'MathematicsScore', 'ScienceScore', 'ReadingScore', 'OverallScore'])

    # Add the OECD average as a "country" for comparison
    oecd_scores = {
        'MathematicsScore': oecd_avg[0],  # AvgMath
        'ScienceScore': oecd_avg[1],      # AvgScience
        'ReadingScore': oecd_avg[2],      # AvgReading
        'OverallScore': oecd_avg[3]       # AvgOverall
    }

    # Combine ASEAN countries and OECD average for comparison
    comparison_df = pd.DataFrame({
        'Country': asean_df['Country'].tolist() + ['OECD Average'],
        'MathematicsScore': asean_df['MathematicsScore'].tolist() + [oecd_scores['MathematicsScore']],
        'ScienceScore': asean_df['ScienceScore'].tolist() + [oecd_scores['ScienceScore']],
        'ReadingScore': asean_df['ReadingScore'].tolist() + [oecd_scores['ReadingScore']],
        'OverallScore': asean_df['OverallScore'].tolist() + [oecd_scores['OverallScore']],
    })

    # Sidebar filter for subject (Mathematics, Science, Reading, Overall)
    subject_filter = st.sidebar.selectbox('Select Subject', ['Mathematics', 'Science', 'Reading', 'Overall'])

    # Customize Plotly Visualization with better tooltips, layout, and consistent colors
    score_mapping = {
        'Mathematics': 'MathematicsScore',
        'Science': 'ScienceScore',
        'Reading': 'ReadingScore',
        'Overall': 'OverallScore'
    }
    selected_category = score_mapping[subject_filter]

    # Create a bar chart for the selected subject comparison (Thai vs ASEAN countries and OECD)
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=comparison_df['Country'],
        y=comparison_df[selected_category],
        marker=dict(color=['#3498db' if country == 'Thailand' else '#2ecc71' if country == 'OECD Average' else '#95a5a6' for country in comparison_df['Country']]),
        hovertemplate='<b>%{x}</b><br>Score: %{y}<extra></extra>',
    ))

    fig.update_layout(
        title=f"{subject_filter} Score Comparison (Thailand vs ASEAN and OECD Average)",
        xaxis_title="Country/Region",
        yaxis_title=f"{subject_filter} Score",
        height=500,
        template="plotly_white",
        showlegend=False
    )

    st.plotly_chart(fig)

    # Displaying final insights based on the comparison
    st.markdown(f"""
    ### Insights for {subject_filter}:
    - **Thai Students' Score**: {thai_df[selected_category].values[0]}
    - **OECD Average Score**: {oecd_scores[selected_category]}
    - **Highest ASEAN Score**: {comparison_df[selected_category].max()}
    """)

    # Additional Insights comparing Thailand with ASEAN and OECD
    if thai_df[selected_category].values[0] < oecd_scores[selected_category]:
        st.markdown(f"**Observation**: Thai students are performing below the OECD average in {subject_filter}. There is a gap of **{oecd_scores[selected_category] - thai_df[selected_category].values[0]:.2f} points**.")
    else:
        st.markdown(f"**Observation**: Thai students are performing above the OECD average in {subject_filter} by **{thai_df[selected_category].values[0] - oecd_scores[selected_category]:.2f} points**.")

    # Insights for ASEAN countries
    asean_max_score = comparison_df[comparison_df['Country'] != 'OECD Average'][selected_category].max()
    asean_max_country = comparison_df.loc[comparison_df[selected_category] == asean_max_score, 'Country'].values[0]

    if thai_df[selected_category].values[0] < asean_max_score:
        st.markdown(f"**Observation**: The top performer in {subject_filter} among ASEAN countries is **{asean_max_country}** with a score of **{asean_max_score:.2f}**. Thai students are behind by **{asean_max_score - thai_df[selected_category].values[0]:.2f} points**.")
    else:
        st.markdown(f"**Observation**: Thai students are the top performers in {subject_filter} among ASEAN countries with a score of **{thai_df[selected_category].values[0]:.2f}**.")

