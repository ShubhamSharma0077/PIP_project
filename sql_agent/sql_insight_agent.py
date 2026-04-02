

from typing import Tuple, List, Dict, Any
import duckdb
import pandas as pd
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from llm_call import RoundRobinLLM


# ---------------------- CONFIG ---------------------- #
MAX_RESULT_LENGTH = 70000
MAX_RETRIES = 3



# ---------------------- MODELS ---------------------- #
class SqlResponse(BaseModel):
    sql: str


# ---------------------- SERVICE ---------------------- #
class SQLInsightService:
    def __init__(self):
        self.llm = RoundRobinLLM()
        self._init_chains()

    def _init_chains(self):
        """Initialize LLM chains."""





        sql_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an data analysis and sql expert.
you have to analysis user query and df information and deside what should be appropiate data needed to answer that user query.
Here is last 3 previous user convertion:{history}

forcus on history only if needed to answer current answer,otherwise ignore it
Your task is to generate DuckDB SQL queries that need to be applied on "data" table .
Dont halluciante or generate any data your self while generating query
-dont return commplete df
-make sql so that all necessary insight can be returned needed to answer query.
"""
    ),
    (
        "human",
        """
user query: {user_query}
columns in input Dataset: {columns}
Column info: {info}
Unique values summary: {unique_values_data}

