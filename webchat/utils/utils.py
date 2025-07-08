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
    # Flatten the incoming list if needed
    updated_page = updated_pages[0]
    updated_page_name = updated_page.get("Page_Name")

    for outer_dict in model_output:
        for i, page in enumerate(outer_dict.get("pages", [])):
            if page.get("Page Name") == updated_page_name:
                # Replace the old page with the updated one (keys adapted to original format)
                new_page = {}

                # Convert keys to match original naming in model_output (like "Meta Title (...)")
                key_map = {
                    "Page_Name": "Page Name",
                    "Meta_Title": "Meta Title (30 to 60 Characters)",
                    "Meta_Description": "Meta Description (70 to 143 Characters)",
                    "Hero_Title": "Hero Title (20 to 70 Characters)",
                    "Hero_Text": "Hero Text (50 to 100 Characters)",
                    "Hero_CTA": "Hero CTA",
                    "Header": "Header",
                    "Leading_Sentence": "Leading Sentence",
                    "CTA_Button": "CTA Button",
                    "Image_Recommendations": "Image Recommendations",
                    "h2_sections": "h2_sections",
                    "H1": "H1 (30 to 70 Characters)",
                    "H1_Content": "H1 Content",
                }

                for k, v in updated_page.items():
                    if v is not None and k in key_map:
                        new_page[key_map[k]] = v

                # Replace the page in the original structure
                outer_dict["pages"][i] = new_page
                return model_output  # early exit after updating

    return model_output  # no match found


def remove_none_values(data):
    if isinstance(data, dict):
        return {k: remove_none_values(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [remove_none_values(item) for item in data]
    else:
        return data
