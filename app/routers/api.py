from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
import traceback

from test_data import (
    main_payload_test_data,
    webpage_content_output_test_data,
    business_info,
    combined_data,
)
from webchat.workflow import get_updated_page_content_openai
from app.utils.content_utils import (
    convert_page_keys_for_update,
    extract_updated_page_from_response,
    identify_content_section,
)
from app.utils.constants import ACTION_QUESTIONS

router = APIRouter()
logger = logging.getLogger(__name__)


class AIRequest(BaseModel):
    selected_text: str
    user_question: str
    current_set: int
    current_page: int
    webpage_output: dict
    payload_output: dict
    business_info: dict
    action_type: Optional[str] = None


class SelectionRequest(BaseModel):
    selected_option: Dict[str, Any]  # The selected option from suggestions
    current_set: int
    current_page: int
    webpage_output: dict
    payload_output: dict
    business_info: dict


def get_page_titles_flexible(combined_data, element_index):
    """Extract page titles/names from either data structure"""
    if element_index < len(combined_data):
        pages = combined_data[element_index]["pages"]
        # Try both possible keys
        if pages and "title" in pages[0]:
            return [page["title"] for page in pages]
        elif pages and "Page Name" in pages[0]:
            return [page["Page Name"] for page in pages]
    return []


def apply_selection_to_content(webpage_output: dict, selection: Dict[str, Any]) -> dict:
    """
    Apply the selected option to the webpage content
    """
    try:
        # Extract selection details
        section = selection.get("section", "")
        selected_output = selection.get("selected_output", "")

        logger.info(f"Applying selection: {selected_output} to section: {section}")

        # Create a copy of the webpage output to modify
        updated_content = webpage_output.copy()

        # Map the section to the correct field in webpage_output
        section_mapping = {
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
        field_name = section_mapping.get(section, section)

        # Apply the selected output to the content
        if field_name in updated_content:
            updated_content[field_name] = selected_output
            logger.info(f"Successfully updated {field_name} with: {selected_output}")
        else:
            # Handle H2 sections and other complex structures
            if section.startswith("H2") and "h2_sections" in updated_content:
                # Handle H2 section updates - would need specific logic based on H2 structure
                logger.info(f"H2 section update needed for: {section}")
            else:
                logger.warning(f"Field {field_name} not found in webpage content")

        return updated_content

    except Exception as e:
        logger.error(f"Error applying selection to content: {str(e)}")
        raise


@router.get("/data/{set_number}")
async def get_data(set_number: int):
    if set_number < 1 or set_number > 3:
        return {"error": "Invalid set number. Must be 1, 2, or 3"}

    index = set_number - 1
    return {
        "main_payload": main_payload_test_data[index]
        if index < len(main_payload_test_data)
        else {},
        "webpage_content": webpage_content_output_test_data[index]
        if index < len(webpage_content_output_test_data)
        else {},
        "business_info": business_info[index] if index < len(business_info) else {},
    }


@router.post("/ask-ai")
async def ask_ai(request: AIRequest):
    selected_text = request.selected_text
    user_question = request.user_question
    current_set = request.current_set
    current_page = request.current_page
    webpage_output = request.webpage_output
    payload_output = request.payload_output
    action_type = request.action_type

    page_name = webpage_output.get(
        "Page Name", payload_output.get("title", f"Page {current_page + 1}")
    )
    content_section = identify_content_section(selected_text, webpage_output)

    # Determine the actual question to process
    if action_type and action_type in ACTION_QUESTIONS:
        actual_question = ACTION_QUESTIONS[action_type]
        logger.info(f"Processing action: {action_type} -> {actual_question}")
    elif user_question and user_question.strip():
        logger.info(f"Processing question: {user_question}")
        actual_question = user_question
    else:
        return {
            "success": False,
            "response": "No question or action provided",
            "summary": {
                "set_number": current_set - 1,
                "page_name": page_name,
                "content_section": content_section,
                "selected_text": selected_text,
                "user_question": user_question,
                "action_type": action_type,
            },
        }

    simplified_response = {
        "set_number": current_set - 1,
        "page_name": page_name,
        "content_section": content_section,
        "selected_text": selected_text,
        "user_question": actual_question,
        "action_type": action_type,
        "is_predefined_action": bool(action_type),
    }

    logger.info(json.dumps(simplified_response, indent=4, ensure_ascii=False))
    logger.info("=" * 60)

    if selected_text:
        try:
            all_pages_names = get_page_titles_flexible(combined_data, current_set - 1)
            payload_output = combined_data[current_set - 1]
            webpage_output_for_api = webpage_content_output_test_data[current_set - 1]

            selected_text_fixed = (
                selected_text
                if isinstance(selected_text, str)
                else selected_text[0]
                if isinstance(selected_text, tuple)
                else str(selected_text)
            )

            # Call the workflow function
            response = await get_updated_page_content_openai(
                payload_output,
                webpage_output_for_api,
                page_name,
                actual_question,
                selected_text_fixed,
                content_section,
                all_pages_names,
            )

            logger.info("=" * 60)
            logger.info(f"Response type: {type(response)}")
            logger.info("WORKFLOW RESPONSE RECEIVED")

            # Handle different response types
            if isinstance(response, list) and len(response) > 0:
                # Check if this is the new suggestions format
                first_item = response[0]
                if isinstance(first_item, dict) and "outputs_list" in first_item:
                    logger.info("Processing as suggestions response")

                    # Format suggestions for frontend
                    suggestions = []
                    for item in response:
                        suggestion = {
                            "outputs_list": item.get("outputs_list", []),
                            "index": item.get("index", 0),
                            "section": item.get("section", ""),
                            "original_text": selected_text_fixed,
                        }
                        suggestions.append(suggestion)

                    return {
                        "success": True,
                        "response_type": "suggestions",
                        "suggestions": suggestions,
                        "message": f"Here are suggested improvements for the selected text in the {content_section} section:",
                        "summary": simplified_response,
                        "action_applied": action_type,
                    }
                else:
                    # This is the legacy direct update format
                    logger.info("Processing as direct update response (legacy format)")

                    updated_page = extract_updated_page_from_response(
                        response, current_set, current_page
                    )

                    if updated_page:
                        converted_page = convert_page_keys_for_update(updated_page)

                        success_message = (
                            f"Content successfully updated!"
                            if not action_type
                            else f"Content successfully {ACTION_QUESTIONS[action_type].lower()}!"
                        )

                        return {
                            "success": True,
                            "response_type": "direct_update",
                            "response": success_message,
                            "updated_content": [converted_page],
                            "summary": simplified_response,
                            "action_applied": action_type,
                        }
                    else:
                        return {
                            "success": True,
                            "response": "Update failed: Could not extract updated page from response",
                            "updated_content": "Could not extract updated page from response",
                            "summary": simplified_response,
                        }

            elif isinstance(response, str):
                logger.info("Processing as error response (string)")
                return {
                    "success": True,
                    "response_type": "error",
                    "response": f"Update failed: {response}",
                    "updated_content": response,
                    "summary": simplified_response,
                }
            else:
                logger.error(f"Unexpected response format: {type(response)}")
                return {
                    "success": False,
                    "response": "Unexpected response format from AI",
                    "summary": simplified_response,
                }

        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Exception in ask_ai: {str(e)}")
            logger.error(f"Traceback:\n{tb_str}")

            return {
                "success": False,
                "response": f"Error processing request: {str(e)}",
                "error": str(e),
                "summary": simplified_response,
            }
    else:
        logger.info("Processing as regular AI response (no selected text)")

        if action_type:
            ai_response = f"""Set: {current_set} | Page: {page_name} | Section: {content_section}

Action: {ACTION_QUESTIONS[action_type]}

AI Analysis: This appears to be a predefined action request, but no text was selected. Please select text first to apply actions."""
        else:
            ai_response = f"""Set: {current_set} | Page: {page_name} | Section: {content_section}

Question: {actual_question}

AI Analysis: This is a regular AI response. To update page content, try selecting text and asking questions about modifying, updating, or improving the content."""

        return {
            "success": True,
            "response_type": "info",
            "response": ai_response,
            "summary": simplified_response,
            "action_applied": action_type,
        }


@router.post("/apply-selection")
async def apply_selection(request: SelectionRequest):
    """
    Apply the selected suggestion to the content
    """
    try:
        selected_option = request.selected_option
        current_set = request.current_set
        current_page = request.current_page
        webpage_output = request.webpage_output
        payload_output = request.payload_output

        logger.info("=" * 60)
        logger.info("APPLYING USER SELECTION:")
        logger.info(f"Selection: {json.dumps(selected_option, indent=2)}")
        logger.info("=" * 60)

        # Apply the selection to the webpage content
        updated_content = apply_selection_to_content(webpage_output, selected_option)

        # Convert to the format expected by the frontend
        converted_page = convert_page_keys_for_update(updated_content)

        logger.info("Selection successfully applied and converted for frontend")

        return {
            "success": True,
            "response": "Content successfully updated with your selection!",
            "updated_content": [converted_page],
            "summary": {
                "set_number": current_set - 1,
                "page_name": webpage_output.get(
                    "Page Name", f"Page {current_page + 1}"
                ),
                "selected_section": selected_option.get("section", ""),
                "selected_output": selected_option.get("selected_output", ""),
            },
        }

    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Exception in apply_selection: {str(e)}")
        logger.error(f"Traceback:\n{tb_str}")

        return {
            "success": False,
            "response": f"Error applying selection: {str(e)}",
            "error": str(e),
        }
