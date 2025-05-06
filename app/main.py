from fastapi import FastAPI
from fastapi import HTTPException
from app.api.players import router as players_router
from app.api.typesense_client import ts_client
import typesense
from app.api.routes import router as upload_router

app = FastAPI(title="Soccer Player Market Analysis")

# Include routers
app.include_router(players_router)
app.include_router(upload_router)

@app.get("/")
def read_root():
    return {"message": "API is up and running"}

@app.on_event("startup")
def create_typesense_collection():
    # Define schema once
    schema = {
      "name": "players",
      "fields": [
        {"name": "id", "type": "int32"},
        {"name": "name", "type": "string"},
        {"name": "position", "type": "string", "facet": True},
        {"name": "team", "type": "string", "facet": True},
        {"name": "market_value_usd", "type": "float"},
      ],
      "default_sorting_field": "market_value_usd"
    }
    # Try to create or recreate collection
    try:
        ts_client.collections.create(schema)
    except typesense.exceptions.ObjectAlreadyExists:
        ts_client.collections["players"].delete()
        ts_client.collections.create(schema)
    except Exception as e:
        print(f"⚠️ Typesense connection failed at startup: {e}")
        return

    # Import data from Silver DB
    try:
        from sqlmodel import Session, select, create_engine
        from app.data_access.models import Player

        engine = create_engine(
            "sqlite:///silver.db", connect_args={"check_same_thread": False}
        )
        with Session(engine) as session:
            players = session.exec(select(Player)).all()
            documents = [
                {
                    "id": p.id,
                    "name": p.name,
                    "position": p.position,
                    "team": p.team,
                    "market_value_usd": p.market_value_usd
                }
                for p in players
            ]
            ts_client.collections["players"].documents.import_(
                documents, {"action": "upsert"}
            )
    except Exception as e:
        print(f"⚠️ Failed to index data in Typesense: {e}")
