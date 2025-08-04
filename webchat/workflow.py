from webchat.utils.utils import (
    extract_key_info,
    update_page_content,
    remove_none_values,
    process_response_updates,
)

from webchat.core.chains.guardrails_chains import (
    return_query_validator,
    return_guidelines_validator,
    return_query_validator_copyright,
)
from typing import Any
from webchat.core.chains.core_chains import return_updated_wesite
import asyncio
import logging
import json
import os


def setup_app_logger():
    """Setup a logger that works in serverless environments like Vercel"""
    app_logger = logging.getLogger("workflow_logger")

    # Remove existing handlers (safety)
    for handler in app_logger.handlers[:]:
        app_logger.removeHandler(handler)

    app_logger.setLevel(logging.INFO)

    # Use StreamHandler instead of FileHandler for serverless environments
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)
    app_logger.addHandler(stream_handler)
    app_logger.propagate = False

    return app_logger


# Set up logger
logger = setup_app_logger()


async def get_updated_page_content_openai(
    payload_data,
    model_output,
    page_name,
    query,
    text_to_change,
    section,
    all_pages_names,
) -> Any:
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
    response = await return_updated_wesite(
        business_info,
        left_panel,
        query,
        main_output,
        page_name,
        text_to_change,
        section,
        all_pages_names,
    )
    logger.info("Here is the main output below")
    logger.info(json.dumps(main_output, indent=4, ensure_ascii=False))

    logger.info("=" * 60)
    logger.info(f"Updated answer {response}")
    logger.info("OPENAI RESPONSE FROM return_updated_wesite:")
    try:
        if isinstance(response, (dict, list)):
            logger.info(json.dumps(response, indent=4, ensure_ascii=False))
        else:
            logger.info(f"Response (non-JSON): {response}")
    except Exception as e:
        logger.error(f"Could not serialize response for logging: {e}")
        logger.info(f"Response (raw): {str(response)}")

    # FIX: Correct parameter order - response should be second parameter
    updated_content = process_response_updates(main_output, response, page_name)

    logger.info("=" * 60)
    logger.info("UPDATED CONTENT AFTER process_response_updates:")
    try:
        if isinstance(updated_content, (dict, list)):
            logger.info(json.dumps(updated_content, indent=4, ensure_ascii=False))
        else:
            logger.info(f"Updated content (non-JSON): {updated_content}")
    except Exception as e:
        logger.error(f"Could not serialize updated_content for logging: {e}")
        logger.info(f"Updated content (raw): {str(updated_content)}")

    cleaned_content = remove_none_values(updated_content)

    logger.info("=" * 60)
    logger.info("CLEANED CONTENT AFTER remove_none_values:")
    try:
        if isinstance(cleaned_content, (dict, list)):
            logger.info(json.dumps(cleaned_content, indent=4, ensure_ascii=False))
        else:
            logger.info(f"Cleaned content (non-JSON): {cleaned_content}")
    except Exception as e:
        logger.error(f"Could not serialize cleaned_content for logging: {e}")
        logger.info(f"Cleaned content (raw): {str(cleaned_content)}")

    final_response = update_page_content(model_output, cleaned_content)

    logger.info("=" * 60)
    logger.info("FINAL RESPONSE AFTER update_page_content:")
    try:
        if isinstance(final_response, (dict, list)):
            logger.info(json.dumps(final_response, indent=4, ensure_ascii=False))
        else:
            logger.info(f"Final response (non-JSON): {final_response}")
    except Exception as e:
        logger.error(f"Could not serialize final_response for logging: {e}")
        logger.info(f"Final response (raw): {str(final_response)}")

    logger.info("=" * 60)

    return final_response
