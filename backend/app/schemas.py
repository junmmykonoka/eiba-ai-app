from pydantic import BaseModel
from typing import List, Optional

class EntryBase(BaseModel):
    bracket_number: int
    horse_number: int
    horse_name: str
    horse_id: Optional[str] = None
    sex_age: str
    jockey_name: str
    jockey_id: Optional[str] = None
    impost: float
    trainer_name: str
    trainer_id: Optional[str] = None
    horse_weight: Optional[int] = None
    weight_diff: Optional[int] = None
    odds: Optional[float] = None
    popularity: Optional[int] = None
    ai_pred_score: Optional[float] = None
    ai_pred_rank: Optional[int] = None

class EntryCreate(EntryBase):
    pass

class EntryResponse(EntryBase):
    id: int
    race_id: str

    class Config:
        from_attributes = True

class RaceBase(BaseModel):
    id: str
    race_name: str
    race_number: int
    race_date: str
    course: str
    track_type: str = "芝"
    distance: int = 2000
    weather: str = "晴"
    track_condition: str = "良"
    start_time: str = "15:00"
    race_class: str = "オープン"

class RaceCreate(RaceBase):
    entries: List[EntryCreate] = []

class RaceSummaryResponse(RaceBase):
    entry_count: Optional[int] = 0

    class Config:
        from_attributes = True

class RaceDetailResponse(RaceBase):
    entries: List[EntryResponse] = []

    class Config:
        from_attributes = True

class ScrapeRequest(BaseModel):
    url_or_date: str
