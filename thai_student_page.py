import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from query import execute_query

def thai_student_performance():
    st.title("📊 Thai Student Performance Dashboard")

    # Gender filter
    gender_options = ["All", "Male", "Female"]
    selected_gender = st.sidebar.radio("Select Gender", gender_options)

    # Fetch data from the database
    query = """
        SELECT `Student ID`, `Gender`, `MATH SCORE`, `SCIENCE SCORE`, `READING SCORE`, `OVERALL SCORE`,
               `Father level of education (ISCED)`, `Mother level of education (ISCED)`,
               `student-teacher ratio`, `ratio of computers available`
        FROM thai_student_data
    """
    if selected_gender != "All":
        query += " WHERE `Gender` = %s"
        data = execute_query(query, (selected_gender,))
    else:
        data = execute_query(query)

    # Convert the data to a DataFrame
    columns = [
        "Student ID", "Gender", "MATH SCORE", "SCIENCE SCORE", "READING SCORE", "OVERALL SCORE",
        "Father level of education (ISCED)", "Mother level of education (ISCED)",
        "student-teacher ratio", "ratio of computers available"
    ]
    thai_student_data = pd.DataFrame(data, columns=columns)

    # Check for necessary columns
    required_columns = [
        "Student ID", "MATH SCORE", "SCIENCE SCORE", "READING SCORE", "OVERALL SCORE",
        "Father level of education (ISCED)", "Mother level of education (ISCED)",
        "student-teacher ratio", "ratio of computers available"
    ]
    if not all(col in thai_student_data.columns for col in required_columns):
        st.warning("Missing required columns in the dataset.")
        return

    # Metrics Section
    st.subheader("Performance Metrics")
    avg_math = thai_student_data["MATH SCORE"].mean()
    avg_science = thai_student_data["SCIENCE SCORE"].mean()
    avg_reading = thai_student_data["READING SCORE"].mean()
    avg_overall = thai_student_data["OVERALL SCORE"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📘 Avg Math Score", f"{avg_math:.2f}")
    col2.metric("🔬 Avg Science Score", f"{avg_science:.2f}")
    col3.metric("📖 Avg Reading Score", f"{avg_reading:.2f}")
    col4.metric("🌍 Avg Overall Score", f"{avg_overall:.2f}")
    
    

    # Prepare the data for visualization
    teacher_resource_analysis = thai_student_data[
        ["student-teacher ratio", "ratio of computers available", "OVERALL SCORE"]
    ].copy()

    # Group by rounded values for analysis
    teacher_resource_analysis["Student-Teacher Ratio (Rounded)"] = teacher_resource_analysis[
        "student-teacher ratio"
    ].round()
    teacher_resource_analysis["Computers Available Ratio (Rounded)"] = teacher_resource_analysis[
        "ratio of computers available"
    ].round(2)

    # Aggregate data
    aggregated_analysis = teacher_resource_analysis.groupby(
        ["Student-Teacher Ratio (Rounded)", "Computers Available Ratio (Rounded)"]
    )["OVERALL SCORE"].mean().reset_index()

    
    # Score filter
    st.subheader("Score Distribution")
    score_column = st.selectbox("Select Score for Analysis", ["MATH SCORE", "SCIENCE SCORE", "READING SCORE", "OVERALL SCORE"])

    # Score Distribution Visualization
    fig_distribution = px.histogram(
        thai_student_data,
        x=score_column,
        nbins=30,
        title=f"Distribution of {score_column.replace('SCORE', '').title()} Scores",
        color_discrete_sequence=['#636EFA'],
        marginal="box",  # Add a box plot on the margins
        labels={score_column: "Score"}
    )
    st.plotly_chart(fig_distribution, use_container_width=True)

    
    # Correlation Heatmap (Second Plot)
    st.subheader("Correlation Between Subject Scores")
    
    # Compute correlations between subject scores
    subject_score_correlations = thai_student_data[
        ['MATH SCORE', 'READING SCORE', 'SCIENCE SCORE', 'OVERALL SCORE']
    ].corr()

    # Plot the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(subject_score_correlations, annot=True, fmt=".2f", cmap="coolwarm", cbar=True)
    plt.title("Correlation Between Subject Scores")
    
    # Display the heatmap in Streamlit
    st.pyplot(plt)

    # Heatmap Section for Parental Education
    st.subheader(f"Impact of Parental Education on {score_column.replace('SCORE', '').title()}")

    # Group by parental education levels and calculate average scores
    parental_education_impact = thai_student_data.groupby(
        ["Father level of education (ISCED)", "Mother level of education (ISCED)"]
    )[[score_column]].mean().reset_index()

    # Pivot data for heatmap
    pivot_data = parental_education_impact.pivot(
        index="Father level of education (ISCED)",
        columns="Mother level of education (ISCED)",
        values=score_column
    )
    fig_heatmap = px.imshow(
        pivot_data,
        color_continuous_scale='Viridis',
        title=f"{score_column.replace('SCORE', '').title()} Score by Parental Education",
        labels={'color': 'Average Score'},
        aspect='auto'
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
# Teacher and Resource Ratios Analysis
    st.subheader("Teacher and Resource Ratios Analysis")
# Visualization 1: Impact of Student-Teacher Ratio
    fig_teacher_ratio = px.scatter(
        aggregated_analysis,
        x="Student-Teacher Ratio (Rounded)",
        y="OVERALL SCORE",
        size="OVERALL SCORE",
        color="OVERALL SCORE",
        title="Impact of Student-Teacher Ratio on Overall Performance",
        labels={"OVERALL SCORE": "Average Overall Score"},
        template="plotly_white",
    )
    st.plotly_chart(fig_teacher_ratio, use_container_width=True)

    # Visualization 2: Impact of Computers Available Ratio
    fig_computers_ratio = px.scatter(
        aggregated_analysis,
        x="Computers Available Ratio (Rounded)",
        y="OVERALL SCORE",
        size="OVERALL SCORE",
        color="OVERALL SCORE",
        title="Impact of Computers Available Ratio on Overall Performance",
        labels={"OVERALL SCORE": "Average Overall Score"},
        template="plotly_white",
    )
    st.plotly_chart(fig_computers_ratio, use_container_width=True)



# Run the dashboard
if __name__ == "__main__":
    thai_student_performance()