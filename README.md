\# Local Text-to-SQL System



A privacy-focused Text-to-SQL application that converts natural-language questions into SQL queries and executes them against a local DuckDB database.



\## Features



\- Natural-language-to-SQL workflow

\- Local Qwen2.5-Coder model integration

\- Database schema retrieval for query context

\- SQL validation using SQLGlot

\- DuckDB for local query execution

\- Deterministic SQL fallback for supported query patterns

\- Streamlit interface for queries and result tables

\- CSV and SQL download options



\## Tech Stack



\- Python

\- Hugging Face Transformers

\- Qwen2.5-Coder

\- DuckDB

\- SQLGlot

\- Streamlit



\## Architecture



1\. User submits a natural-language question.

2\. The system retrieves relevant database schema information.

3\. The model or fallback logic generates SQL.

4\. SQLGlot validates the query.

5\. The query executes against DuckDB.

6\. Results are displayed in the Streamlit interface.



\## Run Locally



\### 1. Clone the repository



```bash

git clone https://github.com/YOUR\_USERNAME/local-text-to-sql.git

cd local-text-to-sql

```



\### 2. Create a virtual environment



```bash

python -m venv .venv

```



Activate it in Windows PowerShell:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



\### 3. Install dependencies



```bash

python -m pip install -r requirements.txt

```



\### 4. Prepare the database and model



Follow the project's database setup instructions and ensure the local model is available before running the application.



\### 5. Start the application



```bash

streamlit run app/streamlit\_app.py

```



Open the local URL displayed in your terminal.



\## Privacy



The application is designed for local execution. The database, environment variables, and virtual environment are excluded from version control. Model downloads may require an initial internet connection.



\## Current Limitations



Model output and fallback behavior depend on the supported query patterns and local environment. Validate generated SQL and results before using them for important decisions.



\## Future Improvements



\- Improve model-generated SQL reliability

\- Expand database schema retrieval

\- Add automated SQL evaluation

\- Improve error handling and query safety

\- Add reproducible sample-data setup



\## License



To be decided.



