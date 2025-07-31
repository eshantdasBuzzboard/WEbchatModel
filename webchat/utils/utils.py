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
