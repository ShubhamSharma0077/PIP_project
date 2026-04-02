import pandas as pd
import joblib
from typing import Optional
from llm_call import RoundRobinLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path

BASE_PATH = Path(__file__).parent.resolve()

class MLInferenceEngine:
    def __init__(self):
        # Initialize LLM
        self.llm = RoundRobinLLM()
        
        # Load one-hot encoder
        self.encoder = joblib.load(BASE_PATH/"onehot_encoder.pkl")
        
        # Load models
        self.models = {
            "Attrition_model": joblib.load(BASE_PATH/"attrition_model.pkl"),
            "engagement_model": joblib.load(BASE_PATH/"engagement_model.pkl"),
            "performance_model": joblib.load(BASE_PATH/"performance_model.pkl")
        }
        
        # LLM chain for extracting employee_id and model type
        class MLInstructClass(BaseModel):
            employee_id: str = Field(description="Employee ID extracted from user query")
            prediction_model: Literal["Attrition_model","engagement_model","performance_model"] = Field(description="Type of prediction required")
        
        ml_instruct_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are an intelligent extraction engine.

Your task:
- Extract employee_id from the user query
- Identify which prediction model is needed

Model selection rules:
- Attrition_model → if query mentions leaving, churn, retention, risk
- engagement_model → if query mentions engagement, satisfaction
- performance_model → if query mentions performance, rating, productivity

Rules:
- Return ONLY valid JSON
- Do NOT explain anything
- Do NOT hallucinate employee_id (return "" if not present)
- Use exact model names only
"""
            ),
            (
                "human",
                """
Previous conversation (use only if needed or related to current user query):
{history}

Current user query:
{user_query}

Output format:
{{
    "employee_id": "string",
    "prediction_model": "Attrition_model | engagement_model | performance_model"
}}
"""
            )
        ])
        
        self.ml_instruct_chain = (
            ml_instruct_prompt
            | self.llm
            | PydanticOutputParser(pydantic_object=MLInstructClass)
        ).with_retry(
            retry_if_exception_type=(OutputParserException,),
            stop_after_attempt=3
        )

    def predict_employee(self, user_query: str, history: Optional[str] = None, df_path: str = r"...\Synthetic_Data\feedback_sentiment_analysis.csv"):
        # Step 1: Extract employee ID and model type
        ml_instruct_result = self.ml_instruct_chain.invoke({
            "history": history,
            "user_query": user_query
        })
        
        employee_id = ml_instruct_result.employee_id
        prediction_model = ml_instruct_result.prediction_model
        
        # Step 2: Load and filter employee data
        df = pd.read_csv(r"Synthetic_Data\feedback_sentiment_analysis.csv")
        df["survey_date"] = pd.to_datetime(df["survey_date"], format="%d-%m-%Y")
        # filtered_df = df[df["employee_id"] == employee_id].sort_values(by="survey_date")
        filtered_df = df[df["employee_id"].str.lower() == employee_id.lower()].sort_values(by="survey_date")
        last_row_df = filtered_df.tail(1)
        
        next_year = int(last_row_df["survey_date"].dt.year.iloc[0] + 1)
        current_year = int(df["survey_date"].dt.year.max())
        
        json_data = filtered_df.to_json(orient="records", date_format="iso")
        
        # Step 3: Prepare features using encoder
        for col in self.encoder.feature_names_in_:
            if col not in last_row_df.columns:
                last_row_df[col] = 0  # set missing columns to 0
        
        last_row_df = last_row_df[self.encoder.feature_names_in_]
        df_encoded = self.encoder.transform(last_row_df)
        
        # Step 4: Predict using the appropriate model
        model = self.models[prediction_model]
        
        # Align columns with model
        for col in model.feature_names_in_:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
        df_encoded = df_encoded[model.feature_names_in_]
        
        if prediction_model == "Attrition_model":
            prediction = model.predict_proba(df_encoded)[0][0]  # probability of attrition
        else:
            prediction = model.predict(df_encoded)[0]
        
        # Step 5: Generate insight prompt
        prompt = f"""
Previous conversation (only if relevant):
{history}

Current user query:
{user_query}

Employee data details:
{json_data}

Prediction type: {prediction_model}
Prediction for employee in next year ({next_year}): {prediction}

Consider the current year as {current_year} when interpreting this prediction.

Generate a professional insight for this employee based on the above information.

Answer in 3 lines
"""
        
        result = self.llm.invoke(prompt)
        return result.content