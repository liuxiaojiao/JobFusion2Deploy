'''
Scrape webpage content from the deeplearning.ai blog
Summarize the major findings from Andrew's newsletters.
'''

import pandas as pd
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from crewai import Agent, Task
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from crewai_tools import BaseTool
import streamlit as st
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"] 
openai_api_key = st.secrets["OPENAI_API_KEY"]
llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo') # Loading GPT-3.5-turbo model

class JDScraperTools(BaseTool):
    name: str = 'Scrape the content of job description'
    description: str = ('A tool to scrape the job description content for given position URL. ')

    def __generate_web_content(self,jd_url):
        '''
        Get the article content from its URL
        '''
        # Send a GET request to the page
        response = requests.get(jd_url)
        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')

        def has_prose_in_class(html_tag):
            return html_tag.name == 'div' and html_tag.has_attr('class') and 'prose' in ' '.join(html_tag['class'])

        # Find the article content
        article_content_div = soup.find(has_prose_in_class)

        # Extract the text from the div
        article_body = article_content_div.get_text()

        return article_body
    
    # @tool('deeplearning.ai top voice scraping and summarization')
    def _run(self, jd_url: str) -> str:
        '''
        Scrape the job desription and position qualifications based on the given position URL.
        '''
        article_content_list = []
        article_content = self.__generate_web_content(jd_url)
        article_content_list.append(article_content)

        articles_urls_dict = {}
        articles_urls_dict['content'] = article_content_list

            # Convert the dictionary to a dataframe and append it to the list
        df = pd.DataFrame(articles_urls_dict)
        df_list.append(df)

        return "\n\n".join(important_findings)

