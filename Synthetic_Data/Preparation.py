
import sys
from pathlib import Path

import os
from dotenv import load_dotenv

# load .env
load_dotenv()

# PROJECT_ROOT = Path(__file__).resolve().parents[1]
# if str(PROJECT_ROOT) not in sys.path:
#     sys.path.insert(0, str(PROJECT_ROOT))

from llm_call.llm_file import RoundRobinLLM

llm = RoundRobinLLM()

import pandas as pd
import numpy as np
import json
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from typing import List
import itertools
from pydantic import PrivateAttr
from langchain_groq import ChatGroq
import json
from typing import List
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate




# ✅ Key Takeaways
# Column	Logic & Reason
# employee_id	Unique, consistent across years, new hires added yearly and few employee remove per year
# survey_date	One per year, sequential
# department	Randomly assigned, stays same per employee
# tenure_years	0.3–1 for new hires, increment 1 for existing employees

#####
# performance_rating	Base = 2 + 2*tenure, fluctuation ±0.5, clipped 1–5
# engagement_score	performance_rating * 20 ±5, clipped 0–100
#########


def Synthetic_data_generation_first():
    # Parameters
    n_years = 4
    initial_employee_count = 100
    new_hires_per_year = [20,30,40]
    departments = ["Sales", "HR", "Engineering", "Finance", "Marketing", "Operations"]

    # Generate Year 1 employee IDs
    employee_ids_year1 = [f"E{str(i).zfill(3)}" for i in range(1, initial_employee_count+1)]

    # DataFrame to collect all years
    all_data = []

    # Dictionaries to track tenure, department, performance, engagement per employee
    tenure_dict = {}
    department_dict = {}
    performance_dict = {}
    engagement_dict = {}

    # Year 1
    df_year = pd.DataFrame({
        "employee_id": employee_ids_year1,
        "survey_date": pd.to_datetime("2019-01-01"),
    })

    # Assign department and tenure
    dept_choices = np.random.choice(departments, size=len(employee_ids_year1), replace=True)
    df_year['department'] = dept_choices
    df_year['tenure_years'] = df_year['employee_id'].apply(lambda x: round(np.random.uniform(0.3, 1.0), 2))

    # # Assign initial performance and engagement based on tenure
    # df_year['performance_rating'] = df_year['tenure_years'].apply(lambda t: round(2 + t*2 + np.random.uniform(-0.5, 0.5), 1))
    # df_year['performance_rating'] = df_year['performance_rating'].clip(1,5).round().astype(int)

    df_year['performance_rating'] = np.random.uniform(1, 5, size=len(df_year))
    df_year['performance_rating'] = (df_year['performance_rating'].clip(1, 5).round().astype(int))


    # df_year['engagement_score'] = df_year['performance_rating'].apply(lambda pr: round(pr*20 + np.random.uniform(-5,5)))
    # df_year['engagement_score'] = df_year['engagement_score'].clip(0,100)
    df_year['engagement_score'] = np.random.uniform(20, 100, size=len(df_year))
    df_year['engagement_score'] = (df_year['performance_rating'].clip(25, 95).round().astype(int))



    # Update dictionaries
    for idx, row in df_year.iterrows():
        tenure_dict[row['employee_id']] = row['tenure_years']
        department_dict[row['employee_id']] = row['department']
        performance_dict[row['employee_id']] = row['performance_rating']
        engagement_dict[row['employee_id']] = row['engagement_score']

    all_data.append(df_year)
    previous_year_ids = set(employee_ids_year1)

    # Years 2-5
    for i in range(1, n_years):
        year = 2019 + i
        retained_ids = list(np.random.choice(list(previous_year_ids),
                                            size=int(len(previous_year_ids) * 0.8),
                                            replace=False))
        n_new = new_hires_per_year[i-1] if i-1 < len(new_hires_per_year) else 0
        new_ids = [f"E{str(len(previous_year_ids)+j+1).zfill(3)}" for j in range(n_new)]
        
        employee_ids = retained_ids + new_ids
        df_year = pd.DataFrame({
            "employee_id": employee_ids,
            "survey_date": pd.to_datetime(f"{year}-01-01")
        })
        
        tenure_list, dept_list, perf_list, engage_list = [], [], [], []
        
        for emp_id in employee_ids:
            if emp_id in tenure_dict:
                # Existing employee: increment tenure
                tenure = round(tenure_dict[emp_id] + 1, 2)
                dept = department_dict[emp_id]
                # Performance: small increase + random fluctuation
                perf = round(performance_dict[emp_id] + np.random.uniform(-0.5, 0.5),1)
                perf = np.clip(perf,1,5)
                # Engagement: correlated with performance + small noise
                engage = round(perf*20 + np.random.uniform(-5,5))
                engage = np.clip(engage,0,100)
                
                # Update dicts
                tenure_dict[emp_id] = tenure
                performance_dict[emp_id] = perf
                engagement_dict[emp_id] = engage
            else:
                # New hire
                tenure = round(np.random.uniform(0.3,1.0),2)
                dept = np.random.choice(departments)
                perf = round(2 + tenure*2 + np.random.uniform(-0.5,0.5),1)
                perf = np.clip(perf,1,5)
                engage = round(perf*20 + np.random.uniform(-5,5))
                engage = np.clip(engage,0,100)
                
                tenure_dict[emp_id] = tenure
                department_dict[emp_id] = dept
                performance_dict[emp_id] = perf
                engagement_dict[emp_id] = engage
            
            tenure_list.append(tenure)
            dept_list.append(dept)
            perf_list.append(perf)
            engage_list.append(engage)
        
        df_year['tenure_years'] = tenure_list
        df_year['department'] = dept_list
        df_year['performance_rating'] = perf_list
        df_year['engagement_score'] = engage_list
        
        all_data.append(df_year)
        previous_year_ids = set(employee_ids)

    # Combine all years
    df_survey = pd.concat(all_data).reset_index(drop=True)

    return df_survey

