"""Modelos SQLAlchemy do IndexBeef (ver docs/06-modelo-de-dados.md).

Importar modulos aqui garante que o Base.metadata registre todas as tabelas
antes de `create_all` ou do autogenerate do Alembic.
"""

from app.models.animal import Animal
from app.models.avaliacao import Avaliacao
from app.models.base import Base, SyncMixin
from app.models.captura import Captura
from app.models.fazenda import Fazenda
from app.models.lote import Lote
from app.models.pesagem import Pesagem

__all__ = [
    "Animal",
    "Avaliacao",
    "Base",
    "Captura",
    "Fazenda",
    "Lote",
    "Pesagem",
    "SyncMixin",
]
