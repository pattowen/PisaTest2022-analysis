import streamlit as st
import pandas as pd
import mysql
import logging
import mysql.connector
from mysql.connector import Error  
from db_connect import connect_to_database 


logging.basicConfig(level=logging.ERROR, filename='db_errors.log')

def execute_query(query, params=None):
    try:
        with connect_to_database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    except mysql.connector.Error as err:
        logging.error(f"Database query error: {err}")
        st.error("An error occurred while querying the database. Please try again later.")
        return None



def fetch_countries(oecd_status):
    query = "SELECT DISTINCT CNT FROM pisa2022_data"
    if oecd_status in ['OECD', 'NON-OECD']:
        query += f" WHERE OECD=%s"
        countries = execute_query(query, (oecd_status,))
    else:
        countries = execute_query(query)
    return [country[0] for country in countries] if countries else []


# Function to fetch questions from codebook

def fetch_questions():
    conn = connect_to_database()
    cursor = conn.cursor()

    # Fetch column names from the pisa2022_data table
    cursor.execute("SHOW COLUMNS FROM pisa2022_data")
    pisa_columns = {row[0] for row in cursor.fetchall()}  # Use a set for efficient lookups

    # Fetch matching questions from the codebook
    query = """
    SELECT Code, Label 
    FROM codebook 
    WHERE Code IN ({})
    """
    if pisa_columns:
        in_clause = ', '.join(['%s'] * len(pisa_columns))
        query = query.format(in_clause)
        cursor.execute(query, tuple(pisa_columns))
        matching_questions = {code: label for code, label in cursor.fetchall()}
    else:
        matching_questions = {}

    conn.close()
    return matching_questions

def fetch_scores(oecd_status):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Base query
    query = """
    SELECT MathematicsRanking, MathematicsCountry, MathematicsOECD, MathematicsScore, 
           ScienceRanking, ScienceCountry, ScienceOECD, ScienceScore, 
           ReadingRanking, ReadingCountry, ReadingOECD, ReadingScore, 
           OverallRanking, OverallCountry, OverallOECD, OverallScore 
    FROM fullscore
    """
    
    # Append the WHERE clause based on the OECD status
    if oecd_status in ['OECD', 'NON-OECD']:
        query += f" WHERE OverallOECD='{oecd_status}'"

    cursor.execute(query)
    scores_data = cursor.fetchall()
    
    columns = ['MathematicsRanking', 'MathematicsCountry', 'MathematicsOECD', 'MathematicsScore',
               'ScienceRanking', 'ScienceCountry', 'ScienceOECD', 'ScienceScore',
               'ReadingRanking', 'ReadingCountry', 'ReadingOECD', 'ReadingScore',
               'OverallRanking', 'OverallCountry', 'OverallOECD', 'OverallScore']
    
    scores_df = pd.DataFrame(scores_data, columns=columns)
    
    # Drop duplicates based on the country column
    scores_df = scores_df.drop_duplicates(subset=['MathematicsCountry', 'ScienceCountry', 'ReadingCountry', 'OverallCountry'])

    conn.close()
    return scores_df


def fetch_data_and_count(oecd_status, selected_genders, countries, question_code):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Map genders to corresponding ST004D01T values
    gender_mapping = {
        "Male": ["1"],  # Male corresponds to 1
        "Female": ["2"],  # Female corresponds to 2
        "All": []  # No filter for "All"
    }

    # Combine gender values
    selected_values = []
    for gender in selected_genders:
        selected_values.extend(gender_mapping.get(gender, []))

    # Build query dynamically
    query = f"""
    SELECT pisa2022_data.CNT, pisa2022_data.{question_code}, COUNT(*) AS Count
    FROM pisa2022_data
    JOIN full_student_score ON pisa2022_data.CNTSCHID = full_student_score.student_id
    WHERE pisa2022_data.CNT IN ({','.join(['%s'] * len(countries))})
    """
    params = countries

    # Add gender filter dynamically
    if selected_values:
        query += " AND pisa2022_data.ST004D01T IN ({})".format(', '.join(['%s'] * len(selected_values)))
        params.extend(selected_values)

    # Add OECD status filter
    if oecd_status != "All":
        query += " AND pisa2022_data.OECD=%s"
        params.append(oecd_status)

    # Group by country and question code
    query += f" GROUP BY pisa2022_data.CNT, pisa2022_data.{question_code}"

    # Execute the query once
    cursor.execute(query, params)
    data = cursor.fetchall()

    # Convert to DataFrame
    result_df = pd.DataFrame(data, columns=["Country", question_code, "Count"])
    data_counts = {country: {"counts_df": result_df[result_df["Country"] == country]} for country in countries}

    cursor.close()
    conn.close()
    return data_counts


