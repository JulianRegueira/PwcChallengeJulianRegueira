# app/api/players.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, select, create_engine
from typing import List
import requests, os

from app.data_access.models import (
    Player,                    # <— raw Silver model
    FactPlayerPerformance      # <— Gold fact
)

security = HTTPBasic()
VALID_USER = os.getenv("API_USER", "admin")
VALID_PASS = os.getenv("API_PASS", "secret")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == VALID_USER and credentials.password == VALID_PASS):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

router = APIRouter(prefix="/players", tags=["players"], dependencies=[Depends(authenticate)])

silver_engine = create_engine("sqlite:///silver.db", connect_args={"check_same_thread": False})
gold_engine   = create_engine("sqlite:///gold.db",   connect_args={"check_same_thread": False})

@router.get("/", response_model=List[Player])
def list_players():
    """List all players from the Silver layer."""
    with Session(silver_engine) as session:
        players = session.exec(select(Player)).all()
    return players

@router.get("/{player_id}/price-ars")
def get_price_in_ars(player_id: int):
    """Return a player's market value in ARS using Dolarapi."""
    with Session(silver_engine) as session:
        player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    try:
        res = requests.get("https://dolarapi.com/v1/dolares/blue")
        res.raise_for_status()
        rate = float(res.json()["venta"])
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch exchange rate")

    return {
        "player_id": player_id,
        "market_value_usd": player.market_value_usd,
        "exchange_rate": rate,
        "market_value_ars": round(player.market_value_usd * rate, 2)
    }

@router.get("/ranking", response_model=List[FactPlayerPerformance])
def get_ranking(limit: int = 10):
    """Return top N players by composite score from the Gold layer."""
    with Session(gold_engine) as session:
        statement = select(FactPlayerPerformance).order_by(FactPlayerPerformance.composite_score.desc()).limit(limit)
        facts = session.exec(statement).all()
    return facts
