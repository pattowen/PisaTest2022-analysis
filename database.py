import streamlit as st
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
from main import *

st.set_option('deprecation.showPyplotGlobalUse', False)

def connect_to_database():
    conn = mysql.connector.connect(
        host='localhost',
        port='3306',
        user='root',
        password='Owen01042545',
        database='pisa2022',
        connect_timeout=12000
)
    return conn


def fetch_countries(oecd_status):
    query_dict = {
        'OECD': "SELECT DISTINCT CountryRegion FROM pisa2022_data WHERE OECD='OECD'",
        'NON-OECD': "SELECT DISTINCT CountryRegion FROM pisa2022_data WHERE OECD='NON-OECD'",
        'All': "SELECT DISTINCT CountryRegion FROM pisa2022_data"
    }
    query = query_dict.get(oecd_status, None)
    
    if not query:
        st.error("Invalid OECD status selected.")
        return []
    
    countries = execute_query(query)
    return [country[0] for country in countries]



# Function to fetch questions from codebook
def fetch_questions():
    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT Code, Label FROM codebook")
    questions = {code: label for code, label in cursor.fetchall()}

    conn.close()
    return questions

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
    
    conn.close()
    return scores_df


def fetch_data_and_count(oecd_status, countries, question_code):
    conn = connect_to_database()
    cursor = conn.cursor()

    questions = fetch_questions()  # Fetch once outside the loop
    data_counts = {}

    for country in countries:
        query = f"SELECT {question_code} FROM pisa2022_data WHERE CountryRegion='{country}'"
        if oecd_status != 'All':
            query += f" AND OECD='{oecd_status}'"

        cursor.execute(query)
        data = cursor.fetchall()

        counts = pd.DataFrame(data, columns=[question_code]).value_counts().reset_index(name='Count')
        question_label = questions.get(question_code, 'Unknown')

        data_counts[country] = {'label': question_label, 'counts_df': counts}

    conn.close()
    return data_counts


def execute_query(query, params=None):
    try:
        with connect_to_database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return []
