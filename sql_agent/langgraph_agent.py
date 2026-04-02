
from llm_call import RoundRobinLLM
from ml_model import MLInferenceEngine
from summarizer import MapReduceSummarizer
from sql_agent.sql_insight_agent import SQLInsightService
from rag import ask_rag
import pandas as pd
import io
import json
import os, time

from langgraph.graph import StateGraph, START, END

import sys
import operator
import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from typing import Annotated, List, TypedDict, Literal
from typing_extensions import Literal as TypedLiteral

from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableConfig

from langchain.messages import HumanMessage, SystemMessage

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver

from IPython.display import Markdown
from io import StringIO




###############


gloabal_df=pd.read_csv(r"Synthetic_Data\feedback_sentiment_analysis.csv")
gloabal_df["survey_date"] = pd.to_datetime(gloabal_df["survey_date"], format="%d-%m-%Y")



SQLInsightAgent = SQLInsightService()

llm=RoundRobinLLM()

summarizer = MapReduceSummarizer(llm=llm,max_chunk=10,)

ML_Engine = MLInferenceEngine()







def get_thread_history(config,history_number=None):
    history = list(graph.get_state_history(config))


    result=[]

    for idx, i in enumerate(history, start=1):
        i_values = i.values
        
        data = {
            "user_query": i_values.get("user_query", ""),
            "insight_content": i_values.get("insight_content", "")
        }
        
        result.append(data)


    result_df=pd.DataFrame(result)


    result_df.drop_duplicates(inplace=True)
    result_df.dropna(inplace=True)
    json_data = json.loads(result_df.to_json(orient="records"))
    json_data=json_data[::-1]

    if history_number!=None:
        json_data=json_data[-history_number:]

    return json_data



########################################################################################################

# class Sql_class(BaseModel):
#     sql: str
    
# sql_generate_prompt = ChatPromptTemplate.from_messages([
#     (
#         "system",
#         """
# You are an data analysis and sql expert.
# you have to analysis user query and df information and deside what should be appropiate data needed to answer that user query.
# Here is last 3 previous user convertion:{history}

# forcus on history only if needed to answer current answer,otherwise ignore it
# Your task is to generate DuckDB SQL queries that need to be applied on "data" table .
# Dont halluciante or generate any data your self while generating query
# -dont return commplete df
# -make sql so that all necessary insight can be returned needed to answer query.
# """
#     ),
#     (
#         "human",
#         """
# user query: {user_query}
# columns in input Dataset: {columns}
# Column info: {info}
# Unique values summary: {unique_values_data}

# Output format (strict JSON, no extra text):
# {{
#     "sql": "string"
# }}
# """
#     )
# ])



# llm_sql = (
#     sql_generate_prompt
#     | llm
#     | PydanticOutputParser(pydantic_object=Sql_class)
# ).with_retry(
#     retry_if_exception_type=(OutputParserException,),
#     stop_after_attempt=3
# )

# #############################################################



# refine_prompt = ChatPromptTemplate.from_messages([
#     (
#         "system",
#         """
# You are an expert in SQL optimization.

# The previous query returned too many rows.

# Your task:
# - Modify the SQL to reduce number of rows without effecting detail needed for reply
# - Prefer:
# - aggregation (AVG, SUM, COUNT)
# - GROUP BY
# - LIMIT
# - filtering

# Return only JSON.

# """
#     ),
#     (
#         "human",
#         """
# Here is last 3 previous user convertion:{history}

# forcus on history only if needed to answer current answer,otherwise ignore it,

# User Query: {user_query}

# current SQL:
# {prev_sql}

# Dataset columns: {columns}

# info:{info}

# this current sql query return large number of row .
# Make SQL to return less rows without losing any important information needed to answer the user query.

# Output format:
# {{
#     "sql": "string"
# }}
# """
#     )
# ])


# llm_refine = (
#     refine_prompt
#     | llm
#     | PydanticOutputParser(pydantic_object=Sql_class)
# ).with_retry(
#     retry_if_exception_type=(OutputParserException,),
#     stop_after_attempt=3
# )

# ########################################################################################


# def execute_sql_with_refinement(user_query,history,df):
#     columns=df.columns
#     # info=df.info()
#     info = (lambda b: (df.info(buf=b), b.getvalue())[1])(__import__("io").StringIO())
#     unique_values = {col: df[col].unique() for col in ["department","performance_rating","feedback_category","sentiment"]}
#     unique_values_data=""

