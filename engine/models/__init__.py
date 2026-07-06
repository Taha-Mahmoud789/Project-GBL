from pydantic import BaseModel, Field
from typing import Optional


class AnalyzeRequest(BaseModel):
    svg_content: str = Field(..., description="Raw SVG string")
    file_name: Optional[str] = "input.svg"


class AnalyzeResponse(BaseModel):
    type: str
    layers: int = 0
    shapes: int = 0
    colors: list[str] = []
    warnings: list[str] = []
    recommended_engine: str


class ConversionSettings(BaseModel):
    depth: float = 0.5
    bevel: float = 0.05
    smoothness: int = 5
    mode: str = "auto"


class MaterialSettings(BaseModel):
    color: str = "#6366f1"
    metalness: float = 0.2
    roughness: float = 0.3


class ConvertRequest(BaseModel):
    svg_content: str
    file_name: Optional[str] = "input.svg"
    settings: Optional[ConversionSettings] = None
    material: Optional[MaterialSettings] = None


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float = 0.0
    message: str = ""


class ProgressEvent(BaseModel):
    task_id: str
    progress: float
    message: str