def fetch_question_response_and_scores(question_code, countries, selected_score, oecd_status, genders):
    conn = connect_to_database()
    cursor = conn.cursor()

    gender_mapping = {"Male": ["1"], "Female": ["2"], "All": []}
    selected_values = [value for gender in genders for value in gender_mapping.get(gender, [])]

    # Build the SELECT clause dynamically
    select_clause = f"""
    SELECT 
        pisa2022_data.CNT AS Country,
        pisa2022_data.{question_code} AS Response,
        full_student_score.student_id AS Student_ID,
        COUNT(*) AS Count
    """
    # Include Score column only if selected_score is not None
    if selected_score:
        select_clause += f", full_student_score.{selected_score} AS Score"

    query = f"""
    {select_clause}
    FROM pisa2022_data
    JOIN full_student_score ON pisa2022_data.CNTSTUID = full_student_score.student_id
    WHERE pisa2022_data.CNT IN ({','.join(['%s'] * len(countries))})
    """
    params = countries

    # Add gender filter dynamically
    if selected_values:
        query += " AND pisa2022_data.ST004D01T IN ({})".format(', '.join(['%s'] * len(selected_values)))
        params.extend(selected_values)

    # Add OECD status filter if applicable
    if oecd_status != "All":
        query += " AND pisa2022_data.OECD = %s"
        params.append(oecd_status)

    # Add GROUP BY clause
    query += f" GROUP BY pisa2022_data.CNT, pisa2022_data.{question_code}, full_student_score.student_id"
    if selected_score:
        query += f", full_student_score.{selected_score}"

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()

    # Define DataFrame columns based on whether selected_score is included
    columns = ["Country", "Response", "student_id", "Count"]
    if selected_score:
        columns.append("Score")

    return pd.DataFrame(data, columns=columns)

def fetch_histogram_questions():
    conn = connect_to_database()
    cursor = conn.cursor()

    # Fetch column names from the pisa2022_data table
    cursor.execute("SHOW COLUMNS FROM pisa2022_data")
    histogram_columns = [row[0] for row in cursor.fetchall() if row[0].startswith("PV")]

    # Fetch matching questions from the codebook
    if histogram_columns:
        query = f"""
        SELECT Code, Label 
        FROM codebook 
        WHERE Code IN ({','.join(['%s'] * len(histogram_columns))})
        """
        cursor.execute(query, tuple(histogram_columns))
        matching_questions = {code: label for code, label in cursor.fetchall()}
    else:
        matching_questions = {}

    conn.close()
    return matching_questions
