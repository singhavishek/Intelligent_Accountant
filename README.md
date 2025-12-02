# 💰 Intelligent Accountant Chatbot

An AI-powered financial assistant that analyzes your Excel financial documents (Profit & Loss, Balance Sheet) to answer questions, perform calculations, and provide insights.

## 🚀 Features

- ** automated Data Loading**: Automatically detects and loads Excel files from the `Data/` directory on startup.
- **Intelligent Analysis**: Uses **Groq (openai/gpt-oss-20b)** to understand complex financial queries.
- **Code Generation & Execution**: Dynamically generates Python/Pandas code to perform accurate calculations on your data.
- **Robust Handling**:
    - Handles varying Excel layouts (summary vs. detailed, different header rows).
    - Smartly identifies "Total" rows (e.g., "Total for Income", "Total Assets").
    - Prioritizes files with actual data over empty templates.
- **Interactive UI**: Built with Streamlit for a clean, chat-based user experience.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **LLM**: Groq API (`openai/gpt-oss-20b`)
- **Data Processing**: Pandas, OpenPyXL

## ⚙️ Setup & Installation

1.  **Clone the repository** (or navigate to the project folder).

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Key**:
    - Create a `.env` file in the root directory.
    - Add your Groq API key:
      ```env
      GROQ_API_KEY=your_groq_api_key_here
      ```

## 🏃‍♂️ Usage

1.  **Run the application**:
    ```bash
    streamlit run app.py
    ```

2.  **Interact**:
    - The app will automatically load any Excel files found in the `Data/` folder.
    - You can also upload additional files via the sidebar.
    - Type your question in the chat input (e.g., "What is the total income?").

## ❓ Sample Questions

**Easy**
- How much cash do we have on hand?

**Medium**
- How much is total undeposit funds?

**Hard**
- What are the biggest risks you see in the expenses?

## 📂 Project Structure

- `app.py`: Main Streamlit application (UI and interaction logic).
- `backend.py`: Core logic for LLM interaction, code generation, and execution.
- `utils.py`: Helper functions for loading and processing Excel files.
- `Data/`: Directory for storing financial Excel files (auto-loaded).
- `requirements.txt`: Python dependencies.