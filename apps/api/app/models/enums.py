"""Enums do dominio (ver docs/06-modelo-de-dados.md e docs/11)."""

from __future__ import annotations

import enum


class CategoriaLote(str, enum.Enum):
    bezerro = "bezerro"
    garrote = "garrote"
    novilha = "novilha"
    matriz = "matriz"
    touro = "touro"


class Variedade(str, enum.Enum):
    padrao = "padrao"
    mocho = "mocho"


class Sexo(str, enum.Enum):
    M = "M"
    F = "F"


class SituacaoAnimal(str, enum.Enum):
    ativo = "ativo"
    vendido = "vendido"
    morto = "morto"
    descartado = "descartado"


class OrigemPesagem(str, enum.Enum):
    balanca = "balanca"
    estimado = "estimado"
    fita = "fita"


class StatusAvaliacao(str, enum.Enum):
    capturada = "capturada"
    processando = "processando"
    revisar = "revisar"
    concluida = "concluida"
    erro = "erro"


class TipoCaptura(str, enum.Enum):
    ao_vivo = "ao_vivo"
    video = "video"
    foto = "foto"


class VistaCaptura(str, enum.Enum):
    lateral = "lateral"
    traseira = "traseira"
    dorsal = "dorsal"
    frontal = "frontal"


class TipoFazenda(str, enum.Enum):
    fazenda = "fazenda"
    sitio = "sitio"
    retiro = "retiro"
    outro = "outro"


class ModoRfid(str, enum.Enum):
    """Modos do padrao ISO 11784/11785 (ver docs/11 §1)."""

    FDX_B = "FDX_B"  # bastao / brinco (comum)
    HDX = "HDX"  # antenas de brete (alcance maior)


class TipoDispositivo(str, enum.Enum):
    balanca = "balanca"
    bastao_rfid = "bastao_rfid"
    antena_rfid_brete = "antena_rfid_brete"
    gps_tracker = "gps_tracker"
    camera = "camera"
    outro = "outro"


class StatusDispositivo(str, enum.Enum):
    ativo = "ativo"
    inativo = "inativo"
    manutencao = "manutencao"


class TipoAplicacaoSanitaria(str, enum.Enum):
    """Tipos distintos porque carencia, obrigatoriedade e campos variam.

    - vacina: brucelose B19, clostridiose, raiva etc. Aftosa suspensa 2025
      vira so historico (nao-ativa). Ver docs/11 §4.
    - vermifugo: avermectinas (ivermectina/moxidectina), carencia 35-133d.
    - terapeutico: antibiotico, antiinflamatorio, outros medicamentos.
    """

    vacina = "vacina"
    vermifugo = "vermifugo"
    terapeutico = "terapeutico"


class ViaAdministracao(str, enum.Enum):
    IM = "IM"  # intramuscular
    SC = "SC"  # subcutanea
    IV = "IV"  # intravenosa
    oral = "oral"
    topico = "topico"
    outra = "outra"


class StatusCampanha(str, enum.Enum):
    planejada = "planejada"
    em_andamento = "em_andamento"
    concluida = "concluida"
    cancelada = "cancelada"


class EstadoAtividadeGps(str, enum.Enum):
    """Estado derivado do acelerometro do tracker (ver docs/11 §3)."""

    grazing = "grazing"  # pastando
    walking = "walking"  # andando
    resting = "resting"  # descansando
    desconhecido = "desconhecido"


class TipoGeofence(str, enum.Enum):
    pasto = "pasto"  # delimitacao de pastagem
    limite = "limite"  # limite da fazenda (fuga se sair)
    alerta = "alerta"  # area de risco (barranco, matagal denso)
    curral = "curral"


class TipoEventoGeofence(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"