Output format (strict JSON, no extra text):
{{
    "sql": "string"
}}
"""
    )
])

        refine_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert in SQL optimization.

The previous query returned too many rows.

Your task:
- Modify the SQL to reduce number of rows without effecting detail needed for reply
- Prefer:
- aggregation (AVG, SUM, COUNT)
- GROUP BY
- LIMIT
- filtering

Return only JSON.

"""
    ),
    (
        "human",
        """
Here is last 3 previous user convertion:{history}

forcus on history only if needed to answer current answer,otherwise ignore it,

User Query: {user_query}

current SQL:
{prev_sql}

Dataset columns: {columns}

info:{info}

this current sql query return large number of row .
Make SQL to return less rows without losing any important information needed to answer the user query.

Output format:
{{
    "sql": "string"
}}
"""
    )
])

        self.sql_chain = (
            sql_prompt
               | self.llm
                | PydanticOutputParser(pydantic_object=SqlResponse)
            ).with_retry(
                retry_if_exception_type=(OutputParserException,),
                stop_after_attempt=3
            )

        self.refine_chain = (
            refine_prompt
               | self.llm
                | PydanticOutputParser(pydantic_object=SqlResponse)
            ).with_retry(
                retry_if_exception_type=(OutputParserException,),
                stop_after_attempt=3
            )

    # ---------------------- UTILITIES ---------------------- #
    @staticmethod
    def _extract_info(df: pd.DataFrame) -> str:
        import io
        buffer = io.StringIO()
        df.info(buf=buffer)
        return buffer.getvalue()

    @staticmethod
    def _extract_unique_values(df: pd.DataFrame) -> str:
        cols = ["department", "performance_rating", "feedback_category", "sentiment"]
        result = ""

        for col in cols:
            if col in df.columns:
                values = df[col].dropna().unique()
                result += f"Column '{col}': {values}\n"

        return result

    @staticmethod
    def _prepare_duckdb(df: pd.DataFrame) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect()
        con.register("df", df)

        con.execute("""
        CREATE OR REPLACE TABLE data AS
        SELECT
            employee_id::VARCHAR,
            department::VARCHAR,
            tenure_years::DOUBLE,
            performance_rating::INTEGER,
            engagement_score::INTEGER,
            feedback_comment::VARCHAR,
            CAST(survey_date AS DATE),
            feedback_category::VARCHAR,
            sentiment::VARCHAR,
            summary::VARCHAR
        FROM df
        """)

        return con

    # ---------------------- CORE LOGIC ---------------------- #
    def _generate_sql(self, user_query: str, history: List[str], df: pd.DataFrame) -> SqlResponse:
        return self.sql_chain.invoke({
            "user_query": user_query,
            "history": history,
            "columns": df.columns.tolist(),
            "info": self._extract_info(df),
            "unique_values_data": self._extract_unique_values(df)
        })

    def _refine_sql(self, user_query: str, history: List[str], prev_sql: str, df: pd.DataFrame) -> SqlResponse:
        return self.refine_chain.invoke({
            "user_query": user_query,
            "prev_sql": prev_sql,
            "history": history,
            "columns": df.columns.tolist(),
            "info": self._extract_info(df)
        })

    def execute_sql_with_refinement(
        self,
        user_query: str,
        history: List[str],
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, str]:

        # con = self._prepare_duckdb(df)
        con = duckdb.connect()
        # con.register("data", df)
        con.execute("DROP TABLE IF EXISTS data")  # optional cleanup
        con.execute("CREATE OR REPLACE TABLE data AS SELECT * FROM df")

        con.execute("""
        CREATE OR REPLACE TABLE data AS
        SELECT
            employee_id::VARCHAR AS employee_id,
            department::VARCHAR AS department,
            tenure_years::DOUBLE AS tenure_years,
            performance_rating::INTEGER AS performance_rating,
            engagement_score::INTEGER AS engagement_score,
            feedback_comment::VARCHAR AS feedback_comment,
            CAST(survey_date AS DATE) AS survey_date,
            feedback_category::VARCHAR AS feedback_category,
            sentiment::VARCHAR AS sentiment,
            summary::VARCHAR AS summary
        FROM df
        """)









        sql_response = self._generate_sql(user_query, history, df)

        for attempt in range(MAX_RETRIES):


            try:
                result_df = con.execute(sql_response.sql).df()
                result_str = result_df.to_string()

                if len(result_str) <= MAX_RESULT_LENGTH:
                    return result_df, sql_response.sql


                sql_response = self._refine_sql(
                    user_query, history, sql_response.sql, df
                )

            except Exception as e:

                print(e)


        return result_df.head(100), sql_response.sql

    # ---------------------- FINAL FUNCTION ---------------------- #
    def sql_insight_content(
        self,
        df: pd.DataFrame,
        history: List[str],
        user_query: str
    ) -> str:

        history = history[-3:]

        df = df[[
            'employee_id', 'department', 'tenure_years',
            'performance_rating', 'engagement_score',
            'feedback_comment', 'survey_date',
            'feedback_category', 'sentiment', 'summary'
        ]]

        filtered_df, final_sql = self.execute_sql_with_refinement(
            user_query, history, df
        )

   

        insight_prompt = f"""
        You are a senior data analyst.

        Your task is to generate accurate, data-driven insights based ONLY on the provided dataset.
        Always identify early-stage or boundary patterns (e.g., very low values at low ranges).
        in output return only insight and result should be self sufficient
        Never criticize the input data in any way(dont tell that data set is missing some data,alway answer professionaly)
        

        User Query:
        {user_query}

        Data:
        {filtered_df.to_string()}

        this data is detrieved using sql query:{final_sql}

        Instructions:

        1. Use ONLY the given data. Do NOT hallucinate or assume missing values.

        2. Understand the question properily.

        3. Perform appropriate analysis:

        4. Always check for:
        - extreme values (min, max)
        - unusual patterns or anomalies
        - early-stage or boundary conditions (if applicable)

        5. Do NOT confuse:
        - correlation with causation
        - averages with trends

        6. Ensure:
        - all numeric comparisons are accurate
        - no contradictions in statements
        - insights directly map to the data


        Output Format:

        - 2-3 lines answering the question directly
        - Key Insights (bullet points with data support)-return insight from given data only
        - Patterns / Trends (if applicable) -return if available otherwise ignore
        - Business Interpretation (practical meaning)

        Return ONLY insights. No code, no explanation of method.
        """


        insight = self.llm.invoke(insight_prompt)
        return insight.content
