#### Streamlit run mock_interview_chatbot.py
import os
import sys
import docx2txt
import time
import re
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.retrievers import ContextualCompressionRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.document_compressors import LLMChainExtractor

import streamlit as st
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# # Load OpenAI API key from local env
# from dotenv import load_dotenv
# load_dotenv()
# openai_api_key = os.getenv('OPENAI_API_KEY')

# Load OpenAI API key from streamlit 
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"] 
openai_api_key = st.secrets["OPENAI_API_KEY"]
llm_35_turbo = ChatOpenAI(api_key=openai_api_key, model='gpt-3.5-turbo', temperature=0.7)

# Function to read in .txt files
def read_txt_files(txt_file_path):
    file_content = []
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        file_content.append(content)
    return file_content

# Function to load files
def file_loading(file_path):
    loaded_files = []
    for file in os.listdir(file_path):
        if file.endswith(".txt"):
            loaded_files.append(file_path + file)
    return loaded_files

# Function to load and split documents
def doc_load_split(files):
    loaders = []
    for file in files:
        if file.endswith('.pdf'):
            loaders.extend([PyPDFLoader(file)])
        elif file.endswith('.txt'):
            loaders.extend([TextLoader(file)])

    documents = []
    for loader in loaders:
        documents.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=1024,
                            chunk_overlap=16,
                            separators=['\n\n','\n','(?<=\. )',' ','']
                            )

    docs = text_splitter.split_documents(documents)
    print('Total #s of splitted chunks: {}'.format(len(docs)))
    return docs

# Function to create embeddings and index
def build_vectordb(docs):
    embeddings = OpenAIEmbeddings()
    vectordb = FAISS.from_documents(docs, embeddings)
    index_folder_path = 'output/faiss_index_chatbot'
    index_name = 'faiss_0'

    if not os.path.exists(index_folder_path):
        os.makedirs(index_folder_path)
    if len(os.listdir(index_folder_path)) == 0:
        print('Creating FAISS index...')
        vectordb.save_local(index_folder_path, index_name)
    else: 
        print('Loading FAISS index for chat!....')
        vectordb = FAISS.load_local(index_folder_path, embeddings, index_name, allow_dangerous_deserialization=True)
    return vectordb

# Function to create the QA chain
def get_qa_chain(db,k,chain_type,user_resume,user_personal_writeup, job_qualifications,openai_api_key,chat_history):
    
    compressor = LLMChainExtractor.from_llm(llm=llm_35_turbo)
    compression_retriever = ContextualCompressionRetriever(
                        base_compressor = compressor,
                        base_retriever = db.as_retriever(search_type='mmr'),
                        search_kwargs={"k": k}
                        )

    template = '''
    You are a Senior Career Advisor chatbot designed to assist candidates in preparing for mock interviews 
    based on provided resumes, personal writeup and job qualifications. Your primary functions include:
    Generate a list of potential interview questions based on the job description, user's past experience and skills based on user's given resume and personal writeup.
    Conduct a mock interview by asking these questions and evaluating the candidate's responses.
    Provide detailed feedback on the candidate's answers, focusing on content, delivery, and confidence.
    Offer tips and strategies to improve interview performance.
    Offer general advice on job searching, networking, and career development.

    You should be professional, supportive, and encouraging in all interactions. 
    You should ensure feedback is constructive and actionable.
    You should maintain the confidentiality and privacy of the candidate's information.
    You should adapt advice based on the industry and specific job role the candidate is targeting.

    You can refer to the context to provide strategies and tips for improving the candidate's interview performance: {context}.
    
    You can use the following information to generate questions or provide feedback:
    Job Qualifications: {job_qualifications}
    User Resume: {resume}
    User Personal Writeup: {personal_writeup}

    Chat History: {chat_history}
    Question: {question}
    
    Helpful Answer:
    '''

    qa_chain_prompt = PromptTemplate(template=template,
                                    input_variables=["context", "question","chat_history"],
                                    partial_variables={ 'resume':user_resume,
                                                        'personal_writeup': user_personal_writeup,
                                                        'job_qualifications': job_qualifications})

    # memory = ConversationBufferMemory(memory_key='chat_history',
    #                                   return_messages=True,
    #                                   input_key='question',
    #                                   output_key='answer')
    
    qa_chain = ConversationalRetrievalChain.from_llm(
                                            llm=llm_35_turbo,
                                            chain_type=chain_type, #chain_type:stuff, map_reduce, refine
                                            retriever=compression_retriever,
                                            combine_docs_chain_kwargs={"prompt": qa_chain_prompt}
    )
    return qa_chain

# Function to update chat history
def update_chat_history(chat_history, user_input, bot_response):
    chat_history.append((user_input, bot_response))
    return chat_history

# Function to print chat history
def print_chat_history(chat_history):
    for i, (user_input, bot_response) in enumerate(chat_history):
        print(f"You: {user_input}")
        print(f"Bot: {bot_response}")
        print()

# streamlit app
def main():
    st.title("Career Advisor Chatbot")
    st.write("Welcome to your personal Career Advisor chatbot! Type your message below:")

    # Load and split documents
    files = file_loading("inputs/")
    docs = doc_load_split(files)

    # Create embeddings and index
    db = build_vectordb(docs)

    # User inputs
    resume_input_path = "inputs/resume_AI.docx"
    personal_writeup_input_path = "inputs/skills_profile.docx"
    user_personal_writeup = docx2txt.process(personal_writeup_input_path)
    user_resume = docx2txt.process(resume_input_path)

    job_qualifications = []
    with open("output/jd.txt", 'r', encoding='utf-8') as file:
        content = file.read()
        job_qualifications.append(content)

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

    # Create QA chain
    qa_chain = get_qa_chain(db, k=3, chain_type="stuff", user_resume=user_resume, 
                            user_personal_writeup=user_personal_writeup, 
                            job_qualifications=job_qualifications,
                            openai_api_key=openai_api_key,
                            chat_history=chat_history)

    if prompt := st.chat_input("How can I help you?"):     
        if prompt is not None:
            st.session_state.messages.append({'role': 'user', 'content': prompt})
            with st.chat_message('user'):
                st.write(f'{prompt}')
            
            with st.chat_message('assistant'):
                message_placeholder = st.empty()
                full_response = ""
                
                bot_response = qa_chain.run({"question": prompt, "chat_history": chat_history})
                # Simulate stream of responsewith milliseconds delay
                for chunk in re.findall(r'\S+|\n', bot_response):
                    full_response += chunk + " "
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)

                # # Get bot response
                # with st.spinner("Thinking..."):
                #     bot_response = qa_chain.run({"context": "", "question": prompt, "chat_history": chat_history})
                #     st.write(f'Advisor:')
                #     full_response = ""
                #     for chunk in re.findall(r'\S+|\n', bot_response):
                #         full_response += chunk + " "
                #         time.sleep(0.05)
                #         st.write(full_response  + "▌")
                        
                #     st.write("")
                # Update chat history
                chat_history = update_chat_history(chat_history, prompt, bot_response)

                # Print updated chat history
                st.session_state['chat_history'] = chat_history
                st.session_state.messages.append({'role': 'assistant', 'content': bot_response})

    if 'chat_history' in st.session_state and st.button('Finish the Chat'):
        st.write("Thank you for using the Career Advisor chatbot! Have a great day!")
        feedback_text = st.text_area("Please provide feedback on your experience with the chatbot:")
        if st.button("Submit Feedback"):
            st.write("Feedback submitted. Thank you!")
            st.stop()


if __name__ == "__main__":
    main()
