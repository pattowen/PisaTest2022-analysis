import streamlit as st
from streamlit_option_menu import option_menu  
from home import home_page  
from thai_student_page import thai_student_performance
from analytic_page import analytics_page
from user_account import display_account_page
from db_connect import connect_to_database
import hashlib  
from mysql.connector import Error

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to register a new user (remove role)
def register_user(email, password):
    hashed_password = hash_password(password)
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", 
                       (email, hashed_password))
        conn.commit()
        st.success("Registration successful! You can now log in.")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to validate user login
def validate_login(email, password):
    hashed_password = hash_password(password)
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = %s AND password = %s", (email, hashed_password))
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the email if login is successful
        else:
            st.error("Invalid email or password.")
            return None
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to display the login page
def display_login_page():
    st.subheader("🔑 Login")
    email = st.text_input("Email", key="login_email")  
    password = st.text_input("Password", type="password", key="login_password")  
    st.warning("Please enter your email and password.")

    if st.button("Login", key="login_button"):
        email = validate_login(email, password)
        if email:
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email  # Store the user email in session
            st.success(f"Logged in as {email}")
            st.rerun()  # Refresh the app after successful login to reflect the state


# Function to display the registration page
def display_registration_page():
    st.subheader("📝 Register")
    email = st.text_input("Email", key="register_email")  
    password = st.text_input("Password", type="password", key="register_password")  

    if st.button("Register", key="register_button"):
        register_user(email, password)

def main():
    # Set page configuration at the start of the main function
    st.set_page_config(
        page_title="Pisa2022 Analysis Tool",
        page_icon="🌎",
        initial_sidebar_state="expanded"
    )

    # Initialize session state for login status and email
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if 'user_email' not in st.session_state:
        st.session_state['user_email'] = None

    # If not logged in, show login or registration page
    if not st.session_state['logged_in']:
        # Using tabs instead of radio buttons for better UI experience
        tabs = st.tabs(["Login", "Register"])
        
        with tabs[0]:
            display_login_page()

        with tabs[1]:
            display_registration_page()

    else:
        # Once logged in, show the main app interface
        st.sidebar.image(r'C:\1stApril\Work\4rd_Year\4rd2\CSS400_Project_Development\CN1-2023\pisa2022_analysis\StreamlitDev\image\PISA-Blog-Ilustración.png')

        # Use the option menu for navigation
        with st.sidebar: 
            page = option_menu(
                menu_title="Main Menu",
                options=["Home", "Thai Student Performance", "Analytics", "Account", "Logout"],
                menu_icon=["cast"],
                icons=["house", "person", "file-earmark-bar-graph", "person", "power"],
                default_index=0
            )

            # Handle Logout button action
            if page == "Logout":
                st.session_state['logged_in'] = False
                st.session_state['user_email'] = None
                st.success("You have been logged out.")
                st.rerun()  # Rerun the app after logging out

        # Show different pages based on menu selection
        if page == "Home":
            home_page()
        elif page == "Thai Student Performance":
            thai_student_performance()
        elif page == "Analytics":
            analytics_page()
        elif page == "Account":
            display_account_page()  


if __name__ == "__main__":
    main()
