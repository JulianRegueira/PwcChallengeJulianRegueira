import pandas as pd
from datetime import datetime, date
from sqlmodel import SQLModel, Field, create_engine, Session, select, text
from typing import List
import requests

from app.data_access.models import (
    PlayerRepository,
    PlayerDimension,
    PerformanceDimension,
    DisciplineDimension,
    ValueDimension,
    DateDimension,
    FactPlayerPerformance,
    FactPlayerPerformanceRepository
)

# Engines
silver_engine = create_engine("sqlite:///silver.db")
gold_engine = create_engine("sqlite:///gold.db")

# Repositories
player_repo = PlayerRepository(silver_engine)
fact_repo = FactPlayerPerformanceRepository(gold_engine)

# Get exchange rate from Dolarapi
def get_usd_to_ars_rate() -> float:
    try:
        response = requests.get("https://dolarapi.com/v1/dolares/blue")
        response.raise_for_status()
        return float(response.json()["venta"])
    except Exception as e:
        print(f"⚠️ Dolarapi fetch failed: {e}. Using fallback rate.")
        return 1000.0  # fallback value

# Build dimension tables from raw data

def build_dimensions(players: List) -> List[List]:
    exchange_rate = get_usd_to_ars_rate()
    dims = {
        "players": [],
        "performances": [],
        "disciplines": [],
        "values": [],
        "dates": []
    }

    # Build players, performance, discipline, value dims
    for p in players:
        dims["players"].append(PlayerDimension(
            player_id=p.id,
            name=p.name,
            position=p.position,
            team=p.team
        ))
        dims["performances"].append(PerformanceDimension(
            performance_id=p.id,
            passes=p.passes,
            pass_accuracy=p.pass_accuracy,
            shots=p.shots,
            shots_on_target=p.shots_on_target,
            saves=p.saves
        ))
        dims["disciplines"].append(DisciplineDimension(
            discipline_id=p.id,
            fouls=p.fouls,
            yellow_cards=p.yellow_cards,
            red_cards=p.red_cards
        ))
        dims["values"].append(ValueDimension(
            value_id=p.id,
            market_value_usd=p.market_value_usd,
            exchange_rate=exchange_rate,
            market_value_ars=p.market_value_usd * exchange_rate
        ))

    # Build date dim once
    today = datetime.today()
    dims["dates"] = [DateDimension(
        date_id=1,
        date=today.date(),
        day_of_week=today.strftime("%A"),
        month=today.strftime("%B"),
        year=today.year
    )]

    return dims["players"], dims["performances"], dims["disciplines"], dims["values"], dims["dates"]

# Build fact table

def build_facts(players: List) -> List[FactPlayerPerformance]:
    facts: List[FactPlayerPerformance] = []
    for index, p in enumerate(players):
        score = (p.pass_accuracy * 0.4 + p.shots_on_target * 0.3 + p.saves * 0.3)
        facts.append(FactPlayerPerformance(
            player_id=p.id,
            performance_id=p.id,
            discipline_id=p.id,
            value_id=p.id,
            date_id=1,
            composite_score=score,
            ranking=index + 1
        ))
    return facts

# Main ETL process
def main():
    # Read players via repository
    players = player_repo.list_all()

    # Build dimensions and facts
    players_dim, perf_dim, disc_dim, val_dim, date_dim = build_dimensions(players)
    facts = build_facts(players)

    # Create Gold schema
    SQLModel.metadata.create_all(gold_engine)

    # Persist dims & facts via repository
    # Bulk insertion
    with Session(gold_engine) as session:
        session.add_all(players_dim + perf_dim + disc_dim + val_dim + date_dim)
        session.add_all(facts)
        session.commit()

    print("✅ Silver → Gold ETL complete!")

def create_top_players_view(engine):
    with Session(engine) as sess:
        # 1) Delete old contents
        sess.exec(text("DELETE FROM topplayers"))
        # 2) Insert fresh top-10
        insert_sql = """
        INSERT INTO topplayers (rank, player_id, name, team, composite_score)
        SELECT row_number() OVER (ORDER BY composite_score DESC) as rank,
               pd.player_id,
               pd.name,
               pd.team,
               f.composite_score
        FROM factplayerperformance f
        JOIN playerdimension pd
          ON f.player_id = pd.player_id
        ORDER BY f.composite_score DESC
        LIMIT 10;
        """
        sess.exec(text(insert_sql))
        sess.commit()

if __name__ == "__main__":
    main()
