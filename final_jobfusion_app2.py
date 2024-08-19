"""
CareerAdvisor Application Script

Purpose:
--------
This script serves as the core functionality for the CareerAdvisor application, which provides users with tools for managing their career-related documents and offers guidance on career development. 
The script is divided into three main functionalities:

1. Build Docs: provides updated resume and cover letter based on job postings. Users can upload their documents and input a job URL, 
and the script will generate tailored documents that align with the job qualifications.

2. Edit Docs: enables users to provide feedback on updated documents, then modifies existing resumes and cover letters based on feedback. 
The script processes user input to refine and enhance the documents, ensuring they are optimized for job qualifications and aligned with users' opinions.

3. Career Chat: offers a chatbot that assists users with mock interviews and answers career-related questions. 
The chatbot leverages natural language processing to provide personalized advice and guidance.

Overall, the script is designed to streamline the job application process and provide users with valuable insights and support in their career journey.

The advantages of this new version of the CareerAdvisor application include:
- Improved user interface and user experience
- Enabled document editing based on user feedback

environment: peotry install based on pyproject.toml; OpenAI API key is required

script usage: poetry run streamlit run final_jobfusion_app2.py

Date: 2024-08-18
"""
import os
import sys
import logging
import streamlit as st
import docx2txt
from crewai import Crew, Task, Agent, Process
from crewai_tools import ScrapeWebsiteTool
from jobfusion_agents import JobFusion_Agents
from jobfusion_tasks import JobFusion_Tasks
from jobfusion2_agents import JobFusion2_Agents
from jobfusion2_tasks import JobFusion2_Tasks
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
from Config import configure as cfg
from mock_interview_chatbot import *
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# os.environ["OPENAI_API_KEY"] = ''

# # Load OpenAI API key from local env -- use ONLY for LOCAL development and streamlit deployment
# from dotenv import load_dotenv
# load_dotenv()
# openai_api_key = os.getenv('OPENAI_API_KEY')

# Load OpenAI API key from streamlit -- uncomment and use ONLY for streamlit cloud deployment
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"] 
openai_api_key = st.secrets["OPENAI_API_KEY"]

# Initialize OpenAI API models for use in the application
llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo', temperature=0.7)
manager_llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo')

# JobFusionCrew class to create an updated version of the resume and cover letter
class JobFusionCrew:
    def __init__(self, resume_input, personal_writeup_input, jd_url_input):
        self.resume_input = resume_input
        self.personal_writeup_input = personal_writeup_input  
        self.jd_url = jd_url_input 

    def run(self):
        # Initialize agents and tasks
        agents = JobFusion_Agents(self.resume_input, self.jd_url)
        tasks = JobFusion_Tasks(self.resume_input, self.personal_writeup_input, self.jd_url)

        crew = Crew(
            agents=[
                agents.researcher(), 
                agents.profiler(), 
                agents.resume_strategist(),
                agents.cover_letter_strategist(),
                agents.interview_preparer()
            ],
            tasks=[
                tasks.research_task(agents.researcher()),
                tasks.profile_task(agents.profiler()),
                tasks.resume_strategy_task(agents.resume_strategist()),
                tasks.cover_letter_strategy_task(agents.cover_letter_strategist()),
                tasks.interview_preparation_task(agents.interview_preparer())
            ],
            verbose=True
        )

        # Kickoff the process and return results
        results = crew.kickoff()
        return results

# JobFusionCrew 2 Class to modify the resume and cover letter based on users feedback
class JobFusionCrew2:
    def __init__(self, ori_resume_input, ori_personal_writeup_input, latest_resume_input, jd_qualifications_input, users_feedback):
        self.original_resume_input = ori_resume_input
        self.original_personal_writeup_input = ori_personal_writeup_input
        self.latest_resume_input = latest_resume_input
        self.jd_qualifications_input = jd_qualifications_input
        self.users_feedback = users_feedback

    def run(self):
        agents = JobFusion2_Agents(self.original_resume_input, self.original_personal_writeup_input, self.latest_resume_input)
        tasks = JobFusion2_Tasks(self.original_resume_input, self.original_personal_writeup_input, self.jd_qualifications_input, self.latest_resume_input, self.users_feedback)

        # Define the crew and hierarchical process
        crew = Crew(
            agents=[
                agents.resume_strategist(),
                agents.cover_letter_strategist(),
                agents.document_validation_manager()
            ],
            tasks=[
                tasks.resume_strategy_task(agents.resume_strategist()),
                tasks.cover_letter_strategy_task(agents.cover_letter_strategist()),
                tasks.document_validation_task(agents.document_validation_manager())
            ],
            process = Process.hierarchical, # Hierarchical process to manage delegation
            manager_llm = manager_llm_35_turbo,  # Assign the manager_llm to the Crew
            verbose=True
        )

        # Kickoff the process and return results
        results = crew.kickoff()
        return results

