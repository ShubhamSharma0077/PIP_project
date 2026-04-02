
from sql_agent.langgraph_agent import graph
from sql_agent.langgraph_agent import get_thread_history
import sys
import io
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from PIL import Image

# Load your CSV data
import os

# Get port from environment variable, default to 8501 for local testing
PORT = int(os.environ.get("PORT", 8501))


import matplotlib
matplotlib.use('Agg')  # Non-GUI backend

import chainlit as cl
from typing import Optional
# from chainlit_app.data_layer import CustomDataLayer
from data_layer import CustomDataLayer
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from datetime import datetime

load_dotenv()

# groq_key = os.getenv("groq_api_key")


# my_graph = graph()





@cl.header_auth_callback
def header_auth_callback(headers: dict) -> Optional[cl.User]:
    user_id = headers.get("x-ms-client-principal-name", "admin")
    return cl.User(identifier=user_id, metadata={"role": "admin", "provider": "header"})

@cl.header_auth_callback
def header_auth_callback(headers: dict):
    user_id = headers.get("x-ms-client-principal-name", "anonymous")
    return cl.User(identifier=user_id, metadata={"role": "user"})

@cl.data_layer
def get_data_layer():
    """
    Returns an instance of CustomerDataLayer.
    """
    return CustomDataLayer()

@cl.on_chat_resume
async def on_chat_resume(thread):
    # await cl.Message(content=thread).send()
    cl.user_session.set("resumed_thread", thread)
    pass




@cl.on_message
async def main(message: cl.Message):

    user = cl.user_session.get("user")  # Get authenticated user
    user_id = user.id if user else "anonymous"

    # data_layer = get_data_layer()

    thread_id_=cl.context.session.thread_id

    print(f"================================   {thread_id_}       =======================================")

    # Normal message
    user_query = message.content


    configurable={
        "thread_id": thread_id_
    }

    
    try:
        history=get_thread_history(configurable)





        response = graph.invoke(
        {
            "user_query": user_query,
            "df_json": "",
            "insight_content": "",
            "python_graph_code": "",
            "history":history
        }, 
        config=configurable
        )

    except Exception as e:
        response={}
        response["insight_content"]="error"
        print(e)



    await cl.Message(content=response["insight_content"]).send()



    df=pd.read_csv(r"Synthetic_Data\feedback_sentiment_analysis.csv")
    df["survey_date"] = pd.to_datetime(df["survey_date"], format="%d-%m-%Y")



    ####img
    def run_sns_plot(code_str: str,df):


        try:
            # Execute the dynamic code string
            exec(code_str, globals(), {"df": df, "plt": plt, "sns": sns})
        except Exception as e:
            return None, f"Error in execution: {e}"

        # Capture the plot in memory
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        return buf, None
        
    try:
        code_template=response["python_graph_code"].python_code
        code_template = code_template.replace("plt.show()", "")


        exec(code_template)


        exec("plt.savefig('plt_save.png')")

        image = cl.Image(path="./plt_save.png", name="image1", display="inline")

        await cl.Message(
            content="This message has an image!",
            elements=[image],
        ).send()


    except Exception as e:
        print(e)

    