#     for col, values in unique_values.items():
#         unique_values_data=unique_values_data+f"Column '{col}' unique values: {values}"




#     # Step 1: Initial SQL
#     r = llm_sql.invoke({
#         "columns": columns,
#         "info": info,
#         "unique_values_data": unique_values_data,
#         "user_query": user_query,
#         "history":history
#     })

#     con = duckdb.connect()
#     # con.register("data", df)
#     con.execute("DROP TABLE IF EXISTS data")  # optional cleanup
#     con.execute("CREATE OR REPLACE TABLE data AS SELECT * FROM df")

#     con.execute("""
#     CREATE OR REPLACE TABLE data AS
#     SELECT
#         employee_id::VARCHAR AS employee_id,
#         department::VARCHAR AS department,
#         tenure_years::DOUBLE AS tenure_years,
#         performance_rating::INTEGER AS performance_rating,
#         engagement_score::INTEGER AS engagement_score,
#         feedback_comment::VARCHAR AS feedback_comment,
#         CAST(survey_date AS DATE) AS survey_date,
#         feedback_category::VARCHAR AS feedback_category,
#         sentiment::VARCHAR AS sentiment,
#         summary::VARCHAR AS summary
#     FROM df
#     """)

#     MAX_LEN=70000

#     for attempt in range(3): 
#         print(r.sql)

#         result_df = con.execute(r.sql).df()
#         result_str = result_df.to_string()

#         # ✅ Check length
#         if len(result_str) <= MAX_LEN:
#             return result_df, r.sql
        

#         print(f"⚠️ Result too large ({len(result_str)}), refining SQL...")


#         # Step 2: Refine SQL
#         r = llm_refine.invoke({
#             "user_query": user_query,
#             "prev_sql": r.sql,
#             "info": info,
#             "columns": columns,
#             "history":history
#         })

#     # Final fallback
#     return result_df.head(100), r.sql


#################################################################################################################################








# =========================================================
# 1. OUTPUT SCHEMA
# =========================================================
class router_Decision_class(BaseModel):

    router_decision: Literal["sql_node", "END","simple_question","ml_prediction","summary_report","rag"] = Field(
        description="Routing decision: either 'email' if email needs edits, or 'none' if email is fine"
    )
    reason: str = Field(
        description="Short explanation "
    )



# =========================================================
# 2. PROMPT
# =========================================================
router_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a router you have to return any one of ["sql_node", "simple_question","ml_prediction","summary_report","rag"] in result.


1. "ml_prediction":(when one specific individual employee id is also given) and (prediction for "attrition" or "performance" or "engagement" only)
2. "sql_node":user query is realted to any insight or wanting any result. 
3. "simple_question": Use when the query can be answered directly without using any dataset or external data.
4. "summary_report":if query asked to generate summanry report or generate summary of chat history
5. "rag":if user ask for HR polices and something that may be get from hr related documents(leaves,perfomance polices,work policies,reward polices). 

Rules:
- Focus on current query. Use history only if necessary.
- Do NOT assume missing data.
- Always choose ONLY ONE option.
- Be precise and deterministic.
"""
        ),
        (
            "human",
            """
Here is last 3 previous user convertion:{history}

forcus on history only if needed to answer current query,otherwise ignore it,


current human query :{user_query}



output format:
{{
  "router_decision": "sql_node | ml_prediction | simple_question | END | summary_report | rag",
  "reason": "Short explanation (1 sentence)"
}}