# Setup Streamlit UI components
def setup_streamlit_ui():
    st.write('Please upload your personal write-up, resume, and job description link.')
    st.text('')

    uploaded_resume = st.file_uploader('Step 1: Upload your resume:', type=['txt', 'docx', 'pdf'])
    uploaded_personal_writeup = st.file_uploader('Step 2: Upload your personal writeup:', type=['txt', 'docx', 'pdf'])
    jd_url_input = st.text_area(label='Step 3: Enter the URL of the job you are applying for:', placeholder='Paste the job description link/URL here...')

    return uploaded_resume, uploaded_personal_writeup, jd_url_input

# Main function to handle the application logic
def main():
    st.subheader('Welcome to JobFusion Crew !')
    st.write('**An AI-powered career advisory service with an agentic workflow to help you secure job interviews.**')
    
    tab1, tab2, tab3 = st.tabs(["Build Docs", "Edit Docs", "Career Chat"])

    # Tab 1: Build Documents (Resume and Cover Letter Creation)
    with tab1:
        uploaded_resume, uploaded_personal_writeup, jd_url_input = setup_streamlit_ui()
        if st.button('Start Processing'):
            if uploaded_resume and uploaded_personal_writeup and jd_url_input:
                st.write('Processing now....')
                logger.debug('Starting Agentic Workflow')

                # create output directory to store angent outputs
                os.makedirs("output/", exist_ok=True)

                # Save uploaded files
                resume_path = os.path.join("streamlit/", uploaded_resume.name)
                os.makedirs(os.path.dirname(resume_path), exist_ok=True)
                with open(resume_path, "wb") as f:
                    f.write(uploaded_resume.getbuffer())

                personal_writeup_path = os.path.join("streamlit/", uploaded_personal_writeup.name)
                os.makedirs(os.path.dirname(personal_writeup_path), exist_ok=True)
                with open(personal_writeup_path, "wb") as f:
                    f.write(uploaded_personal_writeup.getbuffer())

                # JobFusionCrew(resume_path, personal_writeup_path, jd_url_input).run()
                logger.debug('Agentic Workflow finished')
            else:
                st.error("Please upload both resume and personal writeup.")
                logger.error("Both resume and personal writeup are required.")

        col1, col2, col3 = st.columns([1, 1, 1])

        # Generate and download updated documents
        if col1.button('1 - Generate Resume'):
            with open('output/updated_resume.md', 'r') as file:
                resume_output = file.read()
            st.download_button('Download Resume', resume_output, file_name='updated_resume.txt', mime='text/plain')

        if col2.button('2 - Generate Cover Letter'):
            with open('output/coverletter.md', 'r') as file:
                cover_letter_output = file.read()
            st.download_button('Download Cover Letter', cover_letter_output, file_name='coverletter.txt', mime='text/plain')

        if col3.button('3 - Generate Interview Preparation Materials'):
            with open('output/interview_preparation_materials.txt', 'r') as file:
                interview_preparation_output = file.read()
            st.download_button('Download Interview Preparation', interview_preparation_output, file_name='interview_preparation_materials.txt', mime='text/plain')
    

    # Tab 2: Edit Documents (Resume and Cover Letter Modification based on Feedback)
    with tab2:
        st.subheader('Resume and Cover Letter Modification based on Your Feedback')

        # Gather user feedback for document modifications from four aspects
        missing_info = st.text_area(label='1. Which experiences or skills from your original resume do you believe were missed in the updated version?',
                                    placeholder="Please provide details here...")
        new_additions = st.text_area(label='2. Are there any additional achievements or project experiences that you would like to include in your resume?',
                                    placeholder="Please provide details here...")
        correct_inaccuracies = st.text_area(label='3. Do any parts of the updated resume or cover letter inaccurately represent your professional experience?',
                                    placeholder="Please provide details here...")
        general_suggestions = st.text_area(label='4. What additional suggestions do you have for improving the next version of your resume or cover letter?',
                                    placeholder="Please provide details here...")
        users_feedback = {
            'missing_info': missing_info,
            'new_additions': new_additions,
            'correct_inaccuracies': correct_inaccuracies,
            'general_suggestions': general_suggestions
        }
        
        if st.button('Start Modifying Documents Now'):
            st.write('Processing now....')
            logger.debug('Starting JobFusion2 Crew Agentic Workflow')

            # inputs paths for the modification process
            ori_resume_input = os.path.join("streamlit/", uploaded_resume.name)
            ori_personal_writeup_input = os.path.join("streamlit/", uploaded_personal_writeup.name)
            latest_resume_input = 'output/updated_resume.md'
            jd_qualifications_input = 'output/jd.txt'
            
            # Run the JobFusionCrew2 process
            JobFusionCrew2(ori_resume_input, ori_personal_writeup_input, latest_resume_input, jd_qualifications_input, users_feedback).run()
            logger.debug('Agentic Workflow JobFusionCrew2 finished')

        col1, col2 = st.columns([1, 1])

        # Generate and download revised documents
        if col1.button('1 - Generate Revised Resume'):
            with open('output/latest_resume.md', 'r') as file:
                resume_output = file.read()
            st.download_button('Download Revised Resume', resume_output, file_name='revised_resume.txt', mime='text/plain')

        if col2.button('2 - Generate Revised Cover Letter'):
            with open('output/latest_coverletter.md', 'r') as file:
                cover_letter_output = file.read()
            st.download_button('Download Revised Cover Letter', cover_letter_output, file_name='revised_coverletter.txt', mime='text/plain')

    # Tab 3: Career Advice/Mock Interview Chatbot
    with tab3:
        st.subheader('Career Advice Chatbot')
        st.write('You can chat with Career Adviser.')
        chat_container = st.container(height=300)

        # Ensure the necessary documents are uploaded
        if uploaded_resume and uploaded_personal_writeup and jd_url_input:
            logger.debug('Starting Career Advice Chatbot')

            # Load files and prepare vector database for chatbot
            files = file_loading("inputs/contents/")
            docs = doc_load_split(files)
            db = build_vectordb(docs)
            
            # Process user documents for chatbot context
            resume_path = os.path.join("streamlit/", uploaded_resume.name)
            personal_writeup_path = os.path.join("streamlit/", uploaded_personal_writeup.name)
            user_resume = docx2txt.process(resume_path)
            user_personal_writeup = docx2txt.process(personal_writeup_path)
            job_qualifications = []
            with open("output/jd.txt", 'r', encoding='utf-8') as file:
                content = file.read()
                job_qualifications.append(content)
            logger.debug("Resume and personal writeup loaded successfully.")

            # Initialize chat history if not already set
            if 'chat_history' in st.session_state:
                chat_history = st.session_state['chat_history']
            else:
                chat_history = []

            # Store generated responses
            if "messages" not in st.session_state.keys():
                st.session_state.messages = [{"role": "assistant", "content": "How may I help you?"}]

            # Display chat messages
            for message in st.session_state.messages:
                with chat_container.chat_message(message["role"]):
                    st.write(message["content"])
            
            # If vector database is ready, initialize the QA chain
            if db:
                chat_history = st.session_state.get('chat_history', [])
                qa_chain = get_qa_chain(
                    db, k=3, chain_type="stuff", user_resume=user_resume, 
                    user_personal_writeup=user_personal_writeup, job_qualifications=job_qualifications,
                    openai_api_key=openai_api_key, chat_history=chat_history
                )

                # Handle user input in the chat
                if prompt := st.chat_input("How can I help you?"):
                    if prompt is not None:
                        st.session_state.messages.append({'role': 'user', 'content': prompt})
                        with chat_container.chat_message('user'):
                            st.write(f'{prompt}')
                        with chat_container.chat_message('assistant'):
                            message_placeholder = st.empty()
                            full_response = ""
                            bot_response = qa_chain.run({"question": prompt, "chat_history": chat_history})
                            for chunk in re.findall(r'\S+|\n', bot_response):
                                full_response += chunk + " "
                                time.sleep(0.05)
                                message_placeholder.markdown(full_response + "▌")
                            message_placeholder.markdown(full_response)
                            chat_history = update_chat_history(chat_history, prompt, bot_response)

                            # Update chat history in session state
                            st.session_state['chat_history'] = chat_history
                            st.session_state.messages.append({'role': 'assistant', 'content': bot_response})
            else:
                st.error("Failed to build vector database.")
                logger.error("Failed to build vector database.")

            # End chat and collect feedback
            if 'chat_history' in st.session_state and st.button('Finish the Chat'):
                st.write("Thank you for using the Career Advisor chatbot! Have a great day!")
                feedback_text = st.text_area("Please provide feedback on your experience with the chatbot:")
                if st.button("Submit Feedback"):
                    st.write("Feedback submitted. Thank you!")
                    st.stop()

if __name__ == "__main__":
    main()
