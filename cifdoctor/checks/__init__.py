from typing import Protocol, Any, List
from dataclasses import dataclass

@dataclass
class Finding:
    severity: str  # 'info', 'warning', 'error'
    message: str
    file_path: str
    check_name: str

class Check(Protocol):
    name: str
    
    def run(self, structure_or_file: Any) -> List[Finding]:
        ...
