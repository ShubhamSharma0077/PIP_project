import streamlit as st      
import pandas as pd           
import numpy as np             
import plotly.express as px    
import streamlit as st      
import pandas as pd           
import numpy as np               
from pathlib import Path  


def load_dashboard():







    # ==========================
    # Page Config
    # ==========================
    st.set_page_config(
        page_title="📊 Employee Engagement Dashboard",
        page_icon="📊",
        layout="wide"
    )



    
    ############
    # For Matplotlib charts
    img_size = (6, 4)  # Width, Height in inches
    fontsize_title = int(min(img_size) * 2.5)  # Title font size relative to chart size
    fontsize_x = 12  # X and Y axis labels
    fontsize_y=12

    # For Plotly charts
    h = 500  # height in pixels
    w = 800  # width in pixels
    title_size = int(min(h, w) * 0.05)  # Title font size relative to chart size
    axis_size = int(min(h, w) * 0.03)   # Axis label size
    legend_size = int(min(h, w) * 0.025)  # Legend font size


    # ==========================
    # Load Dataset
    # ==========================
    # Replace with your CSV path
    df = pd.read_csv("./Synthetic_Data/synthetic_employee_feedback.csv", parse_dates=['survey_date'])

    # ==========================
    # Sidebar Filters
    # ==========================
    st.sidebar.header("Filters")

    departments = st.sidebar.multiselect(
        "Select Departments:",
        options=df['department'].unique(),
        default=df['department'].unique()
    )



    st.sidebar.header("Filters")


    min_date = df['survey_date'].min().date()
    max_date = df['survey_date'].max().date()

    # Slider returns a tuple of start and end dates

    start_date, end_date = st.sidebar.slider(
        "Select Survey Date Range:",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="DD/MM/YYYY"
    )

    date_range=[start_date,end_date]


    CHAINLIT_URL = "http://localhost:8000"

    st.sidebar.markdown("## 🤖 AI Assistant")
    st.sidebar.link_button("💬 Chainlit AI Chat Bot", CHAINLIT_URL)


    ######################################
    filtered_df = df[
        (df['department'].isin(departments)) &
        (df['survey_date'] >= pd.to_datetime(date_range[0])) &
        (df['survey_date'] <= pd.to_datetime(date_range[1]))
    ]


    # ==========================
    # Dashboard KPIs
    # ==========================
    st.title("📊 Employee Engagement & Performance Dashboard")
    st.markdown("Explore employee engagement, performance, tenure and feedback insights interactively.")

    avg_engagement = filtered_df['engagement_score'].mean()
    avg_tenure = filtered_df['tenure_years'].mean()
    high_perf_count = filtered_df[filtered_df['performance_rating'] >= 4].shape[0]
    low_perf_count = filtered_df[filtered_df['performance_rating'] <= 2].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Engagement", f"{avg_engagement:.1f}")
    col2.metric("Avg Tenure (Years)", f"{avg_tenure:.1f}")
    col3.metric("High Performers (4-5)", high_perf_count)
    col4.metric("Low Performers (1-2)", low_perf_count)

    st.markdown("---")


    # ==========================
    #1) Average Engagement by Department 
    # ==========================
    st.subheader("1️⃣ Average Engagement by Department")
    st.markdown("This chart shows the average engagement score for each department. Departments with lower scores may require HR attention.")

    # Compute average engagement
    avg_eng = filtered_df.groupby("department")["engagement_score"].mean().sort_values()


    fig = px.bar(
        avg_eng.reset_index(),  # Convert Series to DataFrame
        x="department",
        y="engagement_score",
        text=avg_eng.values,  # Show data labels on top of bars
        color="engagement_score",
        color_continuous_scale="Viridis",
        labels={"department": "Department", "engagement_score": "Engagement Score"},
    )

    # Update layout and styling
    fig.update_traces(
        texttemplate="%{text:.1f}",  # format text labels
        textposition="outside",
        marker_line_color="#417d6b",
        marker_line_width=1.5,
    )

    fig.update_layout(
        # title="Average Engagement Score by Department",
        # title_font_size=int(min(h, w) * 0.05),  # dynamic title size
        # title_font_family="Arial",
        xaxis_title="Department",
        yaxis_title="Engagement Score",
        xaxis_tickangle=-45,
        yaxis=dict(range=[0, max(avg_eng.values)*1.2], showgrid=True, gridcolor="lightgray"),
        template="plotly_white",
        height=h,
        width=w,
        font=dict(size=axis_size)
    )

    # Render in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    # Insights in expander
    with st.expander("💡 Insights"):
        st.markdown(f"- **Finance** has the lowest engagement score at 48.2.")
        st.markdown(f"- **Sales**, **Engineering**, and **Marketing** have the highest engagement, with Marketing leading at 56.3.")
        st.markdown("- Overall, engagement differences are moderate, but Finance may need targeted initiatives to improve employee engagement.")

    st.markdown("---")


    # ============================================================
    # 2. PERFORMANCE RATING DISTRIBUTION
    # ============================================================


    st.subheader("2️⃣ Performance Rating Distribution")
    st.markdown("This chart visualizes the distribution of performance ratings across all employees. It helps identify whether ratings are balanced or skewed toward certain levels.")

    # Compute histogram data
    perf_counts, perf_bins = np.histogram(filtered_df['performance_rating'], bins=5)
    perf_labels = [f"{int(perf_bins[i])}-{int(perf_bins[i+1])}" for i in range(len(perf_bins)-1)]

    # Create DataFrame for Plotly
    perf_df = pd.DataFrame({
        "Performance Rating": perf_labels,
        "Count": perf_counts
    })

    # Plotly Express bar chart
    fig = px.bar(
        perf_df,
        x="Performance Rating",
        y="Count",
        text="Count",  # show counts on top
        color="Count",
        color_continuous_scale="Oranges",
        labels={"Count": "Number of Employees"},
    )

    # Update traces and layout
    fig.update_traces(
        texttemplate="%{text}",  # show count on top
        textposition="outside",
        marker_line_color="#e76f51",
        marker_line_width=1.5
    )

    fig.update_layout(
        # title="Distribution of Performance Ratings",
        # title_font_size=int(min(h, w) * 0.05),
        # title_font_family="Arial",
        xaxis_title="Performance Rating",
        yaxis_title="Number of Employees",
        yaxis=dict(range=[0, max(perf_counts)*1.2], showgrid=True, gridcolor="lightgray"),
        template="plotly_white",
        height=h,
        width=w,
        font=dict(size=axis_size)
    )

    # Render in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Insights in expander

    with st.expander("💡 Insights"):
        st.markdown("- Overall, performance ratings are fairly **well-distributed**, with the largest number of employees in the mid-range (2.6-3.4).")
        st.markdown("- No major bias toward extremely low or high ratings, indicating balanced evaluation across departments.")
        st.markdown("- Can be correlated with engagement scores for identifying high performers with low engagement or low performers with high engagement.")

    st.markdown("---")


    # ============================================================
    # 3. TENURE VS ENGAGEMENT
    # ============================================================

    st.subheader("3️⃣ Tenure vs Engagement")
    st.markdown("This scatter plot shows the relationship between employee tenure and engagement. It helps identify trends and groups that may need attention.")



    fig = px.scatter(
        filtered_df,
        x="tenure_years",
        y="engagement_score",
        color="department",
        hover_data=["employee_id", "performance_rating", "engagement_score"],
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"tenure_years":"Tenure (Years)", "engagement_score":"Engagement Score"},
        trendline="ols"  # Adds linear regression trend line
    )

    fig.update_layout(
        # title="Employee Tenure vs Engagement",
        xaxis_title="Tenure (Years)",
        yaxis_title="Engagement Score",
        # title_font_size=title_size,
        legend_title_text="Department",
        template="plotly_white",
        height=h, 
        width=w
    )

    st.plotly_chart(fig, use_container_width=True)

    # Insights in expander
    with st.expander("💡 Insights"):
        st.markdown("- Employees with ** less tenure ** show slightly lower engagement compared to middle or long-tenure employees.")
        st.markdown("- Engagement generally **increases with tenure**, indicating that experienced employees are more engaged.")
        st.markdown("- Identify less-tenure employees for targeted engagement initiatives to retain talent.")





    # ============================================================
    # 4. FEEDBACK COUNT BY DEPARTMENT
    # ============================================================
    st.subheader("4️⃣ Feedback Count by Department")
    st.markdown(
        "This chart shows the number of feedback entries submitted by employees in each department. "
        "It helps identify departments with high engagement or possible dissatisfaction."
        "Departments with higher feedback may reflect either **high engagement** or **dissatisfaction**; cross-reference with engagement scores for clarity."
    )

    # Prepare data
    feedback_count_df = filtered_df['department'].value_counts().reset_index()
    feedback_count_df.columns = ['department', 'feedback_count']

    # Create interactive bar chart with Plotly

    fig = px.bar(
        feedback_count_df,
        x='department',
        y='feedback_count',
        text='feedback_count',
        color='feedback_count',
        color_continuous_scale='Viridis',
        labels={'department':'Department', 'feedback_count':'Feedback Count'},
        hover_data=['feedback_count']
    )

    fig.update_layout(
        # title="Feedback Count by Department",
        xaxis_title="Department",
        yaxis_title="Number of Feedback Entries",
        template="plotly_white",
        # title_font_size=title_size,
        height=h, 
        width=w
    )

    # Highlight top and bottom departments
    max_feedback = feedback_count_df['feedback_count'].max()
    min_feedback = feedback_count_df['feedback_count'].min()
    max_dept = feedback_count_df.loc[feedback_count_df['feedback_count'] == max_feedback, 'department'].values[0]
    min_dept = feedback_count_df.loc[feedback_count_df['feedback_count'] == min_feedback, 'department'].values[0]

    fig.add_annotation(
        x=max_dept,
        y=max_feedback,
        text="Highest Feedback",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        ax=0,
        ay=-40
    )

    fig.add_annotation(
        x=min_dept,
        y=min_feedback,
        text="Lowest Feedback",
        showarrow=True,
        arrowhead=2,
        arrowcolor="green",
        ax=0,
        ay=40
    )

    # Show chart
    st.plotly_chart(fig, use_container_width=True)

    # Professional Insights
    with st.expander("💡 Insights"):
        st.markdown(f"- **Sales** has the highest feedback count ({max_feedback}), indicating active participation or possible workload concerns.")
        st.markdown(f"- **Marketing** has the lowest feedback ({min_feedback}), may indicate less engagement or fewer feedback submissions.")
        st.markdown("- HR and Finance have moderate feedback counts, suggesting balanced engagement.")
        st.markdown("- Use this information to **prioritize HR initiatives** and identify departments needing closer attention.")



    # ============================================================
    # 5. ENGAGEMENT TREND OVER TIME
    # ============================================================


    st.subheader("5️⃣ Engagement Trend Over Time")
    st.markdown(
        "This chart shows how average engagement scores change over survey dates. "
        "It helps detect periods of improvement or potential concern in employee engagement."
    )

    # Prepare data
    trend_df = filtered_df.groupby("survey_date")["engagement_score"].mean().reset_index()
    trend_df = trend_df.sort_values("survey_date")

    # Create interactive line chart

    fig = px.line(
        trend_df,
        x="survey_date",
        y="engagement_score",
        markers=True,
        labels={"survey_date":"Survey Date", "engagement_score":"Avg Engagement Score"},
        # title="Average Engagement Trend Over Time",
        hover_data={"survey_date":True, "engagement_score":":.2f"}
    )

    # Highlight max and min points
    max_eng = trend_df['engagement_score'].max()
    min_eng = trend_df['engagement_score'].min()
    max_date = trend_df.loc[trend_df['engagement_score'] == max_eng, 'survey_date'].values[0]
    min_date = trend_df.loc[trend_df['engagement_score'] == min_eng, 'survey_date'].values[0]

    fig.add_annotation(
        x=max_date,
        y=max_eng,
        text=f"Peak ({max_eng:.1f})",
        showarrow=True,
        arrowhead=2,
        arrowcolor="green",
        ax=0,
        ay=-40
    )

    fig.add_annotation(
        x=min_date,
        y=min_eng,
        text=f"Lowest ({min_eng:.1f})",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        ax=0,
        ay=40
    )

    # Update layout for professional look
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Survey Date",
        yaxis_title="Average Engagement Score",
        # title_font_size=title_size,
        height=h, 
        width=w
    )

    # Show chart
    st.plotly_chart(fig, use_container_width=True)

    # Professional Insights
    with st.expander("💡 Insights"):
        st.markdown("- **2019 → 2020:** Engagement score jumped from 25 → 61.6, indicating major improvements or successful interventions.")
        st.markdown("- **2020 → 2022:** Engagement slightly increased from 61.6 → 62.6, showing a plateau; initial gains are sustained.")
        st.markdown("- **No drop observed**, which is positive; employees are maintaining engagement.")










    # ============================================================
    # 6. TENURE GROUP ANALYSIS
    # ============================================================



    st.subheader("6️⃣ Engagement by Tenure Group")
    st.markdown(
        "This chart shows average engagement scores by employee tenure groups. "
        "It helps identify which tenure segments are most engaged."
    )

    # Create tenure groups
    filtered_df["tenure_group"] = pd.cut(
        filtered_df["tenure_years"],
        bins=[-1, 2, 4, 8],
        labels=["Early", "Mid", "Experienced"]
    )

    # Calculate average engagement by tenure group
    tenure_analysis = filtered_df.groupby("tenure_group")["engagement_score"].mean().reset_index()

    # Create professional interactive bar chart
    fig = px.bar(
        tenure_analysis,
        x="tenure_group",
        y="engagement_score",
        color="engagement_score",
        text="engagement_score",
        color_continuous_scale="Viridis",
        labels={"tenure_group": "Tenure Group", "engagement_score": "Average Engagement Score"},
        # title="Average Engagement Score by Tenure Group"
    )

    # Layout adjustments for professional look
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Tenure Group",
        yaxis_title="Avg Engagement Score",
        # title_font_size=title_size,
        height=h, 
        width=w
    )

    # Display chart
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("💡 Insights"):
        st.markdown(f"- **Early (0-2 yrs):** Avg engagement = 47.3 → New employees may need onboarding support and engagement initiatives.")
        st.markdown(f"- **Mid (2-4 yrs):** Avg engagement = 61.3 → Engagement improves, but still room for growth.")
        st.markdown(f"- **Experienced (4-8 yrs):** Avg engagement = 67.1 → Highly engaged group, retention strategies are effective.")
        st.markdown("- Engagement clearly **increases with tenure**.")
        st.markdown("- Focus on **Early and Mid-tenure employees** to accelerate engagement growth through mentoring, recognition, and training programs.")




    # ============================================================
    # 7. LOW ENGAGEMENT ANALYSIS
    # ============================================================


    st.subheader("7️⃣ Low Engagement Employees by Department")
    st.markdown(
        "This chart identifies departments with employees having **engagement scores below 60**. "
        "It helps HR prioritize interventions for teams at risk."
    )

    # Low engagement data (your actual data)

    low_eng = df[df["engagement_score"] < 60]
    low_eng_data = low_eng["department"].value_counts()
    low_eng_df = low_eng_data.reset_index()
    low_eng_df.columns = ["department", "count"]

    # Professional interactive bar chart
    fig = px.bar(
        low_eng_df,
        x="department",
        y="count",
        color="count",
        text="count",
        color_continuous_scale="Reds",
        labels={"department": "Department", "count": "Number of Low Engagement Employees"},
        # title="Number of Low Engagement Employees by Department"
    )

    # Layout adjustments for professional look
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Department",
        yaxis_title="Count of Low Engagement Employees",
        # title_font_size=title_size,
        height=h, 
        width=w
    )

    # Display chart
    st.plotly_chart(fig, use_container_width=True)

    # Insights panel
    with st.expander("💡 Insights"):
        st.markdown("- **Sales** has the highest number of low-engagement employees (54), indicating **attrition risk**.")
        st.markdown("- **Engineering** and **Finance** also have significant low-engagement counts (48 and 43).")
        st.markdown("- **HR** and **Marketing** have lower low-engagement numbers, showing relatively better engagement.")
        st.markdown("- HR can use this analysis to **prioritize interventions**, mentoring, and recognition programs for departments at risk.")








    st.subheader("8️⃣ Correlation Analysis")
    st.markdown(
        "This heatmap shows correlations between key numerical variables: **Tenure**, **Performance Rating**, and **Engagement Score**. "
        "It helps identify patterns and relationships in employee metrics."
    )

    # Calculate correlation
    corr = filtered_df[["tenure_years", "performance_rating", "engagement_score"]].corr()

    # Plotly heatmap
    fig = px.imshow(
        corr,
        text_auto=".2f",  # show correlation values on cells
        color_continuous_scale="RdBu_r",  # red-blue diverging
        origin="upper",
        aspect="auto",
        labels=dict(x="Metrics", y="Metrics", color="Correlation")
    )

    # Update layout for professional look
    fig.update_layout(
        # title="Correlation Matrix",
        # title_font_size=int(min(h, w) * 0.05),
        template="plotly_white",
        height=h,
        width=w,
    )

    # Adjust text size on cells
    fig.update_xaxes(tickfont_size=axis_size)
    fig.update_yaxes(tickfont_size=axis_size)

    # Render in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("💡 Insights"):
        st.markdown("- **Performance vs Engagement (0.633):** Moderate positive correlation → higher engagement aligns with higher performance. HR can target low-engagement employees to boost performance.")
        st.markdown("- **Tenure vs Engagement (0.435):** Moderate positive correlation → engagement tends to improve with tenure, but mid-tenure employees may need support.")
        st.markdown("- **Tenure vs Performance (0.035):** Almost no correlation → performance is independent of tenure. New employees can perform well if engaged.")
        st.markdown("- **Actionable:** Focus on engagement programs, especially for mid-tenure employees, to maximize performance across departments.")






    ###############################################################################################################################
    ################################################################################################################################



    # import streamlit as st
    # from pathlib import Path
    # import pandas as pd

    # # -----------------------------
    # # CONFIG
    # # -----------------------------

    # REPORT_FILE = Path(r"orchestrator_workflow_insights\final_hr_report.txt")  # your backend report file


    # # -----------------------------
    # # READ DATA FROM TXT
    # # -----------------------------
    # def read_report(file_path: Path) -> str:
    #     if not file_path.exists():
    #         return "Report file not found."
    #     return file_path.read_text(encoding="utf-8")


    # report_text = read_report(REPORT_FILE)


    # # -----------------------------
    # # DASHBOARD HEADER
    # # -----------------------------
    # st.title("HR Feedback & Insights Dashboard")
    # st.markdown(
    #     """
    # This dashboard presents **executive-level insights** on employee feedback, sentiment trends, 
    # engagement, attrition risk, and actionable recommendations. Data is refreshed from backend outputs.
    # """
    # )

    # st.markdown("---")


    # # -----------------------------
    # # EXECUTIVE SUMMARY
    # # -----------------------------
    # st.header("Executive Summary")
    # summary_start = report_text.find("### Executive Summary")
    # summary_end = report_text.find("---", summary_start)
    # executive_summary = report_text[summary_start:summary_end].replace("### Executive Summary", "")
    # st.info(executive_summary.strip())


    # # -----------------------------
    # # SENTIMENT BY DEPARTMENT
    # # -----------------------------
    # st.header("Sentiment by Department")
    # sentiment_start = report_text.find("### 1. Sentiment by Department")
    # sentiment_end = report_text.find("---", sentiment_start)
    # sentiment_text = report_text[sentiment_start:sentiment_end].replace("### 1. Sentiment by Department", "")
    # st.markdown(sentiment_text.strip())


    # # -----------------------------
    # # CORE FEEDBACK THEMES (TABLE)
    # # -----------------------------
    # st.header("Core Feedback Themes")
    # themes_start = report_text.find("### 2. Core Feedback Themes")
    # themes_end = report_text.find("---", themes_start)
    # themes_text = report_text[themes_start:themes_end].splitlines()[2:]  # skip header

    # # Parse table from markdown manually
    # table_lines = [line for line in themes_text if "|" in line]
    # if table_lines:
    #     table_data = [line.strip().split("|")[1:-1] for line in table_lines[2:]]  # skip header separator
    #     df_themes = pd.DataFrame(table_data, columns=["Theme", "Mentions", "Key Insight"])
    #     st.dataframe(df_themes)


    # # -----------------------------
    # # OTHER SECTIONS
    # # -----------------------------
    # sections = {
    #     "Tenure & Engagement Dynamics": "### 3. Tenure & Engagement Dynamics",
    #     "Performance Rating Correlation": "### 4. Performance Rating Correlation",
    #     "Early Attrition Risk": "### 5. Early Attrition Risk",
    #     "Career-Growth Sentiment": "### 6. Career‑Growth Sentiment Split",
    #     "Work-Life Balance Findings": "### 7. Work‑Life Balance Specific Findings",
    #     "Low-Engagement Culture Concerns": "### 8. Low‑Engagement Culture Concerns",
    #     "Department-Level Action Plan": "### 9. Department‑Level Action Plan",
    #     "Consolidated Recommendations": "### 10. Consolidated Recommendations",
    #     "Conclusion": "**Conclusion**"
    # }

    # for title, marker in sections.items():
    #     st.header(title)
    #     start = report_text.find(marker)
    #     if start == -1:
    #         continue
    #     # end at next ---
    #     end = report_text.find("---", start)
    #     section_text = report_text[start:end].replace(marker, "")
        
    #     # Show table differently if it's Q9 Department-Level Action Plan
    #     if "Department‑Level Action Plan" in title:
    #         table_lines = [line for line in section_text.splitlines() if "|" in line]
    #         if table_lines:
    #             table_data = [line.strip().split("|")[1:-1] for line in table_lines[2:]]  # skip header separator
    #             df_action_plan = pd.DataFrame(table_data, columns=["Department", "Initiative", "Owner", "Deadline"])
    #             st.dataframe(df_action_plan)
    #         else:
    #             st.markdown(section_text.strip())
    #     else:
    #         st.markdown(section_text.strip())


    # # -----------------------------
    # # OPTIONAL: Download Report
    # # -----------------------------
    # st.markdown("---")
    # st.download_button(
    #     label="Download Full Report",
    #     data=report_text,
    #     file_name="final_hr_report.txt",
    #     mime="text/plain"
    # )




    ######################################################################################################################



    # -----------------------------
    # BACKEND REPORT FILE
    # -----------------------------
    # REPORT_FILE = Path(r"orchestrator_workflow_insights\final_hr_report.txt")
    REPORT_FILE = Path("orchestrator_workflow_insights/final_hr_report.txt") 

    # -----------------------------
    # READ REPORT
    # -----------------------------
    if REPORT_FILE.exists():
        report_text = REPORT_FILE.read_text(encoding="utf-8")
    else:
        report_text = "Report file not found."

    # -----------------------------
    # DISPLAY IN FRONTEND
    # -----------------------------
    st.title("AI-Generated HR Report")

    st.markdown("---")
    st.markdown(report_text)
