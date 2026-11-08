from typing import List, Optional
from pydantic import BaseModel, Field


class MedicaoItem(BaseModel):
    mnemonico: str
    valor: float


class MedicaoCreate(BaseModel):
    id_aparelho: int
    mnemonico: Optional[str] = None
    valor: Optional[float] = None
    medicoes: Optional[List[MedicaoItem]] = None


class ComandoCreate(BaseModel):
    id_aparelho: int
    comando: str
    setpoint: Optional[float] = Field(default=None, ge=16, le=30)
