import streamlit as st
from dotenv import load_dotenv
import os
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# In-memory user database for demo purposes
user_db = {}

# Function to register a user
def register_user(email, password):
    if email in user_db:
        return "Email already exists!"
    user_db[email] = password
    return "Registration successful!"

# Function to log in a user
def login_user(email, password):
    if email not in user_db:
        return "Email not found!"
    if user_db[email] != password:
        return "Incorrect password!"
    return "Login successful!"

# Function to handle PDF file conversion to images
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Function to get Gemini API response
def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

# Employee (User) Page - Resume Checker
def employee_page():
    st.subheader("Resume Checker")
    
    input_text = st.text_area("Job Description: ", key="input")
    uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

    if uploaded_file is not None:
        st.write("PDF Uploaded Successfully")

    submit1 = st.button("Tell Me About the Resume")
    submit3 = st.button("Percentage Match")

    input_prompt1 = """
    You are an experienced Technical Human Resource Manager. Your task is to review the provided resume against the job description. 
    Please share your professional evaluation on whether the candidate's profile aligns with the role. 
    Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
    """

    input_prompt3 = """
    You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality, 
    your task is to evaluate the resume against the provided job description. Give me the percentage of match if the resume matches
    the job description. First the output should come as percentage, then keywords missing, and last final thoughts.
    """

    if submit1:
        if uploaded_file is not None:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt1, pdf_content, input_text)
            st.subheader("The Response is")
            st.write(response)
        else:
            st.write("Please upload the resume")

    elif submit3:
        if uploaded_file is not None:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt3, pdf_content, input_text)
            st.subheader("The Response is")
            st.write(response)
        else:
            st.write("Please upload the resume")

# Organization Page - Job Description Generator
def organization_page():
    st.subheader("Job Description Generator")
    
    # Collect input fields for JD generation
    job_title = st.text_input("Job Title")
    required_skills = st.text_area("Required Skills")
    experience_range = st.selectbox("Experience Range", ["1-3 years", "3-5 years", "5+ years"])
    job_location = st.text_input("Job Location")
    company_name = st.text_input("Company Name")
    job_summary = st.text_area("Job Summary")

    # Button to generate JD
    if st.button("Generate JD"):
        if job_title and required_skills and experience_range and job_location and company_name and job_summary:
            prompt = f"""
            Job Title: {job_title}
            Required Skills: {required_skills}
            Experience Range: {experience_range}
            Job Location: {job_location}
            Company Name: {company_name}
            Job Summary: {job_summary}
            
            Please generate a detailed job description with the provided details. 
            The JD should include sections on job responsibilities, qualifications, and required skills.
            """
            response = genai.GenerativeModel('gemini-pro-vision').generate_content([prompt])
            st.subheader("Generated Job Description")
            st.write(response.text)
        else:
            st.warning("Please fill in all fields to generate the JD.")

# Login and Registration Page
def login_page():
    st.title("Welcome to ATS & JD Generator")

    # Allow users to choose between login and registration
    page = st.radio("Choose an option", ["Login", "Register"])

    if page == "Register":
        st.subheader("Create a new account")

        # Registration form
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')

        if st.button("Register"):
            if password != confirm_password:
                st.error("Passwords do not match!")
            elif not email or not password:
                st.error("Please fill in all fields!")
            else:
                result = register_user(email, password)
                st.success(result)
                # Set session state to indicate successful registration
                st.session_state.logged_in = True
                st.session_state.email = email
                st.session_state.role = None
                # Redirect to role selection
                role_selection()

    elif page == "Login":
        st.subheader("Login to your account")

        # Login form
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            if not email or not password:
                st.error("Please fill in both fields!")
            else:
                result = login_user(email, password)
                if result == "Login successful!":
                    st.success(result)
                    # Set session state to indicate successful login
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.session_state.role = None
                    # Redirect to role selection
                    role_selection()
                else:
                    st.error(result)

# Role Selection after successful login or registration
def role_selection():
    if st.session_state.logged_in:
        email = st.session_state.email
        role = st.radio(f"Welcome {email}! Please select your role", ["Employee", "Organization"])

        # Save role in session state
        st.session_state.role = role

        if role == "Employee":
            employee_page()
        elif role == "Organization":
            organization_page()

# Main entry point of the app
def main():
    # Check if the user is already logged in
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        # If not logged in, show the login page
        login_page()
    else:
        # If logged in, show role selection
        role_selection()

# Run the app
if __name__ == "__main__":
    main()