def fetch_heatmap_data(country, questions, score, oecd_status=None, genders=None):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Map gender options to their database values
    gender_mapping = {"Male": ["1"], "Female": ["2"], "All": []}
    selected_values = [value for gender in genders for value in gender_mapping.get(gender, [])]

    # Dynamically construct the SELECT clause for questions
    select_questions = ", ".join([f"pisa2022_data.{q}" for q in questions])
    
    # Construct the SQL query
    query = f"""
    SELECT 
        pisa2022_data.CNT AS Country,
        {select_questions},  -- Dynamically include selected questions
        full_student_score.{score} AS Score
    FROM pisa2022_data
    JOIN full_student_score ON pisa2022_data.CNTSTUID = full_student_score.student_id
    WHERE pisa2022_data.CNT = %s
    """
    params = [country]

    if selected_values:
        query += " AND pisa2022_data.ST004D01T IN ({})".format(', '.join(['%s'] * len(selected_values)))
        params.extend(selected_values)

    if oecd_status and oecd_status != "All":
        query += " AND pisa2022_data.OECD = %s"
        params.append(oecd_status)

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()

    # Define column names dynamically
    columns = ["Country"] + questions + ["Score"]

    # Return the data as a pandas DataFrame
    return pd.DataFrame(data, columns=columns)

def fetch_thai_student_data():
    query = """
            SELECT *
            FROM pisa2022.thai_student_data    
            """
    return execute_query(query)

def fetch_thai_student_performance():
    query = """
    SELECT 
        student_id AS StudentID,
        math_score AS MathScore,
        science_score AS SciScore,
        reading_score AS ReadScore,
        overall_score AS OvaScore
    FROM pisa2022.full_student_score
    WHERE country = 'Thailand'
    """
    return execute_query(query)

def fetch_thai_student_data(selected_score=None, genders=["All"]):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Prepare the base query
    query = """
        SELECT `STUDENT ID`, `MATH SCORE`, `SCIENCE SCORE`, `READING SCORE`, `OVERALL SCORE`,
               `Father level of education (ISCED)`, `Mother level of education (ISCED)`, `Gender`
        FROM thai_student_data
    """

    # Initialize parameters list
    params = []

    # Add gender filter if needed
    if genders != ["All"]:
        query += " WHERE `Gender` IN ({})".format(", ".join(["%s"] * len(genders)))
        params.extend(genders)

    # Execute the query
    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    conn.close()

    # Create a DataFrame from the fetched data
    columns = [
        'Student ID', 'MATH SCORE', 'SCIENCE SCORE', 'READING SCORE', 'OVERALL SCORE',
        "Father level of education (ISCED)", "Mother level of education (ISCED)", "Gender"
    ]
    df = pd.DataFrame(data, columns=columns)

    # Map gender values from numeric to descriptive
    gender_mapping = {'1': 'Male', '2': 'Female'}
    df['Gender'] = df['Gender'].map(gender_mapping)

    return df





def fetch_oecd_average():
    query = """
    SELECT m.MathematicsScore AS AvgMath,
           s.ScienceScore AS AvgScience,
           r.ReadingScore AS AvgReading, 
           o.OverallScore AS AvgOverall
    FROM pisa2022.mathscore m
    JOIN pisa2022.readingscore r ON m.MathematicsCountry = r.ReadingCountry
    JOIN pisa2022.sciencescore s ON r.ReadingCountry = s.ScienceCountry
    JOIN pisa2022.overallscore o ON s.ScienceCountry = o.OverallCountry
    WHERE m.MathematicsCountry = 'OECD average'
      AND r.ReadingCountry = 'OECD average'
      AND s.ScienceCountry = 'OECD average'
      AND o.OverallCountry = 'OECD average'
    """
    result = execute_query(query)
    return result[0] if result else None



def fetch_asean_countries_performance():
    query = """
        SELECT 
        OverallCountry,
        MAX(MathematicsScore) AS MathematicsScore,
        MAX(ScienceScore) AS ScienceScore,
        MAX(ReadingScore) AS ReadingScore,
        MAX(OverallScore) AS OverallScore
    FROM pisa2022.fullscore
    WHERE OverallCountry IN ('Brunei Darussalam', 'Cambodia', 'Indonesia', 'Laos', 'Malaysia', 
                            'Myanmar', 'Philippines', 'Singapore', 'Thailand', 'Viet nam')
    GROUP BY OverallCountry

    """
    return execute_query(query)

def execute_query(query, params=None):
    try:
        with connect_to_database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return []