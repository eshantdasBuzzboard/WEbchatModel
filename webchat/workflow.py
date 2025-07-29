from webchat.utils.utils import (
    extract_key_info,
    update_page_content,
    remove_none_values,
)

from webchat.core.chains.guardrails_chains import (
    return_query_validator,
    return_guidelines_validator,
    return_query_validator_copyright,
)
from webchat.core.chains.core_chains import return_updated_wesite
import asyncio


async def get_updated_page_content_openai(
    payload_data,
    model_output,
    page_name,
    query,
    text_to_change,
    section,
    all_pages_names,
):
    # Step 1: Extract relevant page info
    main_output, left_panel, if_copyright, business_info = await extract_key_info(
        payload_data, model_output, page_name
    )

    # Step 2: Run query validation
    if if_copyright == "no":
        # Run all validations concurrently
        copyright_task, query_task, guidelines_task = await asyncio.gather(
            return_query_validator_copyright(main_output, query),
            return_query_validator(query),
            return_guidelines_validator(
                query, section, payload_data, model_output, all_pages_names
            ),
        )

        if query_task.get("score") == 0:
            return query_task.get("reason")
        if copyright_task.get("score") == 0:
            return copyright_task.get("reason")
        if guidelines_task.get("score") == 0:
            return guidelines_task.get("reason")

    else:
        # Run query and guidelines validators concurrently
        query_task, guidelines_task = await asyncio.gather(
            return_query_validator(query),
            return_guidelines_validator(
                query, section, payload_data, model_output, all_pages_names
            ),
        )

        if query_task.get("score") == 0:
            return query_task.get("reason")
        if guidelines_task.get("score") == 0:
            return guidelines_task.get("reason")

    # Step 3: Generate updated content
    updated_content = await return_updated_wesite(
        business_info,
        left_panel,
        query,
        main_output,
        page_name,
        text_to_change,
        section,
        all_pages_names,
    )
    cleaned_content = remove_none_values(updated_content)
    final_response = update_page_content(model_output, cleaned_content)
    return final_response
