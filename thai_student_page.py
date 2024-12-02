import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from query import fetch_thai_student_data, fetch_thai_student_performance, fetch_questions

def thai_student_performance():
    st.title("📊 Thai Student Performance Dashboard")

    # Load Thai student performance data
    thai_data = fetch_questions()
    # Fetch data using the updated function
    performance_data = fetch_thai_student_performance()

    # Convert to a DataFrame
    performance_data = pd.DataFrame(performance_data, columns=["StudentID", "MathScore", "SciScore", "ReadScore", "OvaScore"])


    st.write("Thai Student Performance Data:")
    # Calculate metrics
    avg_math = performance_data['MathScore'].mean()
    avg_science = performance_data['SciScore'].mean()
    avg_reading = performance_data['ReadScore'].mean()
    overall_score = performance_data['OvaScore'].mean()

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📘 Avg Math Score", f"{avg_math:.2f}")
    col2.metric("🔬 Avg Science Score", f"{avg_science:.2f}")
    col3.metric("📖 Avg Reading Score", f"{avg_reading:.2f}")
    col4.metric("🌍 Overall Score", f"{overall_score:.2f}")


    # Score Distribution
    st.subheader("Score Distribution")
    subject = st.selectbox("Select Subject", ["MathScore", "SciScore", "ReadScore"], index=0)
    fig_distribution = px.histogram(
        performance_data,
        x=subject,
        nbins=30,
        title=f"Distribution of {subject.replace('Score', '')} Scores",
        color_discrete_sequence=['#636EFA'],
        marginal="box",
        labels={subject: "Score"}
    )
    st.plotly_chart(fig_distribution, use_container_width=True)

    # Survey Question Analysis
    st.subheader("Survey Responses")
    questions = fetch_questions()
    question_code = st.selectbox("Select Survey Question", options=list(questions.keys()), format_func=lambda x: questions[x])
    response_counts = thai_data[question_code].value_counts().reset_index()
    response_counts.columns = ['Response', 'Count']

    fig_survey = px.pie(
        response_counts,
        names='Response',
        values='Count',
        title=f"Survey Question: {questions[question_code]}"
    )
    st.plotly_chart(fig_survey, use_container_width=True)

    # Regional Analysis (if regional data exists)
    if 'Region' in thai_data.columns:
        st.subheader("Performance by Region")
        regional_data = thai_data.groupby('Region')[['MathScore', 'SciScore', 'ReadScore']].mean().reset_index()
        fig_region = px.bar(
            regional_data,
            x='Region',
            y=['MathScore', 'SciScore', 'ReadScore'],
            title="Average Scores by Region",
            barmode="group"
        )
        st.plotly_chart(fig_region, use_container_width=True)

    # Correlation Heatmap
    st.subheader("Correlation Heatmap")
    numeric_cols = performance_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
    correlation_matrix = performance_data[numeric_cols].corr()
    fig_corr = px.imshow(
        correlation_matrix,
        text_auto=True,
        title="Correlation Heatmap of Performance Metrics"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    # Download Filtered Data
    st.subheader("Download Data")
    csv_data = performance_data.to_csv(index=False)
    st.download_button(
        label="Download Thai Student Data (CSV)",
        data=csv_data,
        file_name="thai_student_performance.csv",
        mime="text/csv"
    )

# Integrate with your main app
if __name__ == "__main__":
    thai_student_performance()
