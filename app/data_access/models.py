from sqlmodel import SQLModel, Field, Session, select
from datetime import date
from typing import List, Optional

# Domain and ORM models
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

# Define a “view” table
class TopPlayers(SQLModel, table=True):
    rank: int = Field(default=None, primary_key=True)
    player_id: int
    name: str
    team: str
    composite_score: float
    
class FactPlayerPerformance(SQLModel, table=True):
    fact_id: int = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="playerdimension.player_id")
    performance_id: int = Field(foreign_key="performancedimension.performance_id")
    discipline_id: int = Field(foreign_key="disciplinedimension.discipline_id")
    value_id: int = Field(foreign_key="valuedimension.value_id")
    date_id: int = Field(foreign_key="datedimension.date_id")
    composite_score: float
    ranking: int


# Repository Pattern for data access
class PlayerRepository:
    def __init__(self, engine):
        self.engine = engine

    def list_all(self) -> List[Player]:
        with Session(self.engine) as session:
            return session.exec(select(Player)).all()

    def get_by_id(self, player_id: int) -> Optional[Player]:
        with Session(self.engine) as session:
            return session.get(Player, player_id)

    def create_batch(self, players: List[Player]) -> None:
        with Session(self.engine) as session:
            session.add_all(players)
            session.commit()

    def delete(self, player_id: int) -> None:
        with Session(self.engine) as session:
            player = session.get(Player, player_id)
            if player:
                session.delete(player)
                session.commit()

class FactPlayerPerformanceRepository:
    def __init__(self, engine):
        self.engine = engine

    def list_top_by_score(self, limit: int = 10) -> List[FactPlayerPerformance]:
        with Session(self.engine) as session:
            statement = select(FactPlayerPerformance).order_by(FactPlayerPerformance.composite_score.desc()).limit(limit)
            return session.exec(statement).all()

    def create_batch(self, facts: List[FactPlayerPerformance]) -> None:
        with Session(self.engine) as session:
            session.add_all(facts)
            session.commit()
