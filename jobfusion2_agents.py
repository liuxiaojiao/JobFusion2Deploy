from crewai import Agent
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
# from tavily import TavilyClient

# from tools.browser_tools import BrowserTools
from crewai_tools import ScrapeWebsiteTool, DOCXSearchTool, SeleniumScrapingTool
import docx2txt
import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"] 
openai_api_key = st.secrets["OPENAI_API_KEY"]

# from dotenv import load_dotenv
# load_dotenv()
# openai_api_key = os.getenv('OPENAI_API_KEY')

llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo', temperature=0.7)
manager_llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo')

class JobFusion2_Agents():
    def __init__(self, ori_resume_input, ori_personal_writeup_input, latest_resume_input):
        self.original_resume_input = ori_resume_input
        self.original_personal_writeup_input = ori_personal_writeup_input
        self.latest_resume_input = latest_resume_input

    def resume_strategist(self):
        return Agent(
                role='Resume Strategist for Data Scientist',
                goal='To create a new version of a resume that effectively aligns with job qualifications and fully incorporates the user’s feedback across multiple areas, ensuring a polished and tailored final document.',
                backstory=('''You are a seasoned resume strategist with years of experience in transforming resumes into compelling narratives that reflect the true potential of candidates. \
                           Your expertise lies in not only highlighting the strengths and achievements of an individual but also in carefully revising resumes to incorporate detailed feedback from users. \
                           Whether it's adding new information, correcting errors, or adjusting the style and format, you ensure that the final resume fully aligns with both the job qualifications and the user’s preferences..'''),
                llm=llm_35_turbo,
                tools=[DOCXSearchTool()],
                allow_delegation=False,
                verbose=True,
                max_iter=5)
    
    def document_validation_manager(self):
        return Agent(
                role='Document Validation Manager',
                goal='To review and validate updated resumes, ensuring they fully align with job qualifications and incorporate all user feedback. Your objective is to produce a final error-free resume that is ready for submission.',
                backstory=('''You are a seasoned document validation expert with a sharp eye for detail and precision. Your expertise ensures that resumes are error-free, fully incorporate user feedback, \
                           and align with strategic goals. You understand the crucial role a resume plays in the job search process and are committed to delivering flawless, submission-ready documents.'''),
                manager_llm=manager_llm_35_turbo,
                allow_delegation=True,  # Enabling delegation
                agents=[self.resume_strategist, self.cover_letter_strategist],  # Subordinate agents
                verbose=True,
                max_iter=5)
    
    def cover_letter_strategist(self):
        return Agent(
                role='Cover Letter Strategist for Data Scientist',
                goal='To craft a compelling, targeted cover letter that effectively aligns the candidate’s qualifications with the job requirements, enhancing their chances of securing the position.',
                backstory=('''You are a skilled cover letter strategist who crafts persuasive narratives that resonate with hiring managers. \
                           You excel at transforming a candidate’s resume and profile into a compelling argument, \
                           clearly demonstrating their strengths and fit for the job. Your talent lies in making candidates stand out as the ideal choice for the position.'''),
                llm=llm_35_turbo,
                tools=[DOCXSearchTool(docx=self.original_personal_writeup_input)],
                allow_delegation=False,
                verbose=True,
                max_iter=5)
    

