from dataclasses import dataclass
import pyads

PLC_AMS = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1


# --- PLC TAGS ---

@dataclass
class PLC_Var:
    name: str
    _symbol: pyads.symbol = None   # bind 전에는 None

    def bind(self, plc: pyads.Connection) -> None:
        """한 번만 호출해서 Symbol 객체를 잡아 둔다."""
        self._symbol = plc.get_symbol(self.name)

    # ── 편의 메서드 ───────────────────
    def read(self):
        if self._symbol is None:
            raise RuntimeError(f"{self.name} : bind() 먼저 호출 필요")
        return self._symbol.read()

    def write(self, value):
        if self._symbol is None:
            raise RuntimeError(f"{self.name} : bind() 먼저 호출 필요")
        self._symbol.write(value)
    
