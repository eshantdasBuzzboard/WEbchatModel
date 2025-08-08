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
from typing import Any, List, Dict
from webchat.core.chains.core_chains import return_updated_wesite
import asyncio
import logging
import json
import os


def setup_app_logger():
    """Setup a logger that writes to log.log (works locally, but be careful in serverless)"""
    app_logger = logging.getLogger("workflow_logger")

    # Remove existing handlers
    for handler in app_logger.handlers[:]:
        app_logger.removeHandler(handler)

    app_logger.setLevel(logging.INFO)

    # Ensure log directory exists

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    app_logger.propagate = False

    return app_logger


# Set up logger
logger = setup_app_logger()


def process_suggestions_response(response: List[Dict]) -> List[Dict]:
    """
    Process the new suggestions response format and ensure consistency
    """
    processed_suggestions = []

    for item in response:
        if isinstance(item, dict) and "outputs_list" in item:
            processed_item = {
                "outputs_list": item.get("outputs_list", []),
                "index": item.get("index", 0),
                "section": item.get("section", ""),
                "original_text": item.get("original_text", ""),
            }
            processed_suggestions.append(processed_item)

            logger.info(
                f"Processed suggestion for section: {processed_item['section']}"
            )
            logger.info(f"Number of outputs: {len(processed_item['outputs_list'])}")

    return processed_suggestions


async def get_updated_page_content_openai(
    payload_data,
    model_output,
    page_name,
    query,
    text_to_change,
    section,
    all_pages_names,
) -> Any:
    """
    Enhanced function to handle both suggestion-based and direct update responses
    """
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
            logger.warning(f"Query validation failed: {query_task.get('reason')}")
            return query_task.get("reason")
        if copyright_task.get("score") == 0:
            logger.warning(
                f"Copyright validation failed: {copyright_task.get('reason')}"
            )
            return copyright_task.get("reason")
        if guidelines_task.get("score") == 0:
            logger.warning(
                f"Guidelines validation failed: {guidelines_task.get('reason')}"
            )
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
            logger.warning(f"Query validation failed: {query_task.get('reason')}")
            return query_task.get("reason")
        if guidelines_task.get("score") == 0:
            logger.warning(
                f"Guidelines validation failed: {guidelines_task.get('reason')}"
            )
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

    logger.info("=" * 60)
    logger.info("OPENAI RESPONSE FROM return_updated_wesite:")
    logger.info(f"Response type: {type(response)}")

    try:
        if isinstance(response, (dict, list)):
            logger.info(json.dumps(response, indent=4, ensure_ascii=False))
        else:
            logger.info(f"Response (non-JSON): {response}")
    except Exception as e:
        logger.error(f"Could not serialize response for logging: {e}")
        logger.info(f"Response (raw): {str(response)}")

    # Step 4: Handle the response based on its structure
    if isinstance(response, list) and len(response) > 0:
        # Check if this is the new suggestions format
        first_item = response[0]
        if isinstance(first_item, dict) and "outputs_list" in first_item:
            logger.info("Processing as suggestions response (new format)")

            # Process and validate the suggestions
            processed_suggestions = process_suggestions_response(response)

            logger.info(f"Processed {len(processed_suggestions)} suggestion groups")

            # Add original text to suggestions for context
            for suggestion in processed_suggestions:
                suggestion["original_text"] = text_to_change

            # Return the suggestions for the frontend to handle
            return processed_suggestions

        else:
            logger.info("Processing as direct update response (legacy format)")

            # This is the legacy direct update format - process as before
            updated_content = process_response_updates(main_output, response, page_name)

            logger.info("=" * 60)
            logger.info("UPDATED CONTENT AFTER process_response_updates:")
            try:
                if isinstance(updated_content, (dict, list)):
                    logger.info(
                        json.dumps(updated_content, indent=4, ensure_ascii=False)
                    )
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
                    logger.info(
                        json.dumps(cleaned_content, indent=4, ensure_ascii=False)
                    )
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
                    logger.info(
                        json.dumps(final_response, indent=4, ensure_ascii=False)
                    )
                else:
                    logger.info(f"Final response (non-JSON): {final_response}")
            except Exception as e:
                logger.error(f"Could not serialize final_response for logging: {e}")
                logger.info(f"Final response (raw): {str(final_response)}")

            logger.info("=" * 60)
            return final_response

    elif isinstance(response, str):
        logger.info("Processing as string response (error/validation failure)")
        return response

    else:
        logger.error(f"Unexpected response format: {type(response)}")
        return f"Unexpected response format: {type(response)}"


async def apply_suggestion_to_content(
    payload_data, model_output, page_name: str, selected_suggestion: Dict[str, Any]
) -> Any:
    """
    Apply a selected suggestion directly to the content without going through the full workflow
    """
    try:
        logger.info("=" * 60)
        logger.info("APPLYING SELECTED SUGGESTION:")
        logger.info(f"Section: {selected_suggestion.get('section')}")
        logger.info(f"Selected output: {selected_suggestion.get('selected_output')}")
        logger.info("=" * 60)

        # Extract the necessary information
        main_output, left_panel, if_copyright, business_info = await extract_key_info(
            payload_data, model_output, page_name
        )

        # Create a mock response structure that mimics the direct update format
        # This allows us to reuse the existing processing pipeline
        mock_response = [main_output.copy()]  # Start with the original content

        # Update the specific section with the selected suggestion
        section = selected_suggestion.get("section", "")
        selected_output = selected_suggestion.get("selected_output", "")

        # Map the section to the correct field in the content structure
        section_field_mapping = {
            "Meta Title": "Meta Title (30 to 60 Characters)",
            "Meta Description": "Meta Description (70 to 143 Characters)",
            "Hero Title": "Hero Title (20 to 70 Characters)",
            "Hero Text": "Hero Text (50 to 100 Characters)",
            "Hero CTA": "Hero CTA",
            "H1": "H1 (30 to 70 Characters)",
            "H1 Content": "H1 Content",
            "Header": "Header",
            "Leading Sentence": "Leading Sentence",
            "CTA Button": "CTA Button",
        }

        # Get the correct field name
        field_name = section_field_mapping.get(section, section)

        # Apply the selected suggestion to the mock response
        if field_name in mock_response[0]:
            mock_response[0][field_name] = selected_output
            logger.info(f"Applied suggestion to field: {field_name}")
        else:
            logger.warning(f"Field {field_name} not found in content structure")
            # Try to handle H2 sections or other nested structures
            if section.startswith("H2") and "h2_sections" in mock_response[0]:
                # Handle H2 section updates - would need more specific logic
                logger.info("H2 section update detected - may need specific handling")

        # Process the mock response through the existing pipeline
        updated_content = process_response_updates(
            main_output, mock_response, page_name
        )
        cleaned_content = remove_none_values(updated_content)
        final_response = update_page_content(model_output, cleaned_content)

        logger.info("=" * 60)
        logger.info("SUGGESTION APPLICATION COMPLETE:")
        logger.info(f"Successfully applied suggestion for {section}")
        logger.info("=" * 60)

        return final_response

    except Exception as e:
        logger.error(f"Error applying suggestion: {str(e)}")
        logger.error(f"Suggestion data: {selected_suggestion}")
        raise
