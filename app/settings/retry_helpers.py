from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from aiohttp import ClientError


@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, ClientError))
)
async def invoke_llm_chain(llm_chain_obj, payload):
    return await llm_chain_obj.ainvoke(payload)