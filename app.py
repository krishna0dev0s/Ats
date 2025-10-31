import streamlit as st
import os
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai

# --------------------------
# 🔑 GEMINI API CONFIGURATION
# --------------------------

st.sidebar.title("🔑 Gemini API Configuration")
user_api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")

# Save API key
if st.sidebar.button("Save API Key"):
    if user_api_key:
        st.session_state["GEMINI_API_KEY"] = user_api_key
        genai.configure(api_key=user_api_key)
        st.sidebar.success("✅ API key saved and configured successfully!")
    else:
        st.sidebar.error("❌ Please enter a valid API key.")

# Check and configure API key
if "GEMINI_API_KEY" in st.session_state:
    genai.configure(api_key=st.session_state["GEMINI_API_KEY"])
else:
    st.sidebar.warning("⚠️ Please enter your Gemini API key to use the app.")


# --------------------------
# 👥 USER AUTHENTICATION LOGIC
# --------------------------

# (⚠️ For production, use a real database like Firebase or Supabase)
user_db = {}

def register_user(email, password):
    if email in user_db:
        return "Email already exists!"
    user_db[email] = password
    return "Registration successful!"

def login_user(email, password):
    if email not in user_db:
        return "Email not found!"
    if user_db[email] != password:
        return "Incorrect password!"
    return "Login successful!"


# --------------------------
# 📄 PDF HANDLING FUNCTIONS
# --------------------------

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]

        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")


# --------------------------
# 🤖 GEMINI RESPONSE FUNCTION
# --------------------------

def get_gemini_response(input_prompt, pdf_content, job_desc):
    if "GEMINI_API_KEY" not in st.session_state:
        return "⚠️ Please add your Gemini API key first from the sidebar."

    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([input_prompt, pdf_content[0], job_desc])
    return response.text


# --------------------------
# 🧑‍💼 EMPLOYEE PAGE
# --------------------------

def employee_page():
    st.subheader("📘 Resume Checker")

    input_text = st.text_area("Job Description: ", key="input")
    uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

    if uploaded_file is not None:
        st.success("✅ PDF Uploaded Successfully")

    submit1 = st.button("Tell Me About the Resume")
    submit3 = st.button("Percentage Match")

    input_prompt1 = """
    You are an experienced Technical Human Resource Manager. Review the resume against the job description.
    Highlight strengths and weaknesses and assess alignment with the role.
    """

    input_prompt3 = """
    You are an ATS (Applicant Tracking System) expert. Evaluate the resume vs the job description.
    Give a percentage match, list missing keywords, and share your final thoughts.
    """

    if submit1:
        if uploaded_file is not None:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt1, pdf_content, input_text)
            st.subheader("🧠 Gemini Evaluation:")
            st.write(response)
        else:
            st.error("⚠️ Please upload the resume")

    elif submit3:
        if uploaded_file is not None:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt3, pdf_content, input_text)
            st.subheader("📊 ATS Match Result:")
            st.write(response)
        else:
            st.error("⚠️ Please upload the resume")


# --------------------------
# 🏢 ORGANIZATION PAGE
# --------------------------

def organization_page():
    st.subheader("🧾 Job Description Generator")

    job_title = st.text_input("Job Title")
    required_skills = st.text_area("Required Skills")
    experience_range = st.selectbox("Experience Range", ["1-3 years", "3-5 years", "5+ years"])
    job_location = st.text_input("Job Location")
    company_name = st.text_input("Company Name")
    job_summary = st.text_area("Job Summary")

    if st.button("Generate JD"):
        if "GEMINI_API_KEY" not in st.session_state:
            st.error("⚠️ Please add your Gemini API key first from the sidebar.")
            return

        if job_title and required_skills and experience_range and job_location and company_name and job_summary:
            prompt = f"""
            Job Title: {job_title}
            Required Skills: {required_skills}
            Experience Range: {experience_range}
            Job Location: {job_location}
            Company Name: {company_name}
            Job Summary: {job_summary}

            Generate a detailed job description including:
            - Responsibilities
            - Qualifications
            - Required Skills
            """
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content([prompt])
            st.subheader("📄 Generated Job Description:")
            st.write(response.text)
        else:
            st.warning("⚠️ Please fill in all fields to generate the JD.")


# --------------------------
# 🔐 LOGIN & REGISTRATION
# --------------------------

def login_page():
    st.title("💼 Welcome to ATS & JD Generator")

    page = st.radio("Choose an option", ["Login", "Register"])

    if page == "Register":
        st.subheader("📝 Create a new account")

        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')

        if st.button("Register"):
            if password != confirm_password:
                st.error("❌ Passwords do not match!")
            elif not email or not password:
                st.error("⚠️ Please fill in all fields!")
            else:
                result = register_user(email, password)
                st.success(result)
                st.session_state.logged_in = True
                st.session_state.email = email
                st.session_state.role = None
                role_selection()

    elif page == "Login":
        st.subheader("🔑 Login to your account")

        email = st.text_input("Email")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            if not email or not password:
                st.error("⚠️ Please fill in both fields!")
            else:
                result = login_user(email, password)
                if result == "Login successful!":
                    st.success(result)
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.session_state.role = None
                    role_selection()
                else:
                    st.error(result)


# --------------------------
# 🎭 ROLE SELECTION
# --------------------------

def role_selection():
    if st.session_state.logged_in:
        email = st.session_state.email
        role = st.radio(f"Welcome {email}! Please select your role:", ["Employee", "Organization"])

        st.session_state.role = role

        if role == "Employee":
            employee_page()
        elif role == "Organization":
            organization_page()


# --------------------------
# 🚀 MAIN APP ENTRY POINT
# --------------------------

def main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        login_page()
    else:
        role_selection()


# --------------------------
# 🏁 RUN THE APP
# --------------------------

if __name__ == "__main__":
    main()
