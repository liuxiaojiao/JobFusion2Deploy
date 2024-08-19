import json
import os

import requests
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

class SearchTools():
    @tool("Search the internet")
    def search_internet(query):
        """Useful to search the internet 
        about a a given topic and return relevant results"""
        top_result_to_return = 4
        url = "https://google.serper.dev/search"
        # url = "https://serpapi.com/search"
        payload = json.dumps({'q': query, 'num': top_result_to_return})
        headers = {
            'X-API-KEY': os.environ['SERPER_API_KEY'],
            'content-type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
     
        if 'organic' not in response.json():
            return "Sorry, couldn't find any relevant results for your query. Please try again with a different query."
        else:
            results = response.json()['organic']
            string = []
            for result in results[:top_result_to_return]:
                try:
                    string.append('\n'.join([
                        f"Title: {result['title']}", 
                        f"Link: {result['link']}",
                        f"Snippet: {result['snippet']}", 
                        "\n-----------------"
                    ]))
                except KeyError:
                    next

            return '\n'.join(string)

# if __name__ == '__main__':
#     query = "Large Language Models in Financial Services Industry"
#     res = SearchTools().search_internet(query)
#     print(res)

# Title: The Rise & Role of Large Language Models in Finance - Aisera
# Link: https://aisera.com/blog/large-language-models-in-financial-services-banking/
# Snippet: The leap to Large Language Models (LLMs) contributes to an unrivaled ability to streamline finance operations while bringing new offerings to financial markets ...

# -----------------
# Title: Large Language Models in Financial Services - KMS Solutions Blog
# Link: https://blog.kms-solutions.asia/large-language-models-in-financial-services
# Snippet: FinGPT is an open-source large language model for the finance sector. FinGPT takes a data-centric approach, providing researchers and ...

# -----------------
# Title: Transforming financial services: Harnessing large language models
# Link: https://us.nttdata.com/en/blog/2024/april/transforming-financial-services
# Snippet: Large Language Models (LLMs) are revolutionizing the financial services industry. Their massive language recognition and text generation ...

# -----------------
# Title: Large Language Models could revolutionise finance sector within ...
# Link: https://www.turing.ac.uk/news/large-language-models-could-revolutionise-finance-sector-within-two-years
# Snippet: Large Language Models (LLMs) have the potential to improve efficiency and safety in the finance sector by detecting fraud,