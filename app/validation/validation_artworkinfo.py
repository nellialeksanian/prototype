from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import os
import settings.settings
from sql.create_tables import save_to_database


gigachat_token = settings.settings.GIGACHAT_TOKEN

giga = GigaChat (
    credentials=gigachat_token,
    model="GigaChat-Max", 
    scope="GIGACHAT_API_B2B",
    verify_ssl_certs=False
)  

prompt = PromptTemplate(
    input_variables=["context", "description"],
    template="""
    You are an expert fact-checker and summarization analyst. Your task is to determine whether the SUMMARY accurately reflects the information in the CONTEXT. Most summaries contain some form of hallucination, even subtle ones. Your job is to **identify even the smallest unsupported, exaggerated, or inferred detail** and err on the side of calling the summary hallucinated unless it is **entirely and unquestionably faithful** to the source.
    A **hallucination** occurs when the SUMMARY:
    - **Contradicts** the CONTEXT or presents information that is not part of the CONTEXT.
    - **Adds details or claims** that are **not supported** by the CONTEXT, including those that could be inferred but are not explicitly stated.
    - **Adds specific details not explicitly present in the CONTEXT**, such as (but not limited to) exact dates, specific times, names of individuals not mentioned, precise locations beyond general references, ages not provided, or any other quantifiable or identifiable information that is not directly stated.
    - **Infers or implies** facts that go beyond what is clearly stated in the CONTEXT.
    - **Exaggerates, distorts**, or otherwise **alters the meaning, tone, or significance** of the CONTEXT.

    The **SUMMARY is faithful** if:
    - It **accurately reflects the facts, tone, and spirit** of the CONTEXT, without overstating, generalizing, or inferring unsupported details.
    - It does **not include** new conclusions or facts not directly grounded in the CONTEXT.
    - It stays true to the **intended meaning** and **significance** of the CONTEXT, without altering or overstating any part of the original message.

    ### Instructions:
    **Perform a step-by-step chain of reasoning**:
    1. Break down the SUMMARY into **individual claims** or **statements**.
    2. For each claim, assess whether it:
        a)Is it stated in the CONTEXT? If not, flag it.
        b) Is this claim **directly and explicitly stated** in the CONTEXT, including all specific details? If a specific detail (like a date, time, or name) is present in the summary but not the context, flag it.
          c)Does this claim introduce any **specific information** (e.g., a date, a precise number, a name) that is not explicitly found in the CONTEXT? If so, flag it.
        d)Does this claim introduce any **new information, even seemingly minor details** not present in the CONTEXT? If so, flag it.
        e)Does this claim make any **inference or implication** that goes beyond the explicit statements in the CONTEXT? If so, flag it.
        f)Does it exaggerate or change tone? If so, flag it.
        g)Does it generalize or imply more than the CONTEXT says? If yes, flag it.
        h)Does it contain **unsupported**, **exaggerated**, or **contradictory** information? If yes, flag it.
        i)Does it distorts the **tone, meaning, or significance** of the CONTEXT (e.g., makes the message sound more extreme, general, or conclusive than the original)? If yes, flag it.
        j)Does this claim state something the CONTEXT **explicitly negates** or **does not mention at all** (without the summary explicitly stating the absence)? If so, flag it.
    3. If **any** part of the summary is even slightly unsupported, mark the entire SUMMARY as:
        - **hallucinated**
        Otherwise, if it is **fully supported and perfectly aligned**, mark:
        - **faithful*
        Note: Default to **hallucinated** unless fully certain.
    **Important:** Always **err on the side of caution**. If in doubt, label it as **hallucinated**. Prioritize **accuracy** and **fidelity** to the source. If any detail could be misinterpreted as an inference, exaggeration, or distortion, label it as **hallucinated**.

    ### Key Guidance:
    - **Avoid overgeneralizing** or inferring conclusions that are not explicit in the CONTEXT.
    - Focus on both **factual accuracy** and the **spirit** of the CONTEXT, ensuring that the meaning and tone are preserved.
    - Do **not** include reasoning in your final answer. Respond only with one of the two labels: "hallucinated" or "faithful".

    ### Examples:

    Example 1:
    CONTEXT:
    The mayor announced a new initiative to plant 10,000 trees over the next five years to combat rising temperatures and improve air quality in urban neighborhoods. The project will start in the city center and expand to outer districts.

    SUMMARY:
    The mayor introduced a five-year plan to plant 10,000 trees to fight climate change and improve air quality in the city.

    Result: → faithful
    Reasoning:
    - 5-year plan → stated.
    - 10,000 trees → stated.
    - Improve air quality → stated.
    - "Fight climate change" → generalizes "combat rising temperatures", but remains consistent and not misleading.

    Example 2:
    CONTEXT:
    The new health guidelines recommend at least 150 minutes of moderate physical activity per week for adults. They also emphasize muscle-strengthening activities on two or more days per week. No specific diet plans are included in the guidelines.

    SUMMARY:
    The health guidelines advise both regular exercise and a plant-based diet for optimal health.

    Result: → hallucinated
    Reasoning:
    - Exercise → supported.
    - Plant-based diet → not in context → hallucinated.

    Example 3:
    CONTEXT:
    The Department of Transportation has launched a new bike lane expansion project aimed at reducing traffic congestion in the downtown area. Over the next two years, more than 25 miles of new bike lanes will be added. The project will begin in neighborhoods with existing cycling infrastructure to ensure seamless connectivity and will later extend to underserved areas. Officials emphasized the plan is about improving urban mobility, not just encouraging cycling.

    SUMMARY:
    The Department of Transportation is encouraging cycling by launching a project to build 25 miles of bike lanes, starting in underserved areas.

    Result: → hallucinated
    Reasoning:
    - "Encouraging cycling" as the main purpose contradicts stated goal → distorted.
    - "Starting in underserved areas" contradicts rollout plan → incorrect.

    NOTE: Be skeptical. It's better to flag a minor hallucination than to let one pass.
    You will be evaluated based on your ability to catch even minor hallucinations. False negatives (missing a hallucination) are considered worse than false positives.

    Now evaluate the following:

    CONTEXT:
    =====
    {context}
    =====

    QUERY:
    =====
    Summarize the context
    =====

    SUMMARY:
    =====
    {description}
    =====

    """
)

llm_chain = prompt | giga

async def evaluate_hallucinations_artworkinfo(session_id, context, answer):
    context_text = context.get("text")
    result = await llm_chain.ainvoke({"context": context_text, "description": answer})
    
    print(f'**tokens used for validation: {result}')
    finish_reason = result.response_metadata.get("finish_reason")
    
    if finish_reason == "blacklist":
        print(f"Finish reason for artwork_info validation: {finish_reason}. Regeneration with the short_description.")
        context_text = context.get("short_description")
        result = await llm_chain.ainvoke({"context": context_text, "description": answer})
        print(f'**tokens used for validation: {result}')

    question = "Опиши картину"
    result = result.content if hasattr(result, 'content') else str(result)
    await save_to_database(session_id, context_text, question, answer, result)
    return result
