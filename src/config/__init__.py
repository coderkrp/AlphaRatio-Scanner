import yaml
from pathlib import Path
from .models import FullConfig

def load_and_validate(config_path: str = "config.yaml") -> FullConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(path, 'r', encoding='utf-8-sig') as f:
        raw_data = yaml.safe_load(f)
        
    if raw_data is None:
        raise ValueError("Configuration file is empty")
        
    return FullConfig(**raw_data)
