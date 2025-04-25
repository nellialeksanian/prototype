from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

from sql.create_tables import save_to_database

load_dotenv() 

gigachat_token = os.getenv("GIGACHAT_TOKEN")

giga = GigaChat (
    credentials=gigachat_token,
    model="GigaChat-Max",
    scope="GIGACHAT_API_CORP",
    verify_ssl_certs=False
)

prompt = PromptTemplate(
    input_variables=["context", "question", "answer"],
    template="""
    A hallucination occurs if the ANSWER includes information not grounded in the CONTEXT or does not directly and accurately address the QUESTION.

    Definition:
    - The ANSWER is hallucinated if it contradicts the CONTEXT, adds unsupported claims, introduces fabricated, untrue details, or fails to correctly address the QUESTION.
    - The ANSWER is faithful if it strictly adheres to the facts in the CONTEXT and:
        1. Accurately responds to the QUESTION using the provided CONTEXT, OR
        2. Clearly states that it cannot answer the QUESTION because the CONTEXT does not contain relevant information.

    Instructions:
    - Respond ONLY "true" if the ANSWER contains hallucinations.
    - Respond ONLY "false" if the ANSWER is grounded, accurate, and appropriately addresses the QUESTION.

    CONTEXT:

    =====
    {context}
    =====

    QUESTION:

    =====
    {question}
    =====

    ANSWER:

    =====
    {answer}
    =====
"""
)


llm_chain = prompt | giga


async def evaluate_hallucinations(session_id, context, answer, question):
    result = await llm_chain.ainvoke({"context": context, "answer": answer, "question": question})
    print(f'**tokens used for validation: {result}')
    result = result.content if hasattr(result, 'content') else str(result)
    save_to_database(session_id, context, question, answer, result)
    return result
