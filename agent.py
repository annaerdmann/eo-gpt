from dotenv import load_dotenv
import os
# LLM + Langchain packages
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
import tools
import prompts
# Streamlit Frontend imports
import streamlit as st

# Load the .env file
load_dotenv()

# Access the credentials
os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY")

# Set up the LLM - OpenAIs GPT4
turbo_llm = ChatOpenAI(
    temperature=0,
    model_name='gpt-4'
)

from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain.agents import initialize_agent
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

# conversational agent memory
memory = ConversationBufferWindowMemory(
    memory_key='chat_history',
    k=3,
    return_messages=True
)

tools = [tools.downloader, tools.api_creator,  tools.analysis_tool, tools.python_tool]

conversational_agent = initialize_agent(
    agent='chat-conversational-react-description',
    tools=tools,
    llm=turbo_llm,
    verbose=True,
    max_iterations=5,
    memory=memory
)

conversational_agent.agent.llm_chain.prompt.messages[0].prompt.template = prompts.fixed_prompt
conversational_agent.agent.llm_chain.prompt.messages[2].prompt.template = prompts.fixed_human_prompt

#conversational_agent.run("What was the sea surface temperature over the mediterranean sea for Christmas eve last year (2023)?")
#conversational_agent.run("What is the name of the current american president?")


# Creating the streamlit app

# App framework
st.title('🦜🔗 KnowEO with WEkEO')
prompt = st.text_input('Ask you question on global sea surface temperature here:') 
