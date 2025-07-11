from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import logging
import traceback
from datetime import datetime
from test_data import (
    main_payload_test_data,
    webpage_content_output_test_data,
    business_info,
    combined_data,
)
from webchat.workflow import get_updated_page_content_openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("log.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class AIRequest(BaseModel):
    selected_text: str
    user_question: str
    current_set: int
    current_page: int
    webpage_output: dict
    payload_output: dict
    business_info: dict


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "main_payload_data": main_payload_test_data,
            "webpage_content_data": webpage_content_output_test_data,
            "business_info": business_info,
        },
    )


@app.get("/api/data/{set_number}")
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


def convert_page_keys_for_update(page_data):
    """
    Convert page keys from original format to the format expected by update_page_content
    """
    key_map = {
        "Page Name": "Page_Name",
        "Meta Title (30 to 60 Characters)": "Meta_Title",
        "Meta Description (70 to 143 Characters)": "Meta_Description",
        "Hero Title (20 to 70 Characters)": "Hero_Title",
        "Hero Text (50 to 100 Characters)": "Hero_Text",
        "Hero CTA": "Hero_CTA",
        "Header": "Header",
        "Leading Sentence": "Leading_Sentence",
        "CTA Button": "CTA_Button",
        "Image Recommendations": "Image_Recommendations",
        "h2_sections": "h2_sections",
        "H1 (30 to 70 Characters)": "H1",
        "H1 Content": "H1_Content",
    }

    converted_page = {}
    for original_key, value in page_data.items():
        if original_key in key_map:
            converted_key = key_map[original_key]
            converted_page[converted_key] = value
        else:
            # Keep original key if no mapping found
            converted_page[original_key] = value

    logger.info(f"Converted page keys: {list(converted_page.keys())}")
    return converted_page


