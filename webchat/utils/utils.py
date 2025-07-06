from typing import Any


async def extract_key_info(payload_data, model_output, page_name) -> Any:
    for i in model_output:
        if i["pages"][0]["Page Name"] == page_name:
            main_output = i["pages"]

    for i in payload_data["pages"]:
        if i["title"] == page_name:
            left_panel = i

    if_copyright = left_panel["copy"]
    business_info = {k: v for k, v in payload_data.items() if k != "pages"}
    return main_output, left_panel, if_copyright, business_info
