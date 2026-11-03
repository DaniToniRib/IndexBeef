"""Modelos SQLAlchemy do IndexBeef (ver docs/06-modelo-de-dados.md).

Importar modulos aqui garante que o Base.metadata registre todas as tabelas
antes de `create_all` ou do autogenerate do Alembic.
"""

from app.models.animal import Animal
from app.models.aplicacao_sanitaria import AplicacaoSanitaria
from app.models.atendimento_veterinario import AtendimentoVeterinario
from app.models.avaliacao import Avaliacao
from app.models.base import Base, SyncMixin
from app.models.caixa_virtual_avaliacao import CaixaVirtualAvaliacao
from app.models.campanha import Campanha
from app.models.captura import Captura
from app.models.dispositivo import Dispositivo
from app.models.evento_geofence import EventoGeofence
from app.models.fazenda import Fazenda
from app.models.geofence import Geofence
from app.models.identificacao_eletronica import IdentificacaoEletronica
from app.models.leitura_rfid import LeituraRfid
from app.models.lote import Lote
from app.models.medida_avaliacao import MedidaAvaliacao
from app.models.pesagem import Pesagem
from app.models.predicao_avaliacao import PredicaoAvaliacao
from app.models.telemetria_gps import TelemetriaGps

__all__ = [
    "Animal",
    "AplicacaoSanitaria",
    "AtendimentoVeterinario",
    "Avaliacao",
    "Base",
    "CaixaVirtualAvaliacao",
    "Campanha",
    "Captura",
    "Dispositivo",
    "EventoGeofence",
    "Fazenda",
    "Geofence",
    "IdentificacaoEletronica",
    "LeituraRfid",
    "Lote",
    "MedidaAvaliacao",
    "Pesagem",
    "PredicaoAvaliacao",
    "SyncMixin",
    "TelemetriaGps",
]
