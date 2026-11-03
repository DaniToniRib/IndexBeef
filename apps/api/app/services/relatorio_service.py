"""Gera relatorio PDF do animal usando ReportLab."""

from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_CINZA = colors.HexColor("#6b7280")
_VERDE = colors.HexColor("#059669")
_AZUL = colors.HexColor("#1e40af")
_BORDA = colors.HexColor("#e5e7eb")

_CABECALHO_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), _AZUL),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
    ("GRID", (0, 0), (-1, -1), 0.4, _BORDA),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
])


def _fmt_data(d: Any) -> str:
    if d is None:
        return "—"
    if isinstance(d, (date, datetime)):
        return d.strftime("%d/%m/%Y")
    s = str(d)
    if "T" in s:
        return s.replace("T", " ")[:16]
    return s[:10]


def _fmt_num(v: Any, decimais: int = 1, sufixo: str = "") -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.{decimais}f}{sufixo}"
    except (TypeError, ValueError):
        return str(v)


def gerar_relatorio_animal(
    animal: dict[str, Any],
    historico: dict[str, Any],
    aplicacoes: list[dict[str, Any]],
    atendimentos: list[dict[str, Any]],
    avaliacoes: list[dict[str, Any]],
) -> bytes:
    """Retorna bytes do PDF com ficha completa do animal."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        title=f"Ficha — {animal.get('brinco', 'animal')}",
    )
    estilos = getSampleStyleSheet()
    h1 = estilos["Heading1"]
    h2 = estilos["Heading2"]
    normal = estilos["Normal"]

    historia: list[Any] = []

    # Cabeçalho
    historia.append(Paragraph("IndexBeef — Ficha do Animal", h1))
    historia.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        normal,
    ))
    historia.append(Spacer(1, 0.4 * cm))

    # Dados do animal
    historia.append(Paragraph("Identificação", h2))
    dados_animal = [
        ["Campo", "Valor", "Campo", "Valor"],
        ["Brinco", animal.get("brinco") or "—", "RGN", animal.get("rgn") or "—"],
        ["Sexo", animal.get("sexo") or "—", "Raça", animal.get("raca") or "—"],
        [
            "Nascimento", _fmt_data(animal.get("nascimento")),
            "CEIP", "Sim" if animal.get("ceip") else "Não",
        ],
        [
            "Situação", str(animal.get("situacao") or "—"),
            "Entrada", _fmt_data(animal.get("data_entrada")),
        ],
    ]
    t_animal = Table(dados_animal, colWidths=[3.5 * cm, 5.5 * cm, 3.5 * cm, 5.5 * cm])
    t_animal.setStyle(_CABECALHO_STYLE)
    historia.append(t_animal)
    historia.append(Spacer(1, 0.3 * cm))

    # Resumo de peso
    historia.append(Paragraph("Resumo de peso", h2))
    resumo = [
        ["Peso atual", "GMD total", "Idade (meses)", "Idade (dias)"],
        [
            _fmt_num(historico.get("peso_atual_kg"), 1, " kg"),
            _fmt_num(historico.get("gmd_total_kg_dia"), 3, " kg/dia"),
            _fmt_num(historico.get("idade_meses"), 1, " m"),
            str(historico.get("idade_dias") or "—"),
        ],
    ]
    t_resumo = Table(resumo, colWidths=[4.5 * cm] * 4)
    t_resumo.setStyle(_CABECALHO_STYLE)
    historia.append(t_resumo)
    historia.append(Spacer(1, 0.3 * cm))

    # Histórico de pesagens
    pesagens = historico.get("pesagens", [])
    if pesagens:
        historia.append(Paragraph("Histórico de pesagens", h2))
        rows = [["Data", "Peso (kg)", "Origem", "GMD (kg/dia)"]]
        for p in pesagens:
            rows.append([
                _fmt_data(p.get("data")),
                _fmt_num(p.get("peso_kg"), 1),
                str(p.get("origem") or "—"),
                _fmt_num(p.get("gmd_kg_dia"), 3) if p.get("gmd_kg_dia") is not None else "—",
            ])
        t_pes = Table(rows, colWidths=[3.5 * cm, 3.5 * cm, 4.5 * cm, 4.5 * cm])
        t_pes.setStyle(_CABECALHO_STYLE)
        historia.append(t_pes)
        historia.append(Spacer(1, 0.3 * cm))

    # Sanitário
    if aplicacoes:
        historia.append(Paragraph("Aplicações sanitárias", h2))
        rows = [["Data", "Tipo", "Princípio ativo", "Via", "Apto abate"]]
        for a in aplicacoes:
            rows.append([
                _fmt_data(a.get("data")),
                str(a.get("tipo") or "—"),
                str(a.get("principio_ativo") or "—"),
                str(a.get("via") or "—"),
                _fmt_data(a.get("apto_abate_em")),
            ])
        t_san = Table(rows, colWidths=[2.5 * cm, 2.5 * cm, 5.5 * cm, 2.5 * cm, 3.5 * cm])
        t_san.setStyle(_CABECALHO_STYLE)
        historia.append(t_san)
        historia.append(Spacer(1, 0.3 * cm))

    if atendimentos:
        historia.append(Paragraph("Atendimentos veterinários", h2))
        rows = [["Data", "Motivo", "Veterinário", "Diagnóstico"]]
        for at in atendimentos:
            rows.append([
                _fmt_data(at.get("data_hora")),
                str(at.get("motivo") or "—")[:40],
                f"{at.get('veterinario_nome', '')} (CRMV {at.get('veterinario_crmv', '')})".strip(),
                str(at.get("diagnostico") or "—")[:40],
            ])
        t_at = Table(rows, colWidths=[2.5 * cm, 4 * cm, 5 * cm, 4.5 * cm])
        t_at.setStyle(_CABECALHO_STYLE)
        historia.append(t_at)
        historia.append(Spacer(1, 0.3 * cm))

    # Última avaliação morfológica
    concluidas = [av for av in avaliacoes if av.get("status") == "concluida" and av.get("medida")]
    if concluidas:
        historia.append(Paragraph("Última avaliação morfológica", h2))
        ult = concluidas[0]
        data_str = _fmt_data(ult.get("data_hora"))
        ver_str = ult.get("versao_pipeline", "—")
        historia.append(Paragraph(f"Data: {data_str} · Pipeline v{ver_str}", normal))
        medida = ult.get("medida") or {}
        rows_med = [["Medida", "Valor (cm)", "Confiança"]]
        medidas_exibir = [
            ("Altura cernelha", "altura_cernelha_cm", "altura_cernelha_conf"),
            ("Altura garupa", "altura_garupa_cm", "altura_garupa_conf"),
            ("Comprimento corporal", "comprimento_corporal_cm", "comprimento_corporal_conf"),
            ("Profundidade torácica", "profundidade_toracica_cm", "profundidade_toracica_conf"),
            ("Comprimento garupa", "comprimento_garupa_cm", "comprimento_garupa_conf"),
            ("Largura garupa", "largura_garupa_cm", "largura_garupa_conf"),
            ("Altura cupim", "altura_cupim_cm", "altura_cupim_conf"),
            ("Umbigo ao chão", "umbigo_chao_cm", "umbigo_chao_conf"),
            ("Inclinação garupa (°)", "inclinacao_garupa_graus", None),
            ("Ângulo jarrete (°)", "jarrete_graus", None),
        ]
        for nome, campo_val, campo_conf in medidas_exibir:
            v = medida.get(campo_val)
            c = medida.get(campo_conf) if campo_conf else None
            if v is not None:
                rows_med.append([
                    nome,
                    _fmt_num(v, 1),
                    _fmt_num(c, 2) if c is not None else "—",
                ])
        if len(rows_med) > 1:
            t_med = Table(rows_med, colWidths=[7 * cm, 4 * cm, 5 * cm])
            t_med.setStyle(_CABECALHO_STYLE)
            historia.append(Spacer(1, 0.2 * cm))
            historia.append(t_med)

        caixa = ult.get("caixa_virtual")
        if caixa:
            historia.append(Spacer(1, 0.2 * cm))
            rows_cv = [
                ["C (cm)", "P (cm)", "L (cm)", "Volume (L)", "IPL", "Compacidade"],
                [
                    _fmt_num(caixa.get("c_cm"), 1),
                    _fmt_num(caixa.get("p_cm"), 1),
                    _fmt_num(caixa.get("l_cm"), 1),
                    _fmt_num(caixa.get("volume_l"), 1),
                    _fmt_num(caixa.get("ipl"), 3),
                    _fmt_num(caixa.get("compacidade"), 3),
                ],
            ]
            t_cv = Table(rows_cv, colWidths=[2.7 * cm] * 6)
            t_cv.setStyle(_CABECALHO_STYLE)
            historia.append(t_cv)

        predicoes = ult.get("predicoes", [])
        if predicoes:
            historia.append(Spacer(1, 0.2 * cm))
            rows_pred = [["Projeção", "Peso (kg)", "Mín (kg)", "Máx (kg)"]]
            tipo_label = {
                "peso_atual": "Peso atual",
                "peso_18m": "18 meses",
                "peso_24m": "24 meses",
                "peso_30m": "30 meses",
            }
            for pred in predicoes:
                rows_pred.append([
                    tipo_label.get(pred.get("tipo", ""), pred.get("tipo", "")),
                    _fmt_num(pred.get("valor"), 1),
                    _fmt_num(pred.get("faixa_min"), 1),
                    _fmt_num(pred.get("faixa_max"), 1),
                ])
            t_pred = Table(rows_pred, colWidths=[4 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
            t_pred.setStyle(_CABECALHO_STYLE)
            historia.append(t_pred)

    historia.append(Spacer(1, 0.5 * cm))
    historia.append(Paragraph(
        "<font color='#9ca3af'>"
        "IndexBeef · Avaliação morfológica Nelore · Relatório gerado automaticamente"
        "</font>",
        normal,
    ))

    doc.build(historia)
    return buf.getvalue()
