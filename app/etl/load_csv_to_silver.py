import pandas as pd
from sqlmodel import SQLModel, Session, create_engine

# Import the Player model from your shared models
from app.data_access.models import Player

# Path to the CSV file
bronze_file = "bronze/argentina_players.csv"

def main():
    # Load the CSV with pandas
    df = pd.read_csv(bronze_file)

    # Create (or recreate) the SQLite database for Silver Layer
    engine = create_engine("sqlite:///silver.db")
    # This will create the Player table (and any other models you import)
    SQLModel.metadata.create_all(engine)

    # Insert the pandas data into the database
    with Session(engine) as session:
        players = [Player(**row) for row in df.to_dict(orient="records")]
        session.add_all(players)
        session.commit()

    print("✅ Players successfully loaded into silver.db")

if __name__ == "__main__":
    main()
