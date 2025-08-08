from typing import Any


async def extract_key_info(payload_data, model_output, page_name) -> Any:
    page_name_lower = page_name.lower()

    # Find matching page in model_output (case-insensitive)
    main_output = None
    for i in model_output:
        page = i.get("pages", [{}])[0]
        if page.get("Page Name", "").lower() == page_name_lower:
            main_output = i["pages"]
            break

    # Find matching page in payload_data["pages"]
    left_panel = None
    for i in payload_data.get("pages", []):
        if i.get("title", "").lower() == page_name_lower:
            left_panel = i
            break

    # Guard for missing page
    if main_output is None or left_panel is None:
        raise ValueError(f"Page '{page_name}' not found in one of the inputs.")

    # Get optional keys safely
    if_copyright = left_panel.get("copy", "")
    business_info = {k: v for k, v in payload_data.items() if k.lower() != "pages"}

    return main_output, left_panel, if_copyright, business_info


def update_page_content(model_output, updated_pages):
    """
    Update the model_output with the updated page content.
    """
    # Flatten the incoming list if needed
    updated_page = updated_pages[0]
    updated_page_name = updated_page.get(
        "Page Name"
    )  # Fixed: use "Page Name" not "Page_Name"

    for outer_dict in model_output:
        for i, page in enumerate(outer_dict.get("pages", [])):
            if page.get("Page Name") == updated_page_name:
                # Update the page with new content, preserving structure
                for key, value in updated_page.items():
                    if value is not None:
                        page[key] = value
                return model_output

    return model_output


