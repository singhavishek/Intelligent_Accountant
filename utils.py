import pandas as pd
import io

def load_excel_file(uploaded_file):
    """
    Loads an Excel file into a dictionary of DataFrames, one for each sheet.
    Attempts to find the correct header row.
    """
    try:
        # Read all sheets
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        dataframes = {}
        for sheet in sheet_names:
            # Read first few rows to find header
            df_preview = pd.read_excel(uploaded_file, sheet_name=sheet, header=None, nrows=20)
            
            header_row_idx = 0
            # Simple heuristic: find first row with at least 3 non-null values
            for i, row in df_preview.iterrows():
                if row.count() >= 3:
                    header_row_idx = i
                    break
            
            # Reload with correct header
            df = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_row_idx)
            
            # Clean up column names (strip whitespace, handle Unnamed)
            df.columns = [str(c).strip() if not str(c).startswith("Unnamed") else f"Column_{i}" for i, c in enumerate(df.columns)]
            
            dataframes[sheet] = df
        return dataframes
    except Exception as e:
        return {"error": str(e)}

def get_dataframe_info(dataframes):
    """
    Generates a string summary of the loaded DataFrames for the LLM.
    """
    info_str = ""
    for filename, sheets in dataframes.items():
        info_str += f"\nFile: {filename}\n"
        for sheet_name, df in sheets.items():
            info_str += f"  Sheet: {sheet_name}\n"
            info_str += f"  Columns: {list(df.columns)}\n"
            info_str += f"  Shape: {df.shape}\n"
            info_str += f"  Sample Data (first 15 rows):\n{df.head(15).to_string()}\n"
            info_str += "-" * 30 + "\n"
    return info_str

def sanitize_code(code_str):
    """
    Strips markdown code blocks from the generated code.
    """
    code_str = code_str.strip()
    if code_str.startswith("```python"):
        code_str = code_str[9:]
    elif code_str.startswith("```"):
        code_str = code_str[3:]
    
    if code_str.endswith("```"):
        code_str = code_str[:-3]
    
    return code_str.strip()