Decide the next action.
"""
        ),
    ]
)

# =========================================================
# 3. CHAIN
# =========================================================
router_chain = (
    router_prompt
    | llm 
    | JsonOutputParser(pydantic_object=router_Decision_class)
).with_retry(
    retry_if_exception_type=(OutputParserException,),
    stop_after_attempt=3
)






class LangGraphState(TypedDict):

    df_json: str
    user_query:str
    insight_content:str
    python_graph_code: str
    history:List

def router_node(state: LangGraphState,config: RunnableConfig):
    
    user_query = state.get("user_query", "")
    history=state.get("history", "")[-3:]

    
    decision = router_chain.invoke(
        {
            "user_query": user_query,
            "history":history
           }
    )
    print(decision)
    

    # Example condition
    if decision["router_decision"]=="sql_node":
        return "sql_node"
    elif decision["router_decision"]=="simple_question":
        return "simple_question"
    elif decision["router_decision"]=="END":
        return END
    elif decision["router_decision"]=="ml_prediction":
        return "ml_prediction"
    
    elif decision["router_decision"]=="summary_report":
        return "summary_report"
    
    elif decision["router_decision"]=="rag":
        return "rag"


def simple_question(state: LangGraphState,config: RunnableConfig):
    
    user_query = state.get("user_query", "")
    history=state.get("history", "")[-3:]
    print(user_query)
    result = llm.invoke(
      f"""
                                   this is conversation history:{history},
    use this history only be its related to current user query otherwise ignore it.
    this is cuurrent user query {user_query}
    check this user query and answer accordingily                 

                                   """
    )

    return {"insight_content": result.content}


    

def ml_prediction(state: LangGraphState,config: RunnableConfig):

    user_query =  state.get("user_query", "")
    history=state.get("history", "")[-3:]
    insight = ML_Engine.predict_employee(user_query=user_query, history=history)

    return {"insight_content":insight}





def summary_report(state: LangGraphState,config: RunnableConfig):

    history=state.get("history", "")
    history=history[1:]
    insight = summarizer.summarize(history)



    os.makedirs("summarizer/all_summary_reports", exist_ok=True)
    open(f"summarizer/all_summary_reports/summary_{int(time.time())}.txt", "w", encoding="utf-8").write(insight)



    return {"insight_content":insight,"python_graph_code":None}



# def sql_insight_generation(state: LangGraphState,config: RunnableConfig):

#     global gloabal_df
#     df=gloabal_df.copy()
#     history=state.get("history", "")[-3:]

#     user_query=state["user_query"]



#     columns = df.columns.tolist()

#     info=df.nunique()

#     unique_values = {col: df[col].unique() for col in ["department","performance_rating","feedback_category","sentiment"]}
#     unique_values_data=""

#     for col, values in unique_values.items():
#         unique_values_data=unique_values_data+f"Column '{col}' unique values: {values}"



#     # r=llm_sql.invoke({"columns":columns,"info":info,"a_str":a_str,"user_query":user_query})

#     con = duckdb.connect()
#     # con.register("data", df)
#     con.execute("DROP TABLE IF EXISTS data")  # optional cleanup
#     con.execute("CREATE OR REPLACE TABLE data AS SELECT * FROM df")

#     # result_df = con.execute(r.sql).df()
#     # result_df=result_df.to_string()

#     ###########################################################




 
#     MAX_LEN = 70000
#     # MAX_LEN = 7



#     df=df[['employee_id', 'department', 'tenure_years', 'performance_rating',
#         'engagement_score', 'feedback_comment', 'survey_date',
#         'feedback_category', 'sentiment', 'summary']]

#     filtered_df,final_sql=execute_sql_with_refinement(user_query,history,df)

        
#     filtered_df_string=filtered_df.to_string()
#     print(filtered_df_string)
#     # insight=llm.invoke(f""" Generate a professional response and just return insight for this user query: {user_query},using data ={filtered_df_string} only,dont return any code or other approach to generate data ,you have to returm only insights..

#     #                    try to answer all details asked in user query using data ,without hallucinating
#     #                 """)
#     insight = llm.invoke(f"""
#     You are a senior data analyst.

#     Your task is to generate accurate, data-driven insights based ONLY on the provided dataset.
#     Always identify early-stage or boundary patterns (e.g., very low values at low ranges).
#     in output return only insight and result should be self sufficient
#     Never criticize the input data in any way(dont tell that data set is missing some data,alway answer professionaly)
    

#     User Query:
#     {user_query}

#     Data:
#     {filtered_df_string}

#     this data is detrieved using sql query:{final_sql}

#     Instructions:

#     1. Use ONLY the given data. Do NOT hallucinate or assume missing values.

#     2. Understand the question properily.

#     3. Perform appropriate analysis:

#     4. Always check for:
#     - extreme values (min, max)
#     - unusual patterns or anomalies
#     - early-stage or boundary conditions (if applicable)

#     5. Do NOT confuse:
#     - correlation with causation
#     - averages with trends

#     6. Ensure:
#     - all numeric comparisons are accurate
#     - no contradictions in statements
#     - insights directly map to the data


