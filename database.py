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
    conn = connect_to_database()
    cursor = conn.cursor()

    if oecd_status == 'OECD':
        cursor.execute("SELECT DISTINCT CountryRegion FROM pisa2022_data WHERE OECD='OECD'")
    elif oecd_status == 'NON-OECD':
        cursor.execute("SELECT DISTINCT CountryRegion FROM pisa2022_data WHERE OECD='NON-OECD'")
    elif oecd_status == 'All':
        cursor.execute("SELECT DISTINCT CountryRegion FROM pisa2022_data")  # Fetch all countries regardless of OECD status
    else:
        st.error("Invalid OECD status selected.")
        return []

    countries = [country[0] for country in cursor.fetchall()]

    conn.close()
    return countries


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

    if oecd_status == 'All':
        cursor.execute("SELECT * FROM fullscore")
    elif oecd_status == 'OECD':
        cursor.execute("SELECT  MathematicsRanking, MathematicsCountry, MathematicsOECD, MathematicsScore, ScienceRanking, ScienceCountry, ScienceOECD, ScienceScore,ReadingRanking, ReadingCountry, ReadingOECD, ReadingScore, OverallRanking, OverallCountry, OverallOECD, OverallScore FROM fullscore WHERE MathematicsCountry IN (SELECT CountryRegion FROM pisa2022_data WHERE OECD='OECD')")
    elif oecd_status == 'NON-OECD':
        cursor.execute("SELECT  MathematicsRanking, MathematicsCountry, MathematicsOECD, MathematicsScore, ScienceRanking, ScienceCountry, ScienceOECD, ScienceScore,ReadingRanking, ReadingCountry, ReadingOECD, ReadingScore, OverallRanking, OverallCountry, OverallOECD, OverallScore FROM fullscore WHERE MathematicsCountry IN (SELECT CountryRegion FROM pisa2022_data WHERE OECD='NON-OECD')")
    else:
        raise ValueError("Invalid OECD status selected.")

    scores_data = cursor.fetchall()
    columns = ['MathematicsRanking','MathematicsCountry','MathematicsOECD', 'MathematicsScore' , 'ScienceRanking','ScienceCountry', 'ScienceOECD', 'ScienceScore', 'ReadingRanking','ReadingCountry','ReadingOECD', 'ReadingScore' ,'OverallRanking', 'OverallCountry','OverallOECD', 'OverallScore']
    scores_df = pd.DataFrame(scores_data, columns=columns)

    # Print the column names fetched from the database
    print("Columns in scores_df:", scores_df.columns.tolist())

    conn.close()
    return scores_df

def fetch_data_and_count(oecd_status, countries, question_code):
    conn = connect_to_database()
    cursor = conn.cursor()

    data_counts = {}

    for country in countries:
        if oecd_status == 'All':
            cursor.execute(f"SELECT {question_code} FROM pisa2022_data WHERE CountryRegion='{country}'")
        else:
            cursor.execute(f"SELECT {question_code} FROM pisa2022_data WHERE CountryRegion='{country}' AND OECD='{oecd_status}'")
        data = cursor.fetchall()

        # Count occurrences of each value for the current country
        counts = pd.DataFrame(data, columns=[question_code]).value_counts().reset_index(name='Count')

        # Fetch the question label from the codebook
        question_label = fetch_questions().get(question_code, 'Unknown')

        data_counts[country] = {'label': question_label, 'counts_df': counts}

    conn.close()
    return data_counts

