from sqlmodel import SQLModel, Field
from datetime import date

class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    position: str
    team: str
    market_value_usd: float
    passes: int
    pass_accuracy: float
    shots: int
    shots_on_target: int
    saves: int
    fouls: int
    yellow_cards: int
    red_cards: int

class PlayerDimension(SQLModel, table=True):
    player_id: int = Field(default=None, primary_key=True)
    name: str
    position: str
    team: str


class PerformanceDimension(SQLModel, table=True):
    performance_id: int = Field(default=None, primary_key=True)
    passes: int
    pass_accuracy: float
    shots: int
    shots_on_target: int
    saves: int


class DisciplineDimension(SQLModel, table=True):
    discipline_id: int = Field(default=None, primary_key=True)
    fouls: int
    yellow_cards: int
    red_cards: int


class ValueDimension(SQLModel, table=True):
    value_id: int = Field(default=None, primary_key=True)
    market_value_usd: float
    exchange_rate: float
    market_value_ars: float


class DateDimension(SQLModel, table=True):
    date_id: int = Field(default=None, primary_key=True)
    date: date
    day_of_week: str
    month: str
    year: int


class FactPlayerPerformance(SQLModel, table=True):
    fact_id: int = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="playerdimension.player_id")
    performance_id: int = Field(foreign_key="performancedimension.performance_id")
    discipline_id: int = Field(foreign_key="disciplinedimension.discipline_id")
    value_id: int = Field(foreign_key="valuedimension.value_id")
    date_id: int = Field(foreign_key="datedimension.date_id")

    composite_score: float
    ranking: int
