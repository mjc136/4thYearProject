from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
if not connection_string:
    print("Error: Connection string not found!")
else:
    print(f"Connection String Loaded: {connection_string}")
