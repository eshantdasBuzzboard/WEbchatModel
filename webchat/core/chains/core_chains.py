from webchat.core.prompts.core_prompts import website_update_prompt
from webchat.core.pydantic_classes.guardrails_classes import Page

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
import json
from typing import Any

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1", temperature=0, use_responses_api=True, max_retries=3)


async def return_updated_wesite(
    business_info,
    left_panel_info,
    query,
    current_output,
    page,
    text_to_change,
    section,
    all_pages_names,
) -> Any:
    llmr = llm.with_structured_output(Page)
    updated_output_chain = website_update_prompt | llmr
    input_data = {
        "business_info": business_info,
        "left_panel_info": left_panel_info,
        "current_output": current_output,
        "query": query,
        "text_to_change": text_to_change,
        "page_name": page,
        "section": section,
        "all_pages_names": all_pages_names,
    }
    result = await updated_output_chain.ainvoke(input_data)
    return [json.loads(result.model_dump_json())]
