from langchain_openai import ChatOpenAI
from webchat.core.prompts.guardrails_prompts import query_checker_prompt
from webchat.core.pydantic_classes.guardrails_classes import QueryValidator
import json


from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1", temperature=0, use_responses_api=True, max_retries=3)


async def return_query_validator(search_query: str):
    llm_structured = llm.with_structured_output(QueryValidator)
    query_validator_chain = query_checker_prompt | llm_structured
    input_data = {"search_query_or_request": search_query}
    result = await query_validator_chain.ainvoke(input_data)
    return json.loads(result.model_dump_json())
