"""
Configuration management for the HMI server.
Loads settings from environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration"""
    
    # Server Configuration
    PORT: int = int(os.getenv("PORT", "5000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Test Configuration
    # Can be fractional (e.g., 0.1 = 6 seconds, 0.5 = 30 seconds) for testing
    TEST_DURATION_MINUTES: float = float(os.getenv("TEST_DURATION_MINUTES", "31"))
    
    # Backend Configuration
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:4000")
    FACTORY_CODE: str = os.getenv("FACTORY_CODE", "factory-a")
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    STATIC_DIR: Path = BASE_DIR / "static"
    RESULTS_DIR: Path = BASE_DIR / "results"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.STATIC_DIR.exists():
            raise FileNotFoundError(
                f"Static directory not found: {cls.STATIC_DIR}\n"
                f"Current working directory: {cls.BASE_DIR}\n"
                f"Please ensure static files are in the correct location."
            )
        
        index_file = cls.STATIC_DIR / "index.html"
        if not index_file.exists():
            raise FileNotFoundError(
                f"index.html not found in static directory: {cls.STATIC_DIR}"
            )
        
        return True

