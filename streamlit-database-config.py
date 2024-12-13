# File: database_config.py
import os
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd

# Load environment variables
load_dotenv()

def get_snowflake_connection():
    """
    Establish a connection to Snowflake using environment variables
    """
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )
    return conn

def execute_query(query):
    """
    Execute a SQL query and return results as a pandas DataFrame
    """
    conn = get_snowflake_connection()
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()
