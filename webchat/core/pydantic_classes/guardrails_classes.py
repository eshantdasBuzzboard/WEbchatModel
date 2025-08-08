from pydantic import BaseModel, Field
from typing import List, Union


class QueryValidator(BaseModel):
    score: int = Field(
        ..., description="Score 0 if query is invalid and 1 if it is valid"
    )
    reason: str = Field(
        default="",
        description=' Empty string ""  if score is 1 and query is valid and enter a proper reason why if the query is invalid and score is 0',
    )


class H2Section(BaseModel):
    H2_Heading: str = Field(..., alias="H2 Heading")
    H2_Content: Union[str, List[str]] = Field(..., alias="H2 Content")


class Page(BaseModel):
    Page_Name: str = Field(..., alias="Page Name")
    Meta_Title: str = Field(..., alias="Meta Title (30 to 60 Characters)")
    Meta_Description: str = Field(..., alias="Meta Description (70 to 143 Characters)")
    Hero_Title: Union[str, None] = Field(None, alias="Hero Title (20 to 70 Characters)")
    Hero_Text: Union[str, None] = Field(None, alias="Hero Text (50 to 100 Characters)")
    Hero_CTA: Union[str, None] = Field(None, alias="Hero CTA")
    H1: Union[str, None] = Field(None, alias="H1 (30 to 70 Characters)")
    H1_Content: Union[str, None] = Field(None, alias="H1 Content")
    h2_sections: Union[List[H2Section], None] = Field(None, alias="h2_sections")
    Header: Union[str, None] = Field(None, alias="Header")
    Leading_Sentence: Union[str, None] = Field(None, alias="Leading Sentence")
    CTA_Button: Union[str, None] = Field(None, alias="CTA Button")
    Image_Recommendations: List[str] = Field(
        default=None, alias="Image Recommendations"
    )


class SuggestedOutputs(BaseModel):
    outputs_list: list[str] = Field(
        ...,
        description="List of three suggested outputs which you are supposed to change",
    )
    index: int = Field(
        default=None, description="The index only if they asked to update h2 content"
    )
    section: str = Field(..., description="The section name which is getting updated")
