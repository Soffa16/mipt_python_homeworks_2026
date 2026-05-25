import sys
from pathlib import Path

# требуется, чтобы импорты работали при вызове pytest вне final_project/
sys.path.insert(0, str(Path(__file__).parent.parent))