#     Output Format:

#     - 2-3 lines answering the question directly
#     - Key Insights (bullet points with data support)-return insight from given data only
#     - Patterns / Trends (if applicable) -return if available otherwise ignore
#     - Business Interpretation (practical meaning)

#     Return ONLY insights. No code, no explanation of method.
#     """)




#     insight_content=insight.content


#     return {"insight_content":insight_content}






def sql_insight_generation(state: LangGraphState,config: RunnableConfig):

    global gloabal_df
    df=gloabal_df.copy()
    history=state.get("history", "")[-3:]

    user_query=state["user_query"]


    insight_content = SQLInsightAgent.sql_insight_content(
            df=df,
            history=history,
            user_query=user_query
        )




    return {"insight_content":insight_content}



def rag_node(state: LangGraphState, config: RunnableConfig):

    user_query = state.get("user_query", "")

    try:
        print("i rag")
        response = ask_rag(user_query)
        print(response)
        print("o rag")
    except Exception as e:
        response = f"RAG Error: {str(e)}"

    return {
        "insight_content": response,
        "python_graph_code": None
    }



def graph_generator(state: LangGraphState, config: RunnableConfig):

    global gloabal_df
    df = gloabal_df.copy()    

    columns = df.columns
    insight_content = state["insight_content"]
    user_query = state["user_query"]

    df_info = (lambda b: (df.info(buf=b), b.getvalue())[1])(__import__("io").StringIO())

    class GraphClass(BaseModel):
        python_code: str




    last_error = ""

    for attempt in range(3):   # 🔁 retry 3 times

        # 👉 dynamically add error only if exists
        error_context = f"{last_error}\always focus on avoid this error in code and output muct be json as told.\n" if last_error else ""
        error_context=""
        graph_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"""
Using the dataframe (already present) "df" :Assume df is already loaded in the environment,

df_column={columns}
info={df_info}

{error_context}

    steps:
    1. Filter data based on: {user_query},"insight_content":{insight_content}

    2. choose one best chart type to represent this above

    3. return only python code for this graph inside list



    rule:
    1)dont assume any data until given inside info or df_column
    2)assume df already present
    3) dont filter on basis of any assumed data or value
    4)do lower before every filter.
    5)use seabon as sns only
    6)return code for graph which is easy to undersand visually
    7)always stick to this output format
    8) use only insight data to make graph if user query is related to prediction of future value.
"""
            ),
        (
            "human",
            """

    output format json with same schema:
    {{
    python_code:python code which can be directily executable using exec()
    }}
    """
        )
        ])

        llm_graph = (
            graph_prompt
            | llm
            | PydanticOutputParser(pydantic_object=GraphClass)
        )

        try:
            _stdout = sys.stdout
            res = llm_graph.invoke({
                "user_query": user_query,
                "insight_content": insight_content
            })

            generated_code = res.python_code
            _stdout = sys.stdout
            sys.stdout = io.StringIO()  

            # 🚀 EXECUTE CODE

            exec(generated_code, {"df": df})
            plt.close('all') 

            # ✅ success → return
            return {"python_graph_code": res}

        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt+1} failed: {last_error}")
        finally:
            sys.stdout = _stdout 
            plt.ion()      

    # ❌ after 3 failures
    # raise Exception(f"Graph generation failed after 3 attempts. Last error: {last_error}")


#########################################################################################################



builder = StateGraph(LangGraphState)



builder.add_node("sql_node", sql_insight_generation)
builder.add_node("graph_node", graph_generator)
builder.add_node("simple_question", simple_question)
builder.add_node("ml_prediction", ml_prediction)
builder.add_node("summary_report", summary_report)
builder.add_node("rag", rag_node)


builder.add_conditional_edges(
    START,
    router_node,
    {
        "sql_node": "sql_node",
        "simple_question": "simple_question",
        "ml_prediction": "ml_prediction",
        "summary_report":"summary_report",
        "rag":"rag",
        "END": END
    }
)

builder.add_edge("rag", END)


builder.add_edge("sql_node", "graph_node")
builder.add_edge("ml_prediction", "graph_node")
builder.add_edge("graph_node", END)
builder.add_edge("simple_question", END)
builder.add_edge("summary_report", END)




memory = MemorySaver()


graph = builder.compile(checkpointer=memory)

