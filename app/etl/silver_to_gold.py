import pandas as pd
from datetime import datetime, date
from sqlmodel import Session, create_engine, SQLModel
from app.data_access.models import (
    PlayerDimension, PerformanceDimension, DisciplineDimension,
    ValueDimension, DateDimension, FactPlayerPerformance
)
import requests

# Engines
silver_engine = create_engine("sqlite:///silver.db")
gold_engine = create_engine("sqlite:///gold.db")

# Get exchange rate from Dolarapi
def get_usd_to_ars_rate() -> float:
    try:
        response = requests.get("https://dolarapi.com/v1/dolares/blue")
        response.raise_for_status()
        return float(response.json()["venta"])
    except Exception:
        return 1000.0  # fallback value

# Build dimension tables from raw data
def build_dimensions(df: pd.DataFrame, exchange_rate: float):
    players, performances, disciplines, values = [], [], [], []
    for index, row in df.iterrows():
        players.append(PlayerDimension(
            player_id=row.id,
            name=row.name,
            position=row.position,
            team=row.team
        ))

        performances.append(PerformanceDimension(
            performance_id=row.id,
            passes=row.passes,
            pass_accuracy=row.pass_accuracy,
            shots=row.shots,
            shots_on_target=row.shots_on_target,
            saves=row.saves
        ))

        disciplines.append(DisciplineDimension(
            discipline_id=row.id,
            fouls=row.fouls,
            yellow_cards=row.yellow_cards,
            red_cards=row.red_cards
        ))

        values.append(ValueDimension(
            value_id=row.id,
            market_value_usd=row.market_value_usd,
            exchange_rate=exchange_rate,
            market_value_ars=row.market_value_usd * exchange_rate
        ))

    today = datetime.today()
    date_dim = [DateDimension(
        date_id=1,
        date=today.date(),
        day_of_week=today.strftime("%A"),
        month=today.strftime("%B"),
        year=today.year
    )]

    return players, performances, disciplines, values, date_dim

# Build fact table

def build_facts(df: pd.DataFrame) -> list[FactPlayerPerformance]:
    facts = []
    for index, row in df.iterrows():
        score = (row.pass_accuracy * 0.4 + row.shots_on_target * 0.3 + row.saves * 0.3)
        facts.append(FactPlayerPerformance(
            player_id=row.id,
            performance_id=row.id,
            discipline_id=row.id,
            value_id=row.id,
            date_id=1,
            composite_score=score,
            ranking=index + 1
        ))
    return facts

# Main ETL process
def main():
    # Read silver data
    df = pd.read_sql("SELECT * FROM playerdimension", silver_engine)

    # Get exchange rate
    rate = get_usd_to_ars_rate()

    # Build dimensions
    players, performances, disciplines, values, date_dim = build_dimensions(df, rate)

    # Create schema
    SQLModel.metadata.create_all(gold_engine)

    # Insert all into gold DB
    with Session(gold_engine) as session:
        session.add_all(players + performances + disciplines + values + date_dim)
        session.add_all(build_facts(df))
        session.commit()

    print("✅ Silver → Gold ETL complete!")

if __name__ == "__main__":
    main()