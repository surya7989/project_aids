import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

from backend.main import app
from mangum import Mangum

handler = Mangum(app)
