import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

MAX_TRIP_DAYS = 5


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    token: str
    email: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TripCreate(BaseModel):
    city: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date
    budget: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(default_factory=list, max_length=10)
    must_visit: list[str] = Field(default_factory=list, max_length=5)
    avoid: list[str] = Field(default_factory=list, max_length=5)
    pace: str = Field(default="normal", pattern="^(relaxed|normal|intense)$")
    language: str = Field(default="en", pattern="^(az|en)$")

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date start_date-dən əvvəl ola bilməz")
        if (self.end_date - self.start_date).days + 1 > MAX_TRIP_DAYS:
            raise ValueError(f"Maksimum {MAX_TRIP_DAYS} günlük səyahət dəstəklənir")
        # Yer/maraq siyahıları: boşları at, hər adı 80 simvola kəs (POI kateqoriya axtarışı client
        # təmizliyindən asılı qalmasın)
        self.must_visit = [s.strip()[:80] for s in self.must_visit if s and s.strip()]
        self.avoid = [s.strip()[:80] for s in self.avoid if s and s.strip()]
        self.interests = [s.strip()[:80] for s in self.interests if s and s.strip()]
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


class ItineraryDayUpdate(BaseModel):
    day: int = Field(ge=1)
    items: list[str] = Field(max_length=10)


class ItineraryUpdate(BaseModel):
    days: list[ItineraryDayUpdate] = Field(min_length=1, max_length=10)


class ItineraryOut(BaseModel):
    days: list
    total_cost: float
    lodging: dict | None = None

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
    must_visit: list | None = None
    avoid: list | None = None
    pace: str = "normal"
    language: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ShareOut(BaseModel):
    token: str


class TripDetail(TripOut):
    messages: list[AgentMessageOut] = []
    itinerary: ItineraryOut | None = None
