import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./labops.db")
    SLA_HOURS: int = int(os.getenv("SLA_HOURS", "4"))
    TEAMS_WEBHOOK_URL: Optional[str] = os.getenv("TEAMS_WEBHOOK_URL")

    # Database configuration
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"

    # API configuration
    API_TITLE: str = "LabOps Metrics API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Laboratory Operations Metrics API"

    # Synthetic data configuration
    DEFAULT_DAYS: int = 3
    DEFAULT_PER_DAY: int = 1200
    ERROR_RATE: float = 0.07  # 7% error rate

    # Assay types
    ASSAYS: list[str] = ["CBC", "Chem7", "PCR"]
    
    # Machine IDs
    MACHINES: list[str] = [f"M{i}" for i in range(1, 6)]
    
    # Operator IDs
    OPERATORS: list[str] = [f"O{i}" for i in range(1, 21)]
    
    # Error codes
    ERROR_CODES: list[str] = ["E01", "E02", "E03", "E04", "E05"]


settings = Settings()
