"""Hook de prueba para onFailure (vídeo 709): igual que bloquear.py, pero antes lee
.claude/hooks/reglas.json, que NO existe. El script revienta con FileNotFoundError y sale con 1:
un hook roto, no uno que decide. Sirve para ver qué hace Claude Code cuando el guardián falla."""
import json
import os
import sys
from pathlib import Path

reglas = json.loads((Path(os.environ["CLAUDE_PROJECT_DIR"]) / ".claude" / "hooks" / "reglas.json").read_text())
sys.path.insert(0, str(Path(__file__).parent))
import bloquear  # noqa: E402

bloquear.main()
