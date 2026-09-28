from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    text_lines: List[str] = Field(..., min_length=1, description="Body paragraphs, wrapped and paginated automatically.")
    template: str = "note"
    tab_text: Optional[str] = None
    tab_fill_color: Optional[str] = Field(None, description="Hex color, e.g. #FFF0E9")
    tab_text_color: Optional[str] = Field(None, description="Hex color, e.g. #D38200")
    tab_font: Optional[str] = None
    body_font: Optional[str] = None
