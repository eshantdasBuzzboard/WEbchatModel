from fastapi import APIRouter
from pydantic import BaseModel
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
    # business_info_data = request.business_info

    page_name = webpage_output.get(
        "Page Name", payload_output.get("title", f"Page {current_page + 1}")
    )
    content_section = identify_content_section(selected_text, webpage_output)

    simplified_response = {
        "set_number": current_set - 1,
        "page_name": page_name,
        "content_section": content_section,
        "selected_text": selected_text,
        "user_question": user_question,
    }

    logger.info(json.dumps(simplified_response, indent=4, ensure_ascii=False))
    logger.info("=" * 60)

    is_update_request = True  # You can update this logic if needed

    if is_update_request and selected_text:
        try:
            payload_output = combined_data[current_set - 1]
            webpage_output_for_api = webpage_content_output_test_data[current_set - 1]

            selected_text_fixed = (
                selected_text
                if isinstance(selected_text, str)
                else selected_text[0]
                if isinstance(selected_text, tuple)
                else str(selected_text)
            )

            response = await get_updated_page_content_openai(
                payload_output,
                webpage_output_for_api,
                page_name,
                user_question,
                selected_text_fixed,
                content_section,
            )

            logger.info("=" * 60)
            logger.info(f"{content_section}")
            logger.info("OPENAI RESPONSE RECEIVED:")
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response is list: {isinstance(response, list)}")
            logger.info(f"Response is string: {isinstance(response, str)}")

            try:
                if isinstance(response, (dict, list)):
                    logger.info(
                        f"Response content (JSON): {json.dumps(response, indent=2, ensure_ascii=False)}"
                    )
                else:
                    logger.info(f"Response content (raw): {response}")
            except Exception as log_error:
                logger.info(f"Could not serialize response for logging: {log_error}")
                logger.info(f"Response content (str): {str(response)}")

            logger.info("=" * 60)

            if isinstance(response, list):
                logger.info("Processing as successful update (list response)")

                updated_page = extract_updated_page_from_response(
                    response, current_set, current_page
                )

                if updated_page:
                    logger.info(
                        f"Successfully extracted updated page for Set {current_set}, Page {current_page}"
                    )

                    converted_page = convert_page_keys_for_update(updated_page)

                    logger.info(f"Original page keys: {list(updated_page.keys())}")
                    logger.info(f"Converted page keys: {list(converted_page.keys())}")
                    logger.info(
                        f"Page_Name in converted page: {converted_page.get('Page_Name', 'NOT FOUND')}"
                    )

                    return {
                        "success": True,
                        "response": "Page content has been updated successfully!",
                        "updated_content": [converted_page],
                        "summary": simplified_response,
                    }
                else:
                    logger.error("Failed to extract updated page from response")
                    return {
                        "success": True,
                        "response": "Update failed: Could not extract updated page from response",
                        "updated_content": "Could not extract updated page from response",
                        "summary": simplified_response,
                    }

            elif isinstance(response, str):
                logger.info("Processing as failed update (string response)")
                return {
                    "success": True,
                    "response": f"Update failed: {response}",
                    "updated_content": response,
                    "summary": simplified_response,
                }
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Exception in get_updated_page_content_openai: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Traceback:\n{tb_str}")
            error_message = (
                f"Error during update: {str(e)}\n"
                f"Exception Type: {type(e)}\n"
                f"Traceback:\n{tb_str}"
            )
            return {
                "success": False,
                "response": error_message,
                "updated_content": error_message,
                "summary": simplified_response,
            }
    else:
        logger.info("Processing as regular AI response (no update request)")
        ai_response = f"""Set: {current_set} | Page: {page_name} | Section: {content_section}

Selected Text: "{selected_text}"
Question: {user_question}

AI Analysis: This is a regular AI response. To update page content, try asking questions like "update this text" or "change this content"."""
        return {
            "success": True,
            "response": ai_response,
            "summary": simplified_response,
        }
