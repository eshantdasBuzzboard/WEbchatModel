import logging
import traceback

logger = logging.getLogger(__name__)


def convert_page_keys_for_update(page_data):
    """Convert page keys from display format to API format"""
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
            converted_page[original_key] = value

    logger.info(f"Converted page keys: {list(converted_page.keys())}")
    return converted_page


def extract_updated_page_from_response(response, current_set, current_page):
    """Extract updated page content from API response"""
    try:
        logger.info(f"=== EXTRACTION DEBUG ===")
        logger.info(
            f"Extracting page from response - Set: {current_set}, Page: {current_page}"
        )
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response is list: {isinstance(response, list)}")

        if isinstance(response, list) and len(response) > 0:
            logger.info(f"Response structure length: {len(response)}")

            for i, item in enumerate(response[:3]):
                if isinstance(item, dict) and "pages" in item:
                    pages_count = len(item["pages"])
                    if pages_count > 0:
                        page_name = item["pages"][0].get("Page Name", "Unknown")
                        logger.info(
                            f"Set {i}: {pages_count} page(s), first page: {page_name}"
                        )

            page_index_as_set = current_page

            logger.info(f"Using page index {current_page} as set index in response")

            if page_index_as_set < len(response):
                set_data = response[page_index_as_set]
                logger.info(f"Set data type: {type(set_data)}")
                logger.info(
                    f"Set data keys: {list(set_data.keys()) if isinstance(set_data, dict) else 'Not a dict'}"
                )

                if isinstance(set_data, dict) and "pages" in set_data:
                    pages = set_data["pages"]
                    logger.info(f"Pages array length: {len(pages)}")

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


def identify_content_section(selected_text, webpage_data):
    """Identify which content section the selected text belongs to"""
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

    if webpage_data.get("h2_sections"):
        for i, section in enumerate(webpage_data["h2_sections"]):
            h2_heading = section.get("H2 Heading") or section.get("H2_Heading")
            if h2_heading and text_lower in h2_heading.lower():
                return f"H2 Heading (Section {i + 1})"

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
