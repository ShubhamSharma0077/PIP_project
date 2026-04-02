import pandas as pd
import numpy as np


INPUT_FILE = "./Synthetic_Data/synthetic_employee_feedback.csv"


# ----------------------------
# LOAD DATA
# ----------------------------
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    print("Initial Shape:", df.shape)
    return df


# ----------------------------
# REMOVE DUPLICATES
# ----------------------------
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    duplicates = df.duplicated().sum()
    print("Duplicate Rows:", duplicates)
    return df.drop_duplicates()


# ----------------------------
# VALIDATE BUSINESS RULES
# ----------------------------
def validate_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    invalid_perf = df[~df["performance_rating"].between(1, 5)]
    print("Invalid Performance:", len(invalid_perf))

    # Keep only valid records
    df = df[df["performance_rating"].between(1, 5)]
    return df


# ----------------------------
# HANDLE MISSING VALUES
# ----------------------------
def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    print("\n--- Missing Values ---")
    print(df.isnull().sum())

    if "department" in df.columns:
        df["department"] = df["department"].fillna(df["department"].mode()[0])

    if "survey_date" in df.columns:
        df["survey_date"] = df["survey_date"].fillna(df["survey_date"].mode()[0])

    if "feedback_comment" in df.columns:
        df["feedback_comment"] = df["feedback_comment"].fillna("No feedback provided")

    if "employee_id" in df.columns:
        df["employee_id"] = df["employee_id"].fillna("UNKNOWN")

    for col in ["engagement_score", "performance_rating", "tenure_years"]:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    return df


# ----------------------------
# FIX DATA TYPES
# ----------------------------
def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    if "survey_date" in df.columns:
        df["survey_date"] = pd.to_datetime(df["survey_date"], errors="coerce")

    if "engagement_score" in df.columns:
        df["engagement_score"] = df["engagement_score"].astype(int)

    if "performance_rating" in df.columns:
        df["performance_rating"] = df["performance_rating"].astype(int)

    if "tenure_years" in df.columns:
        df["tenure_years"] = pd.to_numeric(df["tenure_years"], errors="coerce")

    return df


# ----------------------------
# TRANSFORMATIONS
# ----------------------------
def clean_text(text: str) -> str:
    return str(text).lower().strip()


def apply_transformations(df: pd.DataFrame) -> pd.DataFrame:
    if "feedback_comment" in df.columns:
        df["feedback_comment"] = df["feedback_comment"].apply(clean_text)

    if "department" in df.columns:
        df["department"] = df["department"].str.title()

    return df


# ----------------------------
# MAIN PIPELINE
# ----------------------------
def process_pipeline(input_path=INPUT_FILE) -> pd.DataFrame:
    df = load_data(input_path)

    print("\n--- Data Info ---")
    print(df.info())

    df = remove_duplicates(df)
    df = validate_business_rules(df)
    df = handle_missing_values(df)
    df = fix_data_types(df)
    df = apply_transformations(df)

    print("Final Shape:", df.shape)

    return df


