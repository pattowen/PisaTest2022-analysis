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
    WHERE (Code LIKE 'ST%' OR Code LIKE 'IC%') 
      AND Code IN ({})
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
    JOIN full_student_score ON pisa2022_data.CNTSCHID = full_student_score.Student_ID
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

def fetch_thai_student_data():
    query = """
            SELECT *
            FROM pisa2022.thai_student_data    
            """
    return execute_query(query)

def fetch_thai_student_performance():
    query = """
    SELECT 
        m.MathematicsRanking AS MathRank, 
        m.MathematicsScore AS MathScore,
        s.ScienceRanking AS SciRank, 
        s.ScienceScore AS SciScore,
        r.ReadingRanking AS ReadRank, 
        r.ReadingScore AS ReadScore, 
        o.OverallRanking AS OvaRank, 
        o.OverallScore AS OvaScore
    FROM pisa2022.mathscore m
    JOIN pisa2022.readingscore r ON m.MathematicsCountry = r.ReadingCountry
    JOIN pisa2022.sciencescore s ON r.ReadingCountry = s.ScienceCountry
    JOIN pisa2022.overallscore o ON s.ScienceCountry = o.OverallCountry
    WHERE m.MathematicsCountry = 'Thailand'
      AND r.ReadingCountry = 'Thailand'
      AND s.ScienceCountry = 'Thailand'
      AND o.OverallCountry = 'Thailand'
    """
    return execute_query(query)




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