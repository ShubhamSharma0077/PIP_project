import pandas as pd
from Synthetic_Data import Synthetic_data_generation_first,Synthetic_data_generation_column_feedback_comment,Synthetic_data_generation_get_feedback_details


df=Synthetic_data_generation_first()

df=Synthetic_data_generation_column_feedback_comment(df)

# df.to_csv(r"Synthetic_Data\synthetic_employee_feedback.csv", index=False)

#######################################################################################

df=pd.read_csv("Synthetic_Data\synthetic_employee_feedback.csv")

df=Synthetic_data_generation_get_feedback_details(df)

# df.to_csv(r"Synthetic_Data\feedback_sentiment_analysis.csv", index=False)






