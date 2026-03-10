from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


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
    members_count: int

    class Config:
        from_attributes = True


class AchievementResponse(BaseModel):
    code: str
    name: str
    description: str
    icon: Optional[str] = None
    unlocked_at: Optional[datetime] = None
