from typing import Annotated, List, TypedDict
import operator
from pydantic import BaseModel, Field
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
import duckdb
from llm_call import RoundRobinLLM
from io import StringIO
import pandas as pd
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from pathlib import Path



# ------------------------------
# Initialize LLM
# ------------------------------
llm = RoundRobinLLM()


# ------------------------------
# Load dataset
# ------------------------------
DF_PATH = r"Synthetic_Data\feedback_sentiment_analysis.csv"
df = pd.read_csv(DF_PATH)
df_json = df.to_json(orient="split")




# 1. Schema for report sections
# ------------------------------------------
class Section(BaseModel):
    name: str = Field(description="Name for this section of the report.")
    description: str = Field(description="Brief overview of the main topics to be covered in this section.")
    insight_task: str = Field(description="The insight generation task assigned to this section.")

class Sections(BaseModel):
    sections: List[Section] = Field(description="Sections of the HR insight report.")


# ------------------------------------------
# 2. Graph state
# ------------------------------------------
class State(TypedDict):
    sections: list[Section]
    completed_sections: Annotated[list, operator.add]
    final_report: str
    df_json:str

class WorkerState(TypedDict):
    section: Section
    completed_sections: Annotated[list, operator.add]
    df_json:str

# ------------------------------------------
# 3. Orchestrator: Decide all possible insights
# ------------------------------------------
def orchestrator(state: State):
    """
    Analyze df columns and sample data to decide which HR insights can be generated.
    Returns a list of Section objects, each with an insight_task.
    """
    df = pd.read_json(StringIO(state["df_json"]), orient="split")
    # Prepare dataset summary for LLM prompt
    columns = df.columns.tolist()
    sample_data = df.head(5).to_dict(orient="records")

    unique_values = {
                    col: [str(val).lower() for val in df[col].unique()]
                    for col in ["department", "performance_rating", "feedback_category", "sentiment"]
                }
    unique_values_str=""

    for col, values in unique_values.items():
        unique_values_str=unique_values_str+f"Column '{col}' unique values: {values}"


    planner_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
        You are an data analytics expert.
    Generate list of structured insight plans.
        generate a structured list of HR insights that can be analyzed from this data.
    focus mainly on Employee Feedback Analysis and Attrition Risk Insights
    dont involve any ml or stratistic approch 
        """
            ),
            (
                "human",
                """

    Given the dataset columns: {columns} and sample data: {sample_data},
    distinct data in catagorical columns:{unique_values_str}

    Each insight should include:
        name: str = Field(description="Name for this section of the report.")
            description: str = Field(description="Brief overview of the main topics to be covered in this section.")
            insight_task: str = Field(description="The insight generation task assigned to this section.")



    Output format:
    {{
    "sections": [
    list({{
        "name": "string | null",
        "description": "string | null",
        "insight_task": "string | null",

    }})

    }}

    Return ONLY JSON array.
        """
            )
        ])


    planner = (
        planner_prompt
        | llm
        | PydanticOutputParser(pydantic_object=Sections)
    ).with_retry(
        retry_if_exception_type=(OutputParserException,),
        stop_after_attempt=3
    )


    result = planner.invoke({"columns":columns,"sample_data":sample_data,"unique_values_str":unique_values_str})


    
    return {"sections": result.sections}

# ------------------------------------------
# 4. Worker: Generate insight using pandas + LLM
# ------------------------------------------
def llm_call(state: WorkerState):

    """
    Each worker handles one insight_task:
    1. Generate pandas code dynamically for the insight_task
    2. Run it on df
    3. Send the result to LLM to generate a human-readable report section
    """

    
    try:
        
        df = pd.read_json(StringIO(state["df_json"]), orient="split")

        result_2=str({"name":state["section"].name,"description":state["section"].description,"insight_task":state["section"].insight_task})

        class Sql_class(BaseModel):
            sql: str

        columns = df.columns.tolist()
        
        info=df.nunique()

        unique_values = {col: df[col].unique() for col in ["department","performance_rating","feedback_category","sentiment"]}
        unique_values_str=""

        for col, values in unique_values.items():
            unique_values_str=unique_values_str+f"Column '{col}' unique values: {values}"

        worker_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
        You are an expert in SQL and data analytics. 
        Your task is to generate DuckDB SQL queries that can extract data needed to answer this insight.
        - Return ONLY JSON in the exact specified format.
        - Do NOT include explanations, markdown, or extra text.
        - Make the query efficient so the result contains as few rows as needed without losing required information.
        - try not to return complete table whereever possible
        """
            ),
            (
                "human",
                """
        input data table details:
        Dataset columns: {columns}
        Column info: {info}
        catagorical columns Unique values: {unique_values_str}

        Task description: {result_2}

        Generate a DuckDB SQL query on table named 'data' to accomplish this task.

        Output format (strict JSON, no extra text):
        {{
            "sql": "string"
        }}
        """
            )
        ])


        worker = (
            worker_prompt
            | llm
            | PydanticOutputParser(pydantic_object=Sql_class)
        ).with_retry(
            retry_if_exception_type=(OutputParserException,),
            stop_after_attempt=3
        )

        worker_result=worker.invoke({"columns":columns,"info":info,"unique_values_str":unique_values_str,"result_2":result_2})

        con = duckdb.connect()
        # con.register("data", df)
        con.execute("DROP TABLE IF EXISTS data")  # optional cleanup
        con.execute("CREATE OR REPLACE TABLE data AS SELECT * FROM df")

        result_df = con.execute(worker_result.sql).df()
        result_df=result_df.to_string()

        
        insight=llm.invoke(f"""        
                Generate a concise, professional HR insight based on the following task: {result_2} 
                and the summarized data: {result_df}.
                - Focus on employee feedback, engagement, sentiment, tenure, and department trends.
                - Highlight actionable findings (e.g., departments or categories needing attention).
                - Use bullet points or 3–5 sentences max.
                - Avoid irrelevant information or speculation; do not hallucinate.
                - Format output so it can be directly included in a report.


                """)

        


        section_text = insight.content
    except Exception as e:

        section_text=""

    return {"completed_sections": [section_text]}

