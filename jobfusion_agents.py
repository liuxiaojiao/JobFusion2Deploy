from crewai import Agent
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
# from tavily import TavilyClient

# from tools.browser_tools import BrowserTools
from crewai_tools import ScrapeWebsiteTool, DOCXSearchTool, SeleniumScrapingTool

import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"] 
openai_api_key = st.secrets["OPENAI_API_KEY"]

# from dotenv import load_dotenv
# load_dotenv()
# openai_api_key = os.getenv('OPENAI_API_KEY')

llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo')


class JobFusion_Agents():
    def __init__(self, resume_input, jd_url_input):
        self.resume_input = resume_input
        self.jd_url = jd_url_input

    def researcher(self):
        return Agent(
            role='Data Scientist Job Researcher',
            goal='Do amazing analysis and extraction on job posting to help job applicants',
            backstory=('As a Job Researcher, your expertise in navigating job postings and extracting critical infomation \
                is unparalleled. Your keen ability to identify the essential qualifications and skills \
                sought by employers forms the foundation for effective and tailored job applications.'),
            llm=llm_35_turbo,
            tools=[ScrapeWebsiteTool(website_url=self.jd_url)],
            allow_delegation=False,
            verbose=True,
            max_iter=5)

    def profiler(self):
        return Agent(
                role='Personal Profiler for Data Scientist',
                goal='Do incredible research on job applicants to help them stand out in the job market',
                backstory=('Equipped with analytical prowess, you dissect and synthesize infomration from diverse \
                    sources to craft comprehensive personal and professional profiles, laying the groundwork \
                    for personalized resume enhancements.'),
                llm=llm_35_turbo,
                tools=[DOCXSearchTool(docx=self.resume_input)],
                allow_delegation=False,
                verbose=True,
                max_iter=5)

    def resume_strategist(self):
        return Agent(
                role='Resume Strategist for Data Scientist',
                goal='Find all the best ways to make a resume stand out in the job market.',
                backstory=('''With a strategic mind and an eye for detail, you excel at refining resumes to highlight the \
                    most relevant skills and experiences, ensuring they resonate perfectly with the job's requirements.'''),
                llm=llm_35_turbo,
                tools=[DOCXSearchTool(docx=self.resume_input)],
                allow_delegation=False,
                verbose=True,
                max_iter=5)
    
    def cover_letter_strategist(self):
        return Agent(
                role='Cover Letter Strategist for Data Scientist',
                goal='Find all the best ways to write a cover letter stand out in the job market.',
                backstory=('''With a strategic mind and an eye for detail, you excel at highlight the \
                    most relevant skills and experiences, ensuring they resonate perfectly with the job's requirements.'''),
                llm=llm_35_turbo,
                tools=[DOCXSearchTool(docx=self.resume_input)],
                allow_delegation=False,
                verbose=True,
                max_iter=5)
    
    def interview_preparer(self):
        return Agent(
                role='Data Scientist Interview Preparer',
                goal='Create interview quetions and talking points based on the resume and job requirements',
                backstory=("""Your role is crucial in anticipanting the dynamics of interviews. With your ability to formulate \
                    key questions and talking points, you prepare candidates for success, ensuring they can confidently \
                    address all aspects of the job they are applying for."""),
                llm=llm_35_turbo,
                allow_delegation=False,
                verbose=True,
                max_iter=5)