def extract_updated_page_from_response(response, current_set, current_page):
    """
    Extract the specific updated page from the full response structure
    """
    try:
        logger.info(f"=== EXTRACTION DEBUG ===")
        logger.info(
            f"Extracting page from response - Set: {current_set}, Page: {current_page}"
        )
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response is list: {isinstance(response, list)}")

        if isinstance(response, list) and len(response) > 0:
            logger.info(f"Response structure length: {len(response)}")

            # Log the structure of the first few elements
            for i, item in enumerate(response[:3]):
                if isinstance(item, dict) and "pages" in item:
                    pages_count = len(item["pages"])
                    if pages_count > 0:
                        page_name = item["pages"][0].get("Page Name", "Unknown")
                        logger.info(
                            f"Set {i}: {pages_count} page(s), first page: {page_name}"
                        )

            # The response structure appears to be: each set contains 1 page,
            # and the page index corresponds to the set index in the response
            page_index_as_set = current_page

            logger.info(f"Using page index {current_page} as set index in response")

            # Navigate to the specific page using page index as set index
            if page_index_as_set < len(response):
                set_data = response[page_index_as_set]
                logger.info(f"Set data type: {type(set_data)}")
                logger.info(
                    f"Set data keys: {list(set_data.keys()) if isinstance(set_data, dict) else 'Not a dict'}"
                )

                if isinstance(set_data, dict) and "pages" in set_data:
                    pages = set_data["pages"]
                    logger.info(f"Pages array length: {len(pages)}")

                    # Take the first (and likely only) page from this set
                    if len(pages) > 0:
                        updated_page = pages[0]
                        logger.info(
                            f"Found page with keys: {list(updated_page.keys()) if isinstance(updated_page, dict) else 'Not a dict'}"
                        )
                        logger.info(
                            f"Page Name: {updated_page.get('Page Name', 'No Page Name found')}"
                        )
                        logger.info(f"Successfully extracted updated page")
                        return updated_page
                    else:
                        logger.error(f"No pages found in set {page_index_as_set}")
                else:
                    logger.error(
                        f"Set data doesn't contain 'pages' key or is not a dict"
                    )
                    if isinstance(set_data, dict):
                        logger.error(
                            f"Available keys in set data: {list(set_data.keys())}"
                        )
            else:
                logger.error(
                    f"Page index {page_index_as_set} not found in response array of length {len(response)}"
                )
                # Log available sets for debugging
                for i, set_item in enumerate(response):
                    if isinstance(set_item, dict) and "pages" in set_item:
                        pages_count = len(set_item["pages"])
                        page_name = (
                            set_item["pages"][0].get("Page Name", "Unknown")
                            if pages_count > 0
                            else "No pages"
                        )
                        logger.error(
                            f"  Available set {i}: {pages_count} page(s) - {page_name}"
                        )
                    else:
                        logger.error(f"  Available set {i}: invalid structure")

        logger.error("Could not extract page from response structure")
        logger.info(f"=== END EXTRACTION DEBUG ===")
        return None
    except Exception as e:
        logger.error(f"Error extracting page from response: {str(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return None


@app.post("/api/ask-ai")
async def ask_ai(request: AIRequest):
    selected_text = request.selected_text
    user_question = request.user_question
    current_set = request.current_set
    current_page = request.current_page
    webpage_output = request.webpage_output
    payload_output = request.payload_output
    business_info_data = request.business_info

    def identify_content_section(selected_text, webpage_data):
        text_lower = selected_text.lower().strip()
        if webpage_data.get("Hero Title (20 to 70 Characters)"):
            if text_lower in webpage_data["Hero Title (20 to 70 Characters)"].lower():
                return "Hero Title"
        if webpage_data.get("Hero Text (50 to 100 Characters)"):
            if text_lower in webpage_data["Hero Text (50 to 100 Characters)"].lower():
                return "Hero Text"
        if webpage_data.get("Hero CTA"):
            if text_lower in webpage_data["Hero CTA"].lower():
                return "Hero CTA"
        if webpage_data.get("Meta Title (30 to 60 Characters)"):
            if text_lower in webpage_data["Meta Title (30 to 60 Characters)"].lower():
                return "Meta Title"
        if webpage_data.get("Meta Description (70 to 143 Characters)"):
            if (
                text_lower
                in webpage_data["Meta Description (70 to 143 Characters)"].lower()
            ):
                return "Meta Description"
        if webpage_data.get("H1 (30 to 70 Characters)"):
            if text_lower in webpage_data["H1 (30 to 70 Characters)"].lower():
                return "H1 Title"
        if webpage_data.get("H1 Content"):
            h1_content = webpage_data["H1 Content"]
            if isinstance(h1_content, list):
                h1_content = " ".join(h1_content)
            if text_lower in h1_content.lower():
                return "H1 Content"

        # Check H2 sections - handle both formats
        if webpage_data.get("h2_sections"):
            for i, section in enumerate(webpage_data["h2_sections"]):
                # Handle both "H2 Heading" and "H2_Heading" formats
                h2_heading = section.get("H2 Heading") or section.get("H2_Heading")
                if h2_heading and text_lower in h2_heading.lower():
                    return f"H2 Heading (Section {i + 1})"

                # Handle both "H2 Content" and "H2_Content" formats
                h2_content = section.get("H2 Content") or section.get("H2_Content")
                if h2_content:
                    if isinstance(h2_content, list):
                        h2_content = " ".join(h2_content)
                    if text_lower in h2_content.lower():
                        return f"H2 Content (Section {i + 1})"

        if webpage_data.get("CTA Button"):
            if text_lower in webpage_data["CTA Button"].lower():
                return "CTA Button"
        if webpage_data.get("Header"):
            if text_lower in webpage_data["Header"].lower():
                return "Header"
        if webpage_data.get("Leading Sentence"):
            if text_lower in webpage_data["Leading Sentence"].lower():
                return "Leading Sentence"
        if webpage_data.get("Image Recommendations"):
            for i, img_rec in enumerate(webpage_data["Image Recommendations"]):
                if text_lower in img_rec.lower():
                    return f"Image Recommendation {i + 1}"
        return "Unknown Section"

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

    update_keywords = ["update", "change", "modify", "edit", "replace", "rewrite"]
    is_update_request = True  # You can update this logic if needed

    if is_update_request and selected_text:
        try:
            payload_output = combined_data[current_set - 1]
            webpage_output_for_api = webpage_content_output_test_data[current_set - 1]

            # Fix the selected_text - remove the tuple wrapping
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

                # Extract the specific updated page from the full response
                updated_page = extract_updated_page_from_response(
                    response, current_set, current_page
                )

                if updated_page:
                    logger.info(
                        f"Successfully extracted updated page for Set {current_set}, Page {current_page}"
                    )

                    # Convert the page keys to the format expected by update_page_content
                    converted_page = convert_page_keys_for_update(updated_page)

                    logger.info(f"Original page keys: {list(updated_page.keys())}")
                    logger.info(f"Converted page keys: {list(converted_page.keys())}")
                    logger.info(
                        f"Page_Name in converted page: {converted_page.get('Page_Name', 'NOT FOUND')}"
                    )

                    return {
                        "success": True,
                        "response": "Page content has been updated successfully!",
                        "updated_content": [converted_page],  # Return converted page
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