# ------------------------------------------
# 5. Synthesizer: Combine all sections
# ------------------------------------------
def synthesizer(state: State):
    completed_sections = state["completed_sections"]
    final_report = "\n\n---\n\n".join(completed_sections)
    return {"final_report": final_report}

# ------------------------------------------
# 6. Assign workers to each section
# ------------------------------------------
def assign_workers(state: State):
    return [Send("llm_call", {"section": s,"df_json":df_json}) for s in state["sections"]]
    # return [Send("llm_call", {"section": state["sections"]})]

# ------------------------------------------
# 7. Build workflow
# ------------------------------------------
orchestrator_worker_builder = StateGraph(State)
orchestrator_worker_builder.add_node("orchestrator", orchestrator)
orchestrator_worker_builder.add_node("llm_call", llm_call)
orchestrator_worker_builder.add_node("synthesizer", synthesizer)

orchestrator_worker_builder.add_edge(START, "orchestrator")
orchestrator_worker_builder.add_conditional_edges("orchestrator", assign_workers, ["llm_call"])
orchestrator_worker_builder.add_edge("llm_call", "synthesizer")
orchestrator_worker_builder.add_edge("synthesizer", END)

orchestrator_worker = orchestrator_worker_builder.compile()

# ------------------------------------------


# ================== STRUCTURED OUTPUT SCHEMA ==================

class HRFinalReport(BaseModel):

    final_report: str = Field(..., description="High-level sentiment trends")

# ================== OUTPUT PARSER ==================

final_insight_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are given varous insights from generated from data after analysic, you have to analysic this insight and return final report that can be directily shared with the senior manager without edit
-dont mension that this is generated for senior member.
-return detail analysic results

output format json: {{
                "final_report": "string",
            }}
            """
        ),
        (
            "human",
            """Here are the insight from various analysis:{insights_text}


"""
        )
    ])

# ================== EXTRACTION CHAIN ==================

final_insight_llm_chain = (
    final_insight_prompt
    | llm
    | PydanticOutputParser(pydantic_object=HRFinalReport)
).with_retry(
    retry_if_exception_type=(OutputParserException,),
    stop_after_attempt=1
)






def make_final_txt(output_path: str = r"orchestrator_workflow_insights\final_hr_report.txt"):
    orchestrator_worker_result = orchestrator_worker.invoke({"df_json": df_json})
    final_report_dict=final_insight_llm_chain.invoke({"insights_text":orchestrator_worker_result["final_report"]})

    
    report_text = final_report_dict.final_report

    path = Path(output_path)

    # path.write_text(report_text, encoding="utf-8")