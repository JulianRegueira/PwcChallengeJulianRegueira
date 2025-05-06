from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List, Optional

from sqlmodel import create_engine, Session, select

import requests, os

from app.data_access.models import (
    Player,
    PlayerRepository,
    FactPlayerPerformance,
    FactPlayerPerformanceRepository,
    TopPlayers
)
from app.api.typesense_client import ts_client

# --- Security ---
security = HTTPBasic()
API_USER = os.getenv("API_USER", "admin")
API_PASS = os.getenv("API_PASS", "secret")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if credentials.username != API_USER or credentials.password != API_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- Engines & Repos ---
silver_engine = create_engine(
    "sqlite:///silver.db", connect_args={"check_same_thread": False}
)
gold_engine = create_engine(
    "sqlite:///gold.db", connect_args={"check_same_thread": False}
)

player_repo = PlayerRepository(silver_engine)
fact_repo   = FactPlayerPerformanceRepository(gold_engine)

router = APIRouter(
    prefix="/players",
    tags=["players"],
    dependencies=[Depends(authenticate)]
)

# --- CRUD Endpoints ---

@router.get("/", response_model=List[Player])
def list_players():
    """List all players from the Silver layer."""
    return player_repo.list_all()

@router.get("/{player_id}", response_model=Player)
def get_player(player_id: int):
    """Get a single player by ID."""
    player = player_repo.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.post("/", response_model=List[Player], status_code=status.HTTP_201_CREATED)
def create_players(batch: List[Player]):
    """Batch-create players."""
    player_repo.create_batch(batch)
    return batch

@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int):
    """Delete a player by ID."""
    player_repo.delete(player_id)
    return

# --- Search Endpoint ---

@router.get("/search", response_model=List[Player])
def search_players(
    name: Optional[str]     = Query(None, description="Partial or full player name"),
    position: Optional[str] = Query(None, description="Exact position filter"),
    team: Optional[str]     = Query(None, description="Partial or full team name"),
):
    """
    Search players by name (fuzzy via Typesense) and/or filter by position and/or team.
    Falls back to in-memory substring matching if Typesense isn’t reachable or returns no hits.
    """
    # Build Typesense filters
    ts_filters = []
    if position:
        ts_filters.append(f"position:={position}")
    if team:
        ts_filters.append(f"team:={team}")
    filter_str = " && ".join(ts_filters) if ts_filters else None

    # 1) If name provided, try Typesense search
    if name:
        try:
            params = {"q": name, "query_by": "name"}
            if filter_str:
                params["filter_by"] = filter_str
            resp = ts_client.collections["players"].documents.search(params)
            hits = [hit["document"] for hit in resp["hits"]]
            if hits:
                return hits
        except Exception:
            pass  # fallback to in-memory

    # 2) Fallback to in-memory filtering
    players = player_repo.list_all()
    if name:
        players = [p for p in players if name.lower() in p.name.lower()]
    if position:
        players = [p for p in players if p.position == position]
    if team:
        players = [p for p in players if team.lower() in p.team.lower()]
    return players

# --- Ranking Endpoint ---

@router.get("/ranking", response_model=List[FactPlayerPerformance])
def get_ranking(limit: int = Query(10, ge=1, le=100)):
    """Return top N players by composite score from the Gold layer."""
    return fact_repo.list_top_by_score(limit)

# --- Materialized-view Endpoint ---

@router.get("/top", response_model=List[TopPlayers])
def get_top_players():
    """
    Return the pre-computed top-10 players by composite score
    (simulated materialized view in the Gold layer).
    """
    with Session(gold_engine) as sess:
        statement = select(TopPlayers).order_by(TopPlayers.rank)
        return sess.exec(statement).all()

# --- Price in ARS Endpoint ---

@router.get("/{player_id}/price-ars")
def get_price_in_ars(player_id: int):
    """Return a player's market value in ARS using Dolarapi."""
    player = player_repo.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    try:
        res = requests.get("https://dolarapi.com/v1/dolares/blue")
        res.raise_for_status()
        rate = float(res.json()["venta"])
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch exchange rate")
    return {
        "player_id": player.id,
        "market_value_usd": player.market_value_usd,
        "exchange_rate": rate,
        "market_value_ars": round(player.market_value_usd * rate, 2)
    }