# Preview
# print(df_survey.head(20))
# print(df_survey.groupby(df_survey['survey_date'].dt.year)['employee_id'].count())
# print(df_survey.groupby('department')['employee_id'].count())
# print(df_survey.groupby('survey_date')['performance_rating'].describe())
# print(df_survey.groupby('survey_date')['engagement_score'].describe())



###################################################################################################################################
###################################################################################################################################





# convert to list
GROQ_KEYS = os.getenv("GROQ_KEYS", "").split(",")

# clean list (remove spaces/empty)
GROQ_KEYS = [k.strip() for k in GROQ_KEYS if k.strip()]




GROQ_MODELS = ["openai/gpt-oss-120b",
               "openai/gpt-oss-20b",
# "llama-3.1-8b-instant",

"llama-3.3-70b-versatile",
# "whisper-large-v3",
# "whisper-large-v3-turbo"
]



# GROQ_MODELS = ["llama-3.1-8b-instant"]

LLMS = [
    ChatGroq(groq_api_key=k, model=m, temperature=0.8)
    for k in GROQ_KEYS
    for m in GROQ_MODELS
]



class RoundRobinLLM(BaseChatModel):
    _cycle = PrivateAttr()
    _llms = PrivateAttr()

    def __init__(self, llms: List[BaseChatModel] | None = None):
        super().__init__()
        self._llms = llms or LLMS
        self._cycle = itertools.cycle(self._llms)

    @property
    def _llm_type(self) -> str:
        return "round-robin-generic"

    def _generate(self, messages: List[BaseMessage], **kwargs):
        llm = next(self._cycle)
        return llm._generate(messages, **kwargs)

    async def _agenerate(self, messages: List[BaseMessage], **kwargs):
        llm = next(self._cycle)
        if hasattr(llm, "_agenerate"):
            return await llm._agenerate(messages, **kwargs)
        raise NotImplementedError(f"{llm} does not support async generation.")

    def with_structured_output(self, schema, **kwargs):
        llm = next(self._cycle)
        return llm.with_structured_output(schema, **kwargs)



############################################################################################################



