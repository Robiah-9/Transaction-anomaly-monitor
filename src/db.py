import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "sentinel.db"
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

def get_engine():
    """Create and return a SQLAlchemy engine with appropriate settings."""
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, echo=False)
    else:
        # PostgreSQL pool configuration
        engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, echo=False)
    return engine

def init_db(engine=None):
    """Initialize database tables from sql/create_tables.sql or SQLAlchemy metadata."""
    if engine is None:
        engine = get_engine()
        
    sql_path = BASE_DIR / "sql" / "create_tables.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL DDL file not found at {sql_path}")
        
    with open(sql_path, "r", encoding="utf-8") as f:
        ddl = f.read()

    # Adjust AUTOINCREMENT if Postgres
    if "postgresql" in engine.dialect.name:
        ddl = ddl.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        
    with engine.begin() as conn:
        # Split statements by semicolon
        statements = [s.strip() for s in ddl.split(";") if s.strip()]
        for stmt in statements:
            conn.execute(text(stmt))

if __name__ == "__main__":
    eng = get_engine()
    print(f"Connecting to database: {eng.url}")
    init_db(eng)
    print("Database tables initialized successfully!")
