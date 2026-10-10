from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.dataset import Dataset
from app.core.config import settings
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import re
from sqlalchemy import text

@tool
def analytics_tool(query: str):
    """
    Use this tool for data analysis, generating reports, calculating aggregations (SUM, AVG, COUNT),
    creating charts (bar, line, pie, histograms), or finding trends. It can analyze both the core company
    operational database (employees, departments, sales, projects, customers) and any
    uploaded tabular datasets (CSV/Excel).
    Input should be the specific analysis request.
    """
    db = SessionLocal()
    try:
        # 1. Identify all available data sources
        core_tables = ["employees", "departments", "sales", "projects", "customers"]
        uploaded_datasets = db.query(Dataset).all()

        all_sources = []
        for table in core_tables:
            all_sources.append({"name": table, "type": "core"})
        for ds in uploaded_datasets:
            all_sources.append({"name": ds.table_name, "type": "uploaded", "display_name": ds.name})

        if not all_sources:
            return "No data sources available for analysis."

        # 2. Get schemas for all candidate tables to provide context to the LLM
        engine = db.get_bind()
        full_schema_context = ""
        with engine.connect() as conn:
            for source in all_sources:
                table_name = source["name"]
                try:
                    res = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"))
                    cols = [f"{row[0]} ({row[1]})" for row in res]
                    if cols:
                        full_schema_context += f"\nTable: {table_name}\nColumns: {', '.join(cols)}\n"
                except Exception:
                    continue

        # 3. Use LLM to select the correct table and generate SQL & Plotting code
        from app.services.llm_service import llm
        from langchain_core.messages import HumanMessage

        prompt = f"""
        You are a professional data analyst. Answer the user's question by generating a PostgreSQL SQL query.
        If the user asks for a chart, graph, or visual trend, you MUST provide the Matplotlib Python code to plot it.
        You can use bar charts, line graphs, pie charts, histograms, or scatter plots as appropriate for the data.

        Available Tables and Schemas:
        {full_schema_context}

        User Question: {query}

        Return your response in the following format:
        TABLE: <the name of the table you chose>
        SQL: <your sql query>
        PLOT: <python code using matplotlib to plot df. Use 'df' as the variable name for the query results. Return only the code, no markdown. Include plt.title, plt.xlabel, and plt.ylabel for clarity.>
        NOTES: <short explanation of the result and insights found in the data>

        Important:
        - Ensure the SQL is valid PostgreSQL.
        - For plots, assume 'df' is a pandas DataFrame containing the result of the SQL query.
        - If no plot is needed, leave PLOT empty.
        """

        response = llm.invoke([HumanMessage(content=prompt)]).content

        # Robust parsing using regular expressions
        chosen_table = ""
        sql_query = ""
        plot_code = ""
        notes = ""

        table_match = re.search(r"TABLE:\s*(.*)", response, re.IGNORECASE)
        sql_match = re.search(r"SQL:\s*(.*)", response, re.IGNORECASE)
        plot_match = re.search(r"PLOT:\s*(.*)", response, re.IGNORECASE)
        notes_match = re.search(r"NOTES:\s*(.*)", response, re.IGNORECASE)

        if table_match: chosen_table = table_match.group(1).strip()
        if sql_match: sql_query = sql_match.group(1).strip()
        if plot_match: plot_code = plot_match.group(1).strip()
        if notes_match: notes = notes_match.group(1).strip()

        # Handle multi-line blocks for SQL and PLOT
        # If the LLM returned a block instead of a single line, we find the content between keywords
        if not sql_query or not plot_code:
            # Extract everything between SQL: and PLOT: as the SQL query
            sql_block = re.search(r"SQL:(.*?)PLOT:", response, re.DOTALL | re.IGNORECASE)
            if sql_block:
                sql_query = sql_block.group(1).strip()

            # Extract everything between PLOT: and NOTES: as the plot code
            plot_block = re.search(r"PLOT:(.*?)NOTES:", response, re.DOTALL | re.IGNORECASE)
            if plot_block:
                plot_code = plot_block.group(1).strip()

        if not sql_query:
            return f"Could not generate a valid SQL query for this request. LLM response was: {response}"

        # 4. Execute the SQL query
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]

        if not rows:
            return "The query executed successfully but returned no data."

        df_result = pd.DataFrame(rows)

        # 5. Generate Chart if requested
        chart_base64 = None
        if plot_code:
            try:
                plt.figure(figsize=(10, 6))
                # Execute the plot code in a controlled environment
                local_vars = {"df": df_result, "plt": plt, "pd": pd}
                exec(plot_code, {}, local_vars)

                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                plt.close()
            except Exception as e:
                notes += f" | Chart generation failed: {str(e)}"

        # Try to find a display name for the table if it's an uploaded dataset
        display_name = chosen_table
        for s in all_sources:
            if s["name"] == chosen_table and "display_name" in s:
                display_name = s["display_name"]

        return {
            "dataset_used": display_name,
            "sql_executed": sql_query,
            "analysis_result": df_result.to_string(index=False),
            "notes": notes,
            "chart": chart_base64
        }

    except Exception as e:
        return f"An error occurred during analysis: {str(e)}"
    finally:
        db.close()
