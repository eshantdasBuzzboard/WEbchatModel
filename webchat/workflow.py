from webchat.utils.utils import (
    extract_key_info,
    update_page_content,
    remove_none_values,
)

from webchat.core.chains.guardrails_chains import (
    return_query_validator,
    return_query_validator_copyright,
)
from webchat.core.chains.core_chains import return_updated_wesite
import asyncio


async def get_updated_page_content_openai(payload_data, model_output, page_name, query):
    # Step 1: Extract relevant page info
    main_output, left_panel, if_copyright, business_info = await extract_key_info(
        payload_data, model_output, page_name
    )

    # Step 2: Run query validation
    if if_copyright == "no":
        # Run both validations concurrently
        check_copyright_task, query_validator_task = await asyncio.gather(
            return_query_validator_copyright(main_output, query),
            return_query_validator(query),
        )

        if query_validator_task.get("score") == 0:
            return query_validator_task.get("reason")
        if check_copyright_task.get("score") == 0:
            return check_copyright_task.get("reason")

    else:
        query_validator_task = await return_query_validator(query)
        if query_validator_task.get("score") == 0:
            return query_validator_task.get("reason")

    # Step 3: Generate updated content
    updated_content = await return_updated_wesite(
        business_info, left_panel, query, main_output
    )
    cleaned_content = remove_none_values(updated_content)
    final_response = update_page_content(model_output, cleaned_content)
    return final_response
