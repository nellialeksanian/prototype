from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import os
import settings.settings
from sql.create_tables import save_to_database

gigachat_token = settings.settings.GIGACHAT_TOKEN_MAX

giga = GigaChat (
    credentials=gigachat_token,
    model="GigaChat-Max",
    verify_ssl_certs=False
)

prompt = PromptTemplate(
    input_variables=["context", "question", "answer"],
    template="""
    You are a fact-checking assistant. Your job is to identify whether the ANSWER contains any hallucinations based on the CONTEXT and QUESTION.

    Definition:
    - A hallucination occurs if the ANSWER:
    - Includes claims or facts that are not in the CONTEXT.
    - Contradicts information in the CONTEXT.
    - Fails to directly and accurately answer the QUESTION.
    - An ANSWER is faithful if:
    - It answers the QUESTION based only on the CONTEXT, OR
    - It states that the CONTEXT does not contain enough information.

    Instructions:
    Respond only with:
    - "true" if the ANSWER contains any hallucination.
    - "false" if the ANSWER is completely grounded in the CONTEXT.

    Example 1:
    CONTEXT: Marie Curie won two Nobel Prizes.
    QUESTION: How many Nobel Prizes did Marie Curie win?
    ANSWER: Marie Curie won two Nobel Prizes.
    → false

    Example 2:
    CONTEXT: Marie Curie won two Nobel Prizes.
    QUESTION: What kind of music did Marie Curie enjoy?
    ANSWER: Marie Curie enjoyed classical music.
    → true

    Example 3:
    CONTEXT: The Great Fire of London started in a bakery on Pudding Lane in 1666. It destroyed much of the city, including 87 churches and thousands of homes. There were very few recorded deaths.
    QUESTION: Summarize the event in one or two sentences.
    ANSWER: The Great Fire of London in 1666 began in a bakery on Pudding Lane and caused widespread destruction, including the loss of many buildings and lives.
    → true

    Example 4:
    CONTEXT: The Great Fire of London started in a bakery on Pudding Lane in 1666. It destroyed much of the city, including 87 churches and thousands of homes. There were very few recorded deaths.
    QUESTION: Summarize the event in one or two sentences.
    ANSWER: The Great Fire of London in 1666 began in a bakery on Pudding Lane and destroyed a large part of the city, including many homes and churches. Few deaths were recorded.
    → false

    Now evaluate the following:

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
    context_text = context.get("text")
    result = await llm_chain.ainvoke({"context": context_text, "answer": answer, "question": question})
    print(f'**tokens used for validation: {result}')
    response_text_new = result.content
    if len(response_text_new) > 13:
        print("The BLACKLIST problem while validating. Regeneration with the short_description.")
        context_text = context.get("short_description")
        result =  await llm_chain.ainvoke({"context": context_text, "answer": answer, "question": question})
        print(f'**Validation result is generated with short_description') 
        print(f'**tokens used for validation: {result}') 
    result = result.content if hasattr(result, 'content') else str(result)
    await save_to_database(session_id, context_text, question, answer, result)
    return result