def Synthetic_data_generation_column_feedback_comment(df_survey):

    class feedback_class(BaseModel):
        feedback_comment: List[str] = Field(
            description="List of unique employee feedback comments"
        )


    feedback_class_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
    Generate {n} unique employee feedback_comment in JSON format.

        Each feedback_comment record must be generating considering:
        - category (choose from: Work-life balance, Career growth, Management, Culture, Compensation)
        - sentiment (Positive, Neutral, Negative)

        Rules:
        - Use MIX of all categories
        - Use MIX of sentiments
        - Each comment must be unique
        - One line per comment
        - Output MUST be valid JSON array
        - No explanation text
        - return only feedback_comment without any details related to category or sentiment.

    """
        ),
        (
            "human",
            """

    output format:
        {{
            "feedback_comment": ["Workload has increased recently affecting work life balance.",......]
        }}
    """
        )
    ])


    sample_data_llm=RoundRobinLLM()

    sample_data_llm_parser = (
        feedback_class_prompt
        | sample_data_llm
        | PydanticOutputParser(pydantic_object=feedback_class)
    ).with_retry(
        retry_if_exception_type=(OutputParserException,),
        stop_after_attempt=3
    )



    def generate_feedback_batch(n=20):

        
        res = sample_data_llm_parser.invoke({"n":n})
        
        return res.feedback_comment

    # ----------------------------
    # MAIN FUNCTION: GENERATE N UNIQUE
    # ----------------------------
    import pandas as pd

    def generate_unique_feedback(total_required, batch_size=20):
        
        feedback_pool = []
        feedback_set = set()

        while len(feedback_pool) < total_required:
            batch = generate_feedback_batch(batch_size)  # List[str]

            for comment in batch:
                comment = comment.strip()

                # ✅ Correct uniqueness check
                if comment and comment not in feedback_set:
                    feedback_set.add(comment)
                    feedback_pool.append(comment)

                if len(feedback_pool) >= total_required:
                    break

        # ✅ Correct DataFrame creation
        df = pd.DataFrame({"feedback_comment": feedback_pool})

        # ✅ Series
        feedback_series = df["feedback_comment"]

        return df, feedback_series



    # ----------------------------
    # USAGE
    # ----------------------------
    df_feedback, feedback_series = generate_unique_feedback(len(df_survey))


    def attach_feedback_column(df_survey,feedback_series):

        required_n = len(df_survey)


        feedback_list = feedback_series.tolist()

        # ----------------------------
        # HANDLE SIZE MISMATCH
        # ----------------------------

        if len(feedback_list) > required_n:
            feedback_list = feedback_list[:required_n]

        elif len(feedback_list) < required_n:
            multiplier = (required_n // len(feedback_list)) + 1
            feedback_list = (feedback_list * multiplier)[:required_n]

        # ----------------------------
        # ASSIGN COLUMN
        # ----------------------------

        df_survey = df_survey.copy()
        # print(feedback_list)
        df_survey["feedback_comment"] = feedback_list

        return df_survey

        

    df_survey=attach_feedback_column(df_survey,feedback_series)

    return df_survey




######################################################################################################################################
######################################################################################################################################



##############  get_feedback_details


import pandas as pd
import numpy as np
import json
import time

# =========================
# CONFIG
# =========================
BATCH_SIZE = 10
MAX_RETRIES = 3


# =========================
# PROMPT BUILDER
# =========================
def build_prompt(comments):
    return f"""
You are a strict JSON generator.

Classify and summarize each feedback.

Return ONLY valid JSON array. No explanation, no text.

Each item must contain:
- feedback_category (Work-life balance / Career growth / Management / Culture / Compensation)
- sentiment (Positive / Neutral / Negative)
- summary (5-10 words)
- comments

Feedback list:
{json.dumps(comments)}

Expected Output:
[
  {{
    "feedback_category": "...",
    "sentiment": "...",
    "summary": "...",
    "comments": "exact comment"
  }}
]
"""


# =========================
# LLM CALL HANDLER
# =========================
def call_llm(prompt):
    response = llm.invoke(prompt)

    try:
        return response["choices"][0]["message"]["content"]
    except:
        return response.content


# =========================
# BATCH PROCESSOR WITH RETRY
# =========================
def process_batch(comments):
    for attempt in range(MAX_RETRIES):
        try:
            prompt = build_prompt(comments)
            output = call_llm(prompt)

            parsed = json.loads(output)

            # ✅ Validate structure
            if not isinstance(parsed, list):
                raise ValueError("Output is not a list")

            if len(parsed) != len(comments):
                raise ValueError("Mismatch in output size")

            df_batch = pd.DataFrame(parsed)

            required_cols = [
                "feedback_category",
                "sentiment",
                "summary",
                "comments"
            ]

            # Ensure all columns exist
            for col in required_cols:
                if col not in df_batch.columns:
                    df_batch[col] = ""

            return df_batch[required_cols]

        except Exception as e:
            print(f"Retry {attempt+1}/{MAX_RETRIES} failed: {e}")
            time.sleep(1)

    # ❌ fallback if all retries fail
    return pd.DataFrame({
        "feedback_category": ["error"] * len(comments),
        "sentiment": ["error"] * len(comments),
        "summary": ["error"] * len(comments),
        "comments": list(comments)
    })


# =========================
# MAIN FUNCTION (END-TO-END)
# =========================
def Synthetic_data_generation_get_feedback_details(df_survey):

    # Ensure clean input
    df_survey = df_survey.copy()
    comments_list = df_survey["feedback_comment"].fillna("").tolist()

    all_results = []

    # 🔁 Batch loop
    for i in range(0, len(comments_list), BATCH_SIZE):
        print(f"Processing batch {i} to {i+BATCH_SIZE}")

        batch_comments = comments_list[i:i+BATCH_SIZE]

        df_batch = process_batch(batch_comments)
        all_results.append(df_batch)

    # 🔗 Combine all batches
    df_result = pd.concat(all_results, ignore_index=True)

    # 🔗 Merge with original dataframe
    df_final = pd.concat(
        [df_survey.reset_index(drop=True), df_result],
        axis=1
    )
    df_final.drop("comments", axis=1, inplace=True)
    return df_final


