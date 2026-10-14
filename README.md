

\### 4. Prepare the database



Create and populate the local sample database:



```powershell

python -m src.database.create\_database

python -m src.database.seed\_database

```



\*\*Note:\*\* Run the seeding command on a fresh database. It clears existing sample records before inserting new ones.



\### 5. Start the application



```powershell

streamlit run app/streamlit\_app.py

```



Open the local URL displayed in your terminal.



The local Qwen model may download automatically on first use, depending on the model-loading configuration. An internet connection may be required for the initial download.



