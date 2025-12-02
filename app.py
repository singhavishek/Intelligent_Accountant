import streamlit as st
import pandas as pd
import os
from backend import FinancialAnalyst
from utils import load_excel_file, get_dataframe_info

# Page config
st.set_page_config(page_title="Intelligent Accountant", page_icon="💰", layout="wide")

# Title and Description
st.title("💰 Intelligent Accountant Chatbot")
st.markdown("""
Upload your financial documents (Profit & Loss, Balance Sheet) and ask questions.
I can analyze the data, perform calculations, and explain the results.
""")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

if "analyst" not in st.session_state:
    try:
        st.session_state.analyst = FinancialAnalyst()
    except Exception as e:
        st.error(f"Error initializing Financial Analyst: {e}")
        st.stop()

# Sidebar for File Upload
with st.sidebar:
    st.header("📂 Data Source")
    
    with st.expander("❓ Sample Questions"):
        st.markdown("""
        **Easy:**
        - How much cash do we have on hand?
        
        **Medium:**
        - How much is total undeposit funds?
        
        **Hard:**
        - What are the biggest risks you see in the expenses?
        """)
    
    # Auto-load from Data folder
    data_dir = "Data"
    auto_files = []
    if os.path.exists(data_dir):
        auto_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".xlsx")]
    
    st.write(f"Found {len(auto_files)} files in '{data_dir}' folder.")
    
    # Manual Upload
    uploaded_files = st.file_uploader("Add more Excel files (.xlsx)", type=["xlsx"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Process Uploaded Files"):
            with st.spinner("Processing uploaded files..."):
                for file in uploaded_files:
                    dfs = load_excel_file(file)
                    if "error" in dfs:
                        st.error(f"Error loading {file.name}: {dfs['error']}")
                    else:
                        st.session_state.dataframes[file.name] = dfs
                st.success(f"Added {len(uploaded_files)} files!")

# Auto-load logic (run once if dataframes is empty)
if not st.session_state.dataframes and auto_files:
    with st.spinner("Auto-loading files from Data folder..."):
        for file_path in auto_files:
            dfs = load_excel_file(file_path)
            if "error" in dfs:
                st.error(f"Error loading {os.path.basename(file_path)}: {dfs['error']}")
            else:
                st.session_state.dataframes[os.path.basename(file_path)] = dfs
        st.success(f"Auto-loaded {len(st.session_state.dataframes)} files!")
                
    # Show loaded data summary
    if st.session_state.dataframes:
        st.subheader("Loaded Data")
        for filename, sheets in st.session_state.dataframes.items():
            with st.expander(filename):
                for sheet_name, df in sheets.items():
                    st.write(f"**{sheet_name}**")
                    st.dataframe(df.head(3))

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask a question about your financial data..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check if data is loaded
    if not st.session_state.dataframes:
        response = "Please upload some financial data first so I can answer your question."
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # 1. Get Data Info
                    data_info = get_dataframe_info(st.session_state.dataframes)
                    
                    # 2. Analyze Query (Ambiguity Check)
                    analysis = st.session_state.analyst.analyze_query(prompt, data_info)
                    
                    if analysis != "PROCEED":
                        # Ambiguous or needs clarification
                        response = analysis
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        # 3. Generate Code
                        code = st.session_state.analyst.generate_code(prompt, data_info)
                        
                        # Show code in expander for transparency
                        with st.expander("Generated Code"):
                            st.code(code, language="python")
                        
                        # 4. Execute Code
                        result, output = st.session_state.analyst.execute_code(code, st.session_state.dataframes)
                        
                        if result is None:
                            response = f"I encountered an error while calculating the answer:\n{output}"
                            st.error(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        else:
                            # 5. Explain Result
                            explanation = st.session_state.analyst.explain_result(prompt, result, code)
                            st.markdown(explanation)
                            st.session_state.messages.append({"role": "assistant", "content": explanation})
                            
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
