from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class FinishMethodResponse(BaseModel):
    id: UUID
    code: str
    name: str
    name_pt: Optional[str] = None
    category: str
    requires_round: bool
    requires_scorecard: bool

    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    id: UUID
    user_id: UUID
    fight_id: UUID
    event_id: UUID
    predicted_winner_id: Optional[UUID] = None
    predicted_method_id: Optional[UUID] = None
    predicted_round: Optional[int] = None
    is_winner_correct: Optional[bool] = None
    is_method_correct: Optional[bool] = None
    is_round_correct: Optional[bool] = None
    points_earned: int = 0
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    user_id: UUID
    username: str
    total_points: int
    correct_winners: int
    rank: Optional[int] = None


class UserStatsResponse(BaseModel):
    total_points: int
    total_predictions: int
    correct_winners: int
    underdog_bonus_points: int
    global_rank: Optional[int] = None
    current_streak: int
    best_streak: int
    events_participated: int


class LeagueResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    invite_code: str
    owner_id: UUID
    members_count: int = 0
    active_event_id: Optional[UUID] = None
    active_event_name: Optional[str] = None

    class Config:
        from_attributes = True


class LeagueDetailResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    invite_code: str
    owner_id: UUID
    owner_name: str = ""
    members_count: int = 0
    is_owner: bool = False
    is_member: bool = False
    active_event_id: Optional[UUID] = None
    active_event_name: Optional[str] = None
    active_event_date: Optional[str] = None
    active_event_fights_count: int = 0
    active_event_status: Optional[str] = None
    active_event_winner_name: Optional[str] = None
    active_event_winner_points: int = 0

    class Config:
        from_attributes = True


class LeagueLeaderboardEntry(BaseModel):
    user_id: UUID
    username: str
    total_points: int
    rank: Optional[int] = None


class LeagueEventLeaderboardEntry(BaseModel):
    user_id: UUID
    username: str
    total_points: int
    total_predictions: int = 0
    correct_winners: int = 0
    rank: Optional[int] = None


class LeaguePredictionResponse(BaseModel):
    id: UUID
    fight_id: UUID
    fighter1_name: Optional[str] = None
    fighter2_name: Optional[str] = None
    predicted_winner_id: Optional[UUID] = None
    predicted_winner_name: Optional[str] = None
    is_correct: Optional[bool] = None
    points_earned: int = 0


class AchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str
    icon: Optional[str] = None
    unlocked_at: Optional[datetime] = None
