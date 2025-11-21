import sys
from pathlib import Path

resource_path = lambda path: str(((Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(__file__).parent) / path).resolve())
