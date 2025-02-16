from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

load_dotenv() 

gigachat_token = os.getenv("GIGACHAT_TOKEN")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def save_to_database(context, question, answer, result):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Insert data into table
        insert_query = sql.SQL("""
            INSERT INTO hallucination_evaluations (context, question, answer, result)
            VALUES (%s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (context, question, answer, result))

        # Commit changes and close connection
        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved successfully!")

    except Exception as e:
        print(f"Error saving to database: {e}")

giga = GigaChat (
    credentials=gigachat_token,
    model="GigaChat-Max",
    scope="GIGACHAT_API_CORP",
    verify_ssl_certs=False
)

prompt = PromptTemplate(
    input_variables=["context", "description"],
    template="""
    A hallucination occurs if the DESCRIPTION includes information not grounded in the CONTEXT.

    Definition:
    - The DESCRIPTION is hallucinated if it contradicts the CONTEXT, adds unsupported claims, introduces fabricated,  untrue details.
    - The DESCRIPTION is faithful if it strictly adheres to the facts in the CONTEXT.

    Instructions:
    - Respond ONLY "true" if the DESCRIPTION contains hallucinations.
    - Respond ONLY "false" if the DESCRIPTION is grounded and accurate.

    CONTEXT:

    =====
    {context}
    =====

    DESCRIPTION:

    =====
    {description}
    =====
"""
)


llm_chain = LLMChain(llm=giga, prompt=prompt)

def evaluate_hallucinations_artworkinfo(context, answer):
    result = llm_chain.run({"context": context, "description": answer})
    question = "Опиши картину"
    save_to_database(context, question, answer, result)
    
    return result
