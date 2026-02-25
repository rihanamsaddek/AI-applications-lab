"""pytest configuration — adds project root to sys.path so imports work."""
import sys
from pathlib import Path

# Add the marketing-automation-agent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))