def remove_none_values(data):
    if isinstance(data, dict):
        return {k: remove_none_values(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [remove_none_values(item) for item in data]
    else:
        return data


def find_exact_field_name(page, section_name):
    """
    Find the exact field name in the page data with flexible matching.
    """
    # First try exact match
    if section_name in page:
        return section_name

    # Then try case-insensitive match
    for field_name in page.keys():
        if field_name.lower() == section_name.lower():
            return field_name

    # Handle special cases for fields with additional text in parentheses
    section_lower = section_name.lower()
    for field_name in page.keys():
        field_lower = field_name.lower()
        # Check if the section name is contained in the field name (for cases like "Meta Description" -> "Meta Description (70 to 143 Characters)")
        if section_lower in field_lower or field_lower.startswith(section_lower):
            return field_name

    return None


def update_page_data(pages_data, page_name, section_name, new_value):
    """
    Updates a specific field in the page data structure.
    Flexible field matching.
    """
    # Make a deep copy to avoid modifying the original data
    updated_data = [page.copy() for page in pages_data]

    # Find the page to update (case-insensitive)
    for page in updated_data:
        if page.get("Page Name", "").lower() == page_name.lower():
            # Handle nested updates for h2_sections
            if section_name.lower().startswith("h2_sections"):
                if "[" in section_name and "]" in section_name:
                    parts = section_name.split("[")[1].split("]")
                    index = int(parts[0])
                    field = parts[1].lstrip(".")

                    if "h2_sections" in page and index < len(page["h2_sections"]):
                        # Make deep copy of h2_sections
                        page["h2_sections"] = [
                            section.copy() for section in page["h2_sections"]
                        ]
                        exact_field = find_exact_field_name(
                            page["h2_sections"][index], field
                        )
                        if exact_field:
                            page["h2_sections"][index][exact_field] = new_value
                else:
                    exact_field = find_exact_field_name(page, section_name)
                    if exact_field:
                        page[exact_field] = new_value
            else:
                # Direct field update - find exact field name with flexible matching
                exact_field = find_exact_field_name(page, section_name)
                if exact_field:
                    page[exact_field] = new_value
                    print(f"✓ Updated field '{exact_field}' with value: {new_value}")
                else:
                    print(
                        f"⚠️  Could not find field for section: '{section_name}' in page '{page_name}'"
                    )
                    print(f"Available fields: {list(page.keys())}")
            break

    return updated_data


def update_h2_section_content(
    pages_data, page_name, section_index, field_name, new_value
):
    """
    Specialized function to update h2_sections content more easily.
    Case-insensitive matching.
    """
    updated_data = [page.copy() for page in pages_data]

    # Find the page to update (case-insensitive)
    for page in updated_data:
        if page.get("Page Name", "").lower() == page_name.lower():
            if "h2_sections" in page and section_index < len(page["h2_sections"]):
                # Make deep copy of h2_sections
                page["h2_sections"] = [
                    section.copy() for section in page["h2_sections"]
                ]
                exact_field = find_exact_field_name(
                    page["h2_sections"][section_index], field_name
                )
                if exact_field:
                    page["h2_sections"][section_index][exact_field] = new_value
            break

    return updated_data


def process_response_updates(pages_data, response, page_name=None):
    """
    Process an array of updates from a response and apply them to the page data.

    Args:
        pages_data (list): List of page dictionaries
        response (list): List of update dictionaries with 'updated_text', 'index', 'section'
        page_name (str, optional): Name of the page to update. If None, uses first page

    Returns:
        list: Updated pages data structure
    """
    # Handle the case where pages_data might be a single dict instead of a list
    if isinstance(pages_data, dict):
        pages_data = [pages_data]

    updated_data = pages_data

    # If no page_name provided, use the first page
    if page_name is None:
        if len(pages_data) > 0:
            page_name = pages_data[0].get("Page Name", "Unknown")
            print(f"ℹ️  No page name specified. Using first page: '{page_name}'")

    print(f"Processing {len(response)} updates for page: '{page_name}'")

    for update in response:
        updated_text = update.get("updated_text")
        index = update.get("index")
        section = update.get("section")

        print(f"Processing update: section='{section}', index={index}")

        if section == "H2 Content":
            # Update h2 section content using the index
            updated_data = update_h2_section_content(
                updated_data, page_name, index, "H2 Content", updated_text
            )
            print(f"✓ Updated H2 Content at index {index}")

        elif section == "H2 Heading":
            # Update h2 section heading using the index
            updated_data = update_h2_section_content(
                updated_data, page_name, index, "H2 Heading", updated_text
            )
            print(f"✓ Updated H2 Heading at index {index}")

        else:
            # For other sections, use the section name directly with flexible matching
            updated_data = update_page_data(
                updated_data, page_name, section, updated_text
            )
            print(f"✓ Processed update for section: {section}")

    return updated_data


"""
Utility functions for handling suggestion selection and application
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def create_updated_content_from_selection(
    original_content: Dict[str, Any], selection: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create updated content by applying a selected suggestion to the original content

    Args:
        original_content: The original webpage content
        selection: The selected suggestion containing section and selected_output

    Returns:
        Updated content with the selection applied
    """
    try:
        # Create a copy to avoid modifying the original
        updated_content = original_content.copy()

        section = selection.get("section", "")
        selected_output = selection.get("selected_output", "")

        logger.info(f"Applying selection: {section} -> {selected_output}")

        # Map section names to actual field names in the content
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
            "Image Recommendations": "Image Recommendations",
        }

        # Get the correct field name
        field_name = section_field_mapping.get(section, section)

        # Apply the selection
        if field_name in updated_content:
            updated_content[field_name] = selected_output
            logger.info(f"Successfully updated {field_name}")
        elif section.startswith("H2") and "h2_sections" in updated_content:
            # Handle H2 sections
            updated_content = handle_h2_section_update(
                updated_content, section, selected_output
            )
        else:
            logger.warning(f"Field {field_name} not found in content")
            # Try direct mapping as fallback
            updated_content[section] = selected_output

        return updated_content

    except Exception as e:
        logger.error(f"Error creating updated content from selection: {str(e)}")
        raise


def handle_h2_section_update(
    content: Dict[str, Any], section: str, selected_output: str
) -> Dict[str, Any]:
    """
    Handle updates to H2 sections specifically

    Args:
        content: The original content
        section: The H2 section identifier
        selected_output: The new content for the section

    Returns:
        Updated content with H2 section modified
    """
    try:
        # Parse the section identifier to find which H2 section and field
        # Example: "H2 Section 1 Heading" or "H2 Section 2 Content"
        if "h2_sections" not in content or not isinstance(content["h2_sections"], list):
            logger.warning("No h2_sections found in content")
            return content

        # Extract section number and field type from section string
        import re

        match = re.search(r"H2.*?(\d+).*?(Heading|Content)", section)

        if match:
            section_index = int(match.group(1)) - 1  # Convert to 0-based index
            field_type = match.group(2)

            if 0 <= section_index < len(content["h2_sections"]):
                h2_section = content["h2_sections"][section_index]

                if field_type == "Heading":
                    # Update heading
                    if "H2 Heading" in h2_section:
                        h2_section["H2 Heading"] = selected_output
                    elif "H2_Heading" in h2_section:
                        h2_section["H2_Heading"] = selected_output
                elif field_type == "Content":
                    # Update content
                    if "H2 Content" in h2_section:
                        h2_section["H2 Content"] = selected_output
                    elif "H2_Content" in h2_section:
                        h2_section["H2_Content"] = selected_output

                logger.info(f"Updated H2 section {section_index + 1} {field_type}")
            else:
                logger.warning(f"H2 section index {section_index} out of range")
        else:
            logger.warning(f"Could not parse H2 section identifier: {section}")

    except Exception as e:
        logger.error(f"Error handling H2 section update: {str(e)}")

    return content


def validate_suggestion_structure(suggestions: List[Dict]) -> bool:
    """
    Validate that the suggestions have the expected structure

    Args:
        suggestions: List of suggestion dictionaries

    Returns:
        True if valid, False otherwise
    """
    try:
        if not isinstance(suggestions, list) or len(suggestions) == 0:
            return False

        for suggestion in suggestions:
            if not isinstance(suggestion, dict):
                return False

            required_fields = ["outputs_list", "section"]
            for field in required_fields:
                if field not in suggestion:
                    logger.warning(f"Missing required field: {field}")
                    return False

            # Validate outputs_list
            outputs_list = suggestion.get("outputs_list", [])
            if not isinstance(outputs_list, list) or len(outputs_list) == 0:
                logger.warning("Invalid or empty outputs_list")
                return False

            # Validate that we have exactly 3 outputs
            if len(outputs_list) != 3:
                logger.warning(f"Expected 3 outputs, got {len(outputs_list)}")
                return False

        return True

    except Exception as e:
        logger.error(f"Error validating suggestion structure: {str(e)}")
        return False


def format_suggestions_for_frontend(suggestions: List[Dict]) -> List[Dict]:
    """
    Format suggestions for optimal frontend display

    Args:
        suggestions: Raw suggestions from the AI model

    Returns:
        Formatted suggestions ready for frontend
    """
    formatted_suggestions = []

    try:
        for suggestion in suggestions:
            formatted_suggestion = {
                "outputs_list": suggestion.get("outputs_list", []),
                "index": suggestion.get("index", 0),
                "section": suggestion.get("section", ""),
                "original_text": suggestion.get("original_text", ""),
                # Add display-friendly section name
                "display_section": format_section_name_for_display(
                    suggestion.get("section", "")
                ),
                # Add metadata for tracking
                "suggestion_id": f"{suggestion.get('section', '')}_{suggestion.get('index', 0)}",
            }
            formatted_suggestions.append(formatted_suggestion)

        logger.info(f"Formatted {len(formatted_suggestions)} suggestions for frontend")
        return formatted_suggestions

    except Exception as e:
        logger.error(f"Error formatting suggestions for frontend: {str(e)}")
        return suggestions  # Return original if formatting fails


def format_section_name_for_display(section: str) -> str:
    """
    Convert technical section names to user-friendly display names

    Args:
        section: Technical section name

    Returns:
        User-friendly display name
    """
    display_mapping = {
        "Meta Title": "Page Meta Title",
        "Meta Description": "Page Meta Description",
        "Hero Title": "Hero Section Title",
        "Hero Text": "Hero Section Text",
        "Hero CTA": "Hero Call-to-Action",
        "H1": "Main Page Heading",
        "H1 Content": "Main Page Content",
        "Header": "Page Header",
        "Leading Sentence": "Leading Sentence",
        "CTA Button": "Call-to-Action Button",
    }

    return display_mapping.get(section, section)


def log_suggestion_analytics(suggestions: List[Dict], selected_suggestion: Dict = None):
    """
    Log analytics data for suggestion usage

    Args:
        suggestions: All suggestions provided
        selected_suggestion: The suggestion that was selected (if any)
    """
    try:
        logger.info("=" * 60)
        logger.info("SUGGESTION ANALYTICS:")
        logger.info(f"Total suggestions provided: {len(suggestions)}")

        for i, suggestion in enumerate(suggestions):
            section = suggestion.get("section", "Unknown")
            num_outputs = len(suggestion.get("outputs_list", []))
            logger.info(f"Suggestion {i + 1}: {section} with {num_outputs} options")

        if selected_suggestion:
            logger.info(
                f"User selected: {selected_suggestion.get('section')} - {selected_suggestion.get('selected_output', '')[:50]}..."
            )
        else:
            logger.info("No suggestion was selected")

        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error logging suggestion analytics: {str(e)}")
