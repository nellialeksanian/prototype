from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import os
import settings.settings
from sql.create_tables import save_to_database


gigachat_token = settings.settings.GIGACHAT_TOKEN

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

llm_chain = prompt | giga

async def evaluate_hallucinations_artworkinfo(session_id, context, answer):
    result = await llm_chain.ainvoke({"context": context, "description": answer})
    question = "Опиши картину"
    print(f'**tokens used for validation: {result}')
    result = result.content if hasattr(result, 'content') else str(result)
    await save_to_database(session_id, context, question, answer, result)
    return result
