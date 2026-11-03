"""Parser de CSV de bastao RFID (Allflex RS420 / Datamars / Gallagher).

As colunas nao sao padronizadas entre fabricantes; aceita variacoes de case
e nomes alternativos (ver docs/11 §1). Combina Date + Time -> timestamp.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation

from app.schemas.leitura_rfid import LeituraRfidCreate

# Mapa de aliases (lowercase) -> campo canonico
_ALIASES: dict[str, str] = {
    "eid": "eid",
    "animal id": "eid",
    "animalid": "eid",
    "rfid": "eid",
    "vid": "vid",
    "visual id": "vid",
    "visualid": "vid",
    "tag": "vid",
    "brinco": "vid",
    "date": "date",
    "data": "date",
    "time": "time",
    "hora": "time",
    "datetime": "datetime",
    "timestamp": "datetime",
    "session": "session",
    "sessionname": "session",
    "sessao": "session",
    "lat": "lat",
    "latitude": "lat",
    "lon": "lon",
    "lng": "lon",
    "longitude": "lon",
}


class ErroCsv(ValueError):
    """Erro de parsing de uma linha."""

    def __init__(self, linha: int, motivo: str) -> None:
        super().__init__(f"linha {linha}: {motivo}")
        self.linha = linha
        self.motivo = motivo


def _parse_date(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"data invalida: {s!r}")


def _parse_time(s: str) -> time:
    s = s.strip()
    for fmt in ("%H:%M:%S", "%H:%M", "%H:%M:%S.%f"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"hora invalida: {s!r}")


def _parse_decimal(s: str) -> Decimal | None:
    s = (s or "").strip().replace(",", ".")
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation as e:
        raise ValueError(f"numero invalido: {s!r}") from e


def parse_csv_bastao(
    conteudo: str, dispositivo_id=None,
) -> tuple[list[LeituraRfidCreate], list[dict[str, str]]]:
    """Devolve (leituras, erros_por_linha). Nao persiste nada."""
    buf = io.StringIO(conteudo)
    reader = csv.DictReader(buf)
    if reader.fieldnames is None:
        return [], [{"linha": "0", "motivo": "CSV sem cabecalho"}]

    campo_para_canonico: dict[str, str] = {}
    for coluna in reader.fieldnames:
        chave = (coluna or "").strip().lower()
        canon = _ALIASES.get(chave)
        if canon:
            campo_para_canonico[coluna] = canon

    if "eid" not in campo_para_canonico.values():
        return [], [
            {"linha": "0", "motivo": "coluna EID (ou alias) obrigatoria no CSV"},
        ]

    leituras: list[LeituraRfidCreate] = []
    erros: list[dict[str, str]] = []
    for i, raw in enumerate(reader, start=2):  # linha 1 = header
        try:
            dados: dict[str, str] = {}
            for coluna, canon in campo_para_canonico.items():
                dados[canon] = (raw.get(coluna) or "").strip()

            if not dados.get("eid"):
                raise ErroCsv(i, "EID vazio")

            if "datetime" in dados and dados["datetime"]:
                ts = datetime.fromisoformat(dados["datetime"].replace("Z", "+00:00"))
            else:
                d_str = dados.get("date")
                t_str = dados.get("time") or "00:00:00"
                if not d_str:
                    raise ErroCsv(i, "sem Date e sem DateTime")
                ts = datetime.combine(_parse_date(d_str), _parse_time(t_str))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)

            leituras.append(
                LeituraRfidCreate(
                    dispositivo_id=dispositivo_id,
                    eid=dados["eid"],
                    vid=dados.get("vid") or None,
                    timestamp=ts,
                    session=dados.get("session") or None,
                    latitude=_parse_decimal(dados.get("lat") or ""),
                    longitude=_parse_decimal(dados.get("lon") or ""),
                ),
            )
        except ErroCsv as e:
            erros.append({"linha": str(e.linha), "motivo": e.motivo})
        except (ValueError, TypeError) as e:
            erros.append({"linha": str(i), "motivo": str(e)})
    return leituras, erros


def parse_csv_balanca(
    conteudo: str,
) -> tuple[list[dict], list[dict[str, str]]]:
    """Parser para CSV de balanca (Tru-Test Data Link e similares).

    Colunas aceitas (case/alias):
      VID, EID, Weight/Peso, Date, Time, Session, ADG (opcional)

    Devolve (linhas_normalizadas, erros). Cada linha e um dict com:
      {eid?, vid?, peso_kg, data, session?}
    O match com animal fica no router.
    """
    aliases: dict[str, str] = {
        "eid": "eid",
        "vid": "vid",
        "tag": "vid",
        "brinco": "vid",
        "weight": "peso_kg",
        "peso": "peso_kg",
        "peso_kg": "peso_kg",
        "date": "date",
        "data": "date",
        "time": "time",
        "hora": "time",
        "datetime": "datetime",
        "timestamp": "datetime",
        "session": "session",
        "sessionname": "session",
    }
    buf = io.StringIO(conteudo)
    reader = csv.DictReader(buf)
    if reader.fieldnames is None:
        return [], [{"linha": "0", "motivo": "CSV sem cabecalho"}]

    campo_para_canonico: dict[str, str] = {}
    for coluna in reader.fieldnames:
        chave = (coluna or "").strip().lower()
        canon = aliases.get(chave)
        if canon:
            campo_para_canonico[coluna] = canon

    canonicos = set(campo_para_canonico.values())
    if "peso_kg" not in canonicos:
        return [], [{"linha": "0", "motivo": "coluna de peso (Weight/Peso) obrigatoria"}]
    if not {"eid", "vid"} & canonicos:
        return [], [{"linha": "0", "motivo": "precisa EID ou VID para parear o animal"}]

    linhas: list[dict] = []
    erros: list[dict[str, str]] = []
    for i, raw in enumerate(reader, start=2):
        try:
            dados: dict[str, str] = {}
            for coluna, canon in campo_para_canonico.items():
                dados[canon] = (raw.get(coluna) or "").strip()

            peso = _parse_decimal(dados.get("peso_kg", ""))
            if peso is None or peso <= 0:
                raise ErroCsv(i, "peso ausente ou nao-positivo")

            if "date" in dados and dados["date"]:
                data = _parse_date(dados["date"])
            elif "datetime" in dados and dados["datetime"]:
                data = datetime.fromisoformat(
                    dados["datetime"].replace("Z", "+00:00"),
                ).date()
            else:
                raise ErroCsv(i, "sem Date ou DateTime")

            linhas.append(
                {
                    "eid": (dados.get("eid") or "").replace(" ", "").replace("-", "")
                    or None,
                    "vid": dados.get("vid") or None,
                    "peso_kg": peso,
                    "data": data,
                    "session": dados.get("session") or None,
                },
            )
        except ErroCsv as e:
            erros.append({"linha": str(e.linha), "motivo": e.motivo})
        except (ValueError, TypeError) as e:
            erros.append({"linha": str(i), "motivo": str(e)})
    return linhas, erros
