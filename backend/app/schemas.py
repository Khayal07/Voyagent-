import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

MAX_TRIP_DAYS = 5


class TripCreate(BaseModel):
    city: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date
    budget: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(default_factory=list, max_length=10)
    language: str = Field(default="en", pattern="^(az|en)$")

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date start_date-dən əvvəl ola bilməz")
        if (self.end_date - self.start_date).days + 1 > MAX_TRIP_DAYS:
            raise ValueError(f"Maksimum {MAX_TRIP_DAYS} günlük səyahət dəstəklənir")
        return self


class AgentMessageOut(BaseModel):
    id: int
    agent: str
    round: int
    role: str
    content: str
    payload: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ItineraryOut(BaseModel):
    days: list
    total_cost: float

    model_config = {"from_attributes": True}


class TripOut(BaseModel):
    id: uuid.UUID
    city: str
    start_date: date
    end_date: date
    budget: float
    currency: str
    travelers: int
    interests: list
    language: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TripDetail(TripOut):
    messages: list[AgentMessageOut] = []
    itinerary: ItineraryOut | None = None
