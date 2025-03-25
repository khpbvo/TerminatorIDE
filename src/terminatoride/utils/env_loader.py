import os
from pathlib import Path
from dotenv import load_dotenv

def load_env_vars(app_root: Path = None):
    """
    Load environment variables from .env file.
    
    This should be called early in the application startup.
    """
    if app_root is None:
        # Assume we're in src/terminatoride/utils, find project root
        app_root = Path(__file__).parent.parent.parent.parent
    
    # Try to load from .env file
    env_path = app_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        return True
    
    return False

def check_required_vars():
    """Check that required environment variables are set."""
    required_vars = ['OPENAI_API_KEY']
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please set them in a .env file or in your environment."
        )
