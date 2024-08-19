import os
import sys
import logging
import streamlit as st
import docx2txt
from crewai import Crew, Task, Agent
from crewai_tools import ScrapeWebsiteTool
from jobfusion_agents import JobFusion_Agents
from jobfusion_tasks import JobFusion_Tasks
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

# Initialize OpenAI API model
llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo', temperature=0.7)

# JobFusion Crew Class
class JobFusionCrew:
    def __init__(self, resume_input, personal_writeup_input, jd_url_input):
        self.resume_input = resume_input
        self.personal_writeup_input = personal_writeup_input  
        self.jd_url = jd_url_input 

    def run(self):
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

        results = crew.kickoff()
        return results

# Setup Streamlit UI
def setup_streamlit_ui():
    st.subheader('Welcome to JobFusion Crew -- AI-powered career advisory service with an agentic workflow to help you secure job interviews.')
    st.write('Please upload your personal write-up, resume, and job description link.')
    st.text('')

    uploaded_resume = st.file_uploader('Step 1: Upload your resume:', type=['txt', 'docx', 'pdf'])
    uploaded_personal_writeup = st.file_uploader('Step 2: Upload your personal writeup:', type=['txt', 'docx', 'pdf'])
    jd_url_input = st.text_area(label='Step 3: Enter the URL of the job you are applying for:', placeholder='Paste the job description link/URL here...')

    return uploaded_resume, uploaded_personal_writeup, jd_url_input

# Main function
def main():
    uploaded_resume, uploaded_personal_writeup, jd_url_input = setup_streamlit_ui()

    if st.button('Start Processing'):
        if uploaded_resume and uploaded_personal_writeup and jd_url_input:
            st.write('Processing now....')
            logger.debug('Starting Agentic Workflow')

            # create output directory to store angent outputs
            os.makedirs("output/", exist_ok=True)

            resume_path = os.path.join("streamlit/", uploaded_resume.name)
            os.makedirs(os.path.dirname(resume_path), exist_ok=True)
            with open(resume_path, "wb") as f:
                f.write(uploaded_resume.getbuffer())

            personal_writeup_path = os.path.join("streamlit/", uploaded_personal_writeup.name)
            os.makedirs(os.path.dirname(personal_writeup_path), exist_ok=True)
            with open(personal_writeup_path, "wb") as f:
                f.write(uploaded_personal_writeup.getbuffer())

            JobFusionCrew(resume_path, personal_writeup_path, jd_url_input).run()
            logger.debug('Agentic Workflow finished')
        else:
            st.error("Please upload both resume and personal writeup.")
            logger.error("Both resume and personal writeup are required.")

    col1, col2, col3 = st.columns([1, 1, 1])

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
    
    # Career Advice/Mock Interview Chatbot
    st.text('')
    st.text('')
    st.write('You can chat with Career Adviser.')
    if uploaded_resume and uploaded_personal_writeup and jd_url_input:
        logger.debug('Starting Career Advice Chatbot')
        resume_path = os.path.join("streamlit/", uploaded_resume.name)
        personal_writeup_path = os.path.join("streamlit/", uploaded_personal_writeup.name)
        user_resume = docx2txt.process(resume_path)
        user_personal_writeup = docx2txt.process(personal_writeup_path)
        job_qualifications = []
        with open("output/jd.txt", 'r', encoding='utf-8') as file:
            content = file.read()
            job_qualifications.append(content)
        logger.debug("Resume and personal writeup loaded successfully.")

        if 'chat_history' in st.session_state:
            chat_history = st.session_state['chat_history']
        else:
            chat_history = []

        # Store generated responses
        if "messages" not in st.session_state.keys():
            st.session_state.messages = [{"role": "assistant", "content": "How may I help you?"}]

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        # read in job qualifications from the output of JobFusionCrew
        # jd_result = WEBScrapeWebsiteToolAgent(cfg.web_agent_role, cfg.web_agent_goal, cfg.web_agent_bk, cfg.web_task_goal, jd_url_input)
        files = file_loading("inputs/contents/")
        docs = doc_load_split(files)
        db = build_vectordb(docs)

        if db:
            chat_history = st.session_state.get('chat_history', [])
            qa_chain = get_qa_chain(
                db, k=3, chain_type="stuff", user_resume=user_resume, 
                user_personal_writeup=user_personal_writeup, job_qualifications=job_qualifications,
                openai_api_key=openai_api_key, chat_history=chat_history
            )

            if prompt := st.chat_input("How can I help you?"):
                if prompt is not None:
                    st.session_state.messages.append({'role': 'user', 'content': prompt})
                    with st.chat_message('user'):
                        st.write(f'{prompt}')
                    with st.chat_message('assistant'):
                        message_placeholder = st.empty()
                        full_response = ""
                        bot_response = qa_chain.run({"question": prompt, "chat_history": chat_history})
                        for chunk in re.findall(r'\S+|\n', bot_response):
                            full_response += chunk + " "
                            time.sleep(0.05)
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                        chat_history = update_chat_history(chat_history, prompt, bot_response)

                        # Print updated chat history
                        st.session_state['chat_history'] = chat_history
                        st.session_state.messages.append({'role': 'assistant', 'content': bot_response})
        else:
            st.error("Failed to build vector database.")
            logger.error("Failed to build vector database.")

        if 'chat_history' in st.session_state and st.button('Finish the Chat'):
            st.write("Thank you for using the Career Advisor chatbot! Have a great day!")
            feedback_text = st.text_area("Please provide feedback on your experience with the chatbot:")
            if st.button("Submit Feedback"):
                st.write("Feedback submitted. Thank you!")
                st.stop()

if __name__ == "__main__":
    main()
