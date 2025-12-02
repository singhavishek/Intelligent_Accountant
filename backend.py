import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from utils import get_dataframe_info, sanitize_code
import sys
import io

load_dotenv()

class FinancialAnalyst:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=self.api_key)
        self.model = "openai/gpt-oss-20b" # User requested model

    def analyze_query(self, query, data_info):
        """
        Determines if the query is ambiguous or if it can be answered with the data.
        """
        system_prompt = """You are an expert financial analyst assistant. 
        Your goal is to help users analyze their financial data (Profit & Loss, Balance Sheets).
        
        You have access to the schema and sample data of the uploaded files.
        
        Analyze the user's query.
        1. If the query is ambiguous or unclear, or if you need more context to select the right file/column, ask a clarifying question.
        2. If the query is clear and can be answered with the provided data, output "PROCEED".
        
        IMPORTANT: 
        - Do not be too pedantic. If the user asks for "Total Income" and there is a "Profit and Loss" sheet or a column with "Income", assume that is what they want.
        - NEVER ask "which file should I use?" if there is a file that clearly matches the intent (e.g. "Profit and Loss" for income/expenses, "Balance Sheet" for assets/liabilities). Just pick the most relevant one.
        - Only ask for clarification if the data is completely missing or if there is a genuine unresolvable conflict.
        - If the user asks about a specific company (e.g. "Sandbox Company") and the file is named "Sandbox Company...", PROCEED.
        
        Data Info:
        {data_info}
        
        Output ONLY the clarifying question OR "PROCEED".
        """
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt.format(data_info=data_info)},
                {"role": "user", "content": query}
            ],
            model=self.model,
            temperature=0,
        )
        return response.choices[0].message.content.strip()

    def generate_code(self, query, data_info):
        """
        Generates Python code to answer the query.
        """
        system_prompt = """You are a Python data analysis expert.
        You have been given a dictionary of pandas DataFrames called `dataframes`.
        The keys of the dictionary are filenames, and the values are dictionaries of {{sheet_name: dataframe}}.
        
        Structure of `dataframes`:
        {{
            "filename1.xlsx": {{
                "Sheet1": pd.DataFrame(...),
                "Sheet2": pd.DataFrame(...)
            }},
            ...
        }}
        
        Data Info (Schema & Samples):
        {data_info}
        
        User Query: {query}
        
        Write Python code to answer the query.
        - Assume `dataframes` is already loaded.
        - **File Selection**: You might have multiple files (e.g., a detailed one and a summary one). Look at the sample data. **If one file seems to contain mostly zeros and another has actual values, USE THE ONE WITH VALUES.**
        - **Column Identification**: 
            - Do NOT assume standard names.
            - **CRITICAL**: The amount column might be loaded as **text/object** because it contains strings like "Total" or currency symbols.
            - You MUST check object columns for numeric-looking values.
            - In the summary file, `Column_1` is likely the amount column (even if it's object type).
            - Convert the amount column to numeric: `df[col] = pd.to_numeric(df[col], errors='coerce')`.
        - **Hierarchical Data (Step-by-Step Algorithm)**: 
            1. **Search for Total Row**: Look for a row where the category column contains "**Total for Income**", "**Total Income**", "**Total for Assets**", or "**Total Assets**" (case insensitive).
            2. **Use Total Value**: If found, get the value from the amount column. 
                - **CRITICAL**: If there are multiple numeric columns (e.g. vendor-level data), the **LAST** numeric column is usually the Grand Total. Use that one.
                - **Return this value immediately.**
            3. **Sum Sub-items (Fallback)**: ONLY if no total row is found, sum the sub-items.
                - Find the "Income" or "Assets" header.
                - Sum rows *after* the header until you hit the *next* "Total" row or the end of the section.
                - **DO NOT** sum the entire file. You must stop at the end of the section.
        - **Robustness**: 
            - Initialize `result = "Could not calculate"` at the very beginning.
            - Define all helper variables (like `category_column`) before using them.
            - **CRITICAL**: Before using `.str.contains()`, ensure the column is string type: `df[col] = df[col].astype(str)`.
            - **CRITICAL**: Before summing ANY column, convert it to numeric: `df[col] = pd.to_numeric(df[col], errors='coerce')`. This handles empty strings and non-numeric characters.
            - **String Matching**: Use the following pattern: `df[col].str.contains('pattern', case=False, na=False)`. Do not repeat arguments.
            - Handle cases where a column might be strings (e.g. "$1,234.56"). You may need to clean it: `.replace('[\$,]', '', regex=True).astype(float)`.
        - You MUST create a variable named `result` that contains the final answer. (string, number, or dataframe).
        - If the answer is a DataFrame, `result` should be that DataFrame.
        - If the answer is a number or text, `result` should be that value.
        - Use pandas for data manipulation.
        - Handle potential missing values or data type issues if obvious from the sample.
        - Do NOT use `print()` to output the answer, assign it to `result`.
        - ONLY output the executable Python code. No markdown, no explanations.
        """
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt.format(data_info=data_info, query=query)},
                {"role": "user", "content": "Generate the code."}
            ],
            model=self.model,
            temperature=0,
        )
        return sanitize_code(response.choices[0].message.content)

    def execute_code(self, code, dataframes):
        """
        Executes the generated code in a restricted environment.
        """
        # Create a local scope with the dataframes
        local_scope = {"dataframes": dataframes, "pd": pd}
        
        try:
            # Redirect stdout to capture any prints (optional, but good for debugging)
            old_stdout = sys.stdout
            redirected_output = io.StringIO()
            sys.stdout = redirected_output
            
            # We pass local_scope as globals so that functions defined in the code
            # can access variables like 'pd' and 'dataframes'.
            exec(code, local_scope)
            
            sys.stdout = old_stdout
            
            if "result" in local_scope:
                return local_scope["result"], redirected_output.getvalue()
            else:
                return None, "Error: The code did not define a 'result' variable."
                
        except Exception as e:
            sys.stdout = old_stdout # Restore stdout just in case
            return None, f"Execution Error: {type(e).__name__}: {str(e)}"

    def explain_result(self, query, result, code):
        """
        Explains the result in natural language.
        """
        system_prompt = """You are a helpful accountant.
        The user asked: "{query}"
        
        We executed the following code:
        {code}
        
        And got this result:
        {result}
        
        Please explain this answer to the user in a clear, human-friendly way. 
        Explain HOW the answer was derived briefly.
        """
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt.format(query=query, code=code, result=str(result))},
                {"role": "user", "content": "Explain the answer."}
            ],
            model=self.model,
            temperature=0.5,
        )
        return response.choices[0].message.content
