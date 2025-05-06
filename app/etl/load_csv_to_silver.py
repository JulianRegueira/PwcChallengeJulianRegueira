import pandas as pd
from sqlmodel import SQLModel, create_engine
from app.data_access.models import Player, PlayerRepository

# Path to the CSV file
BRONZE_FILE = "bronze/argentina_players.csv"

def main():
    # 1) Read the CSV
    df = pd.read_csv(BRONZE_FILE)

    # 2) Create (or recreate) the Silver DB schema
    engine = create_engine("sqlite:///silver.db")
    SQLModel.metadata.create_all(engine)

    # 3) Build Player instances
    players = [Player(**row) for row in df.to_dict(orient="records")]

    # 4) Use the repository to batch‐insert
    repo = PlayerRepository(engine)
    repo.create_batch(players)

    print("✅ Players successfully loaded into silver.db")

if __name__ == "__main__":
    main()
