# 11 · Rastreabilidade, dispositivos e sanitário

Referência técnica consolidando os padrões brasileiros/MAPA que o IndexBeef precisa suportar na gestão de fazenda. Este documento é a fonte da verdade quando o código precisar decidir sobre nomes de campos, carências, formatos de arquivo e protocolos.

## 1. Identificação RFID bovino (ISO 11784/11785)

- **Padrão**: LF 134.2 kHz, 64 bits, modos **FDX-B** (comum em bastão/brinco) e **HDX** (antenas de brete, maior alcance).
- **EID (Electronic ID)**: 15 dígitos. Prefixo **076** = Brasil (ISO 3166-1), seguido de 12 dígitos (faixa do fabricante + serial).
- **VID (Visual ID)**: número impresso no brinco visual. **O VID e o EID carregam o mesmo número** em identificação SISBOV — o botton eletrônico espelha o brinco.
- **SISBOV** (IN MAPA 51/2018 + CNA NT-27/2024): identificação **individual** com brinco visual + botton RFID. Obrigatório para rebanhos **ERAS** (exportação UE). Em 2026 há movimento para rastreabilidade individual nacional.

### Formato de CSV de bastão RFID
Bastões Allflex RS420, Datamars SRS2/XRS2 e Gallagher HR5 exportam:

| coluna comum | significado |
|---|---|
| `EID` | 15 dígitos ou formato `982 000012345678` |
| `VID` | número do brinco visual |
| `Date` / `Time` | timestamp local |
| `Session` / `SessionName` | agrupamento de leituras |
| `Lat` / `Lon` | opcional (bastão com GPS) |

O endpoint de ingestão precisa aceitar essas colunas em ordens variadas.

## 2. Balanças eletrônicas

- **Marcas BR**: Coimma KM3-N / KM3 Plus (tech Gallagher), Tru-Test / Datamars MP600/MP800 + indicador S3/EziWeigh7i, Gallagher W-0/W310/W810, Toledo MGR-4000.
- **Protocolos**: quase todas expõem **RS232** (string ASCII) ou **Bluetooth SPP**. Padrão Toledo contínuo: `ST,GS,+00456.5,kg\r\n`.
- **CSV Data Link (Tru-Test)**: `VID,EID,Weight,Date,Time,Session,ADG` (ADG = average daily gain).
- **Mínimo para match**: `VID` (ou `EID`) + `Weight` + `Date`.

## 3. GPS tracker em pecuária

- **Soluções BR**: iBoi (NB-IoT, brinco com GPS+RFID+acelerômetro), Spacevis Smart Tag (LoRaWAN, 4 posições/dia), Cowmed (collar Sub-GHz, foco em cio/saúde).
- **Trade-off**:
  - **LoRa/LoRaWAN**: baixo custo, baixa taxa, precisa gateway próprio na fazenda (~15 km LoS)
  - **NB-IoT/4G**: paga por SIM, usa cobertura carrier (NET/Vivo/Claro) — não precisa gateway
  - Sigfox: praticamente descontinuado no BR
- **Payload típico**: `device_id, timestamp_utc, lat, lon, hdop, battery_pct, temp_c, activity_count_1h, state (grazing/walking/resting), rssi`.
- **Eventos derivados**: geofence (entrada/saída de polígono), detecção de cio (pico de atividade do acelerômetro), inatividade (possível morte/parto), deslocamento anômalo, bateria baixa.

## 4. Calendário sanitário (MAPA 2026)

| Doença / aplicação | Status 2026 | Regra |
|---|---|---|
| **Febre aftosa** | ⚠️ **Suspensa** em todo o BR desde 2025 (OMSA, zona livre sem vacinação). | Guardar histórico; **não** entra em calendário ativo. Pode voltar se MAPA reverter. |
| **Brucelose B19** | Obrigatória | Fêmeas 3–8 meses, dose única. **Somente veterinário habilitado MAPA** aplica — registrar CRMV. |
| **Brucelose RB51** | Específico | Fêmeas adultas em plantéis selecionados. |
| **Raiva** | Condicional | Obrigatória **só** em áreas com focos ou morcegos hematófagos (varia por município). |
| **Clostridioses** (carbúnculo sintomático, gangrena, enterotoxemia) | Rotina | 1ª dose aos 3 meses, reforço em 30 dias, revacinação anual. Recomendado 1 mês após B19. |

### Vermifugação / avermectinas

| Produto | Carência abate | Nota |
|---|---|---|
| Ivermectina 1% | 35 dias | — |
| Ivermectina 3,15–4% longa ação | até 133 dias | Verificar bula |
| Associação iverm + aba 3,5% | 92 dias | — |
| Albendazole sulfóxido | ver bula | Preferir em matrizes prenhes (30d pré-parto) |

- **IN SDA 48/2011**: proíbe carência > 28 dias em confinamento/terminação.
- **Prenhez**: evitar avermectinas no terço final.
- **GTA**: comprovação de aftosa (quando aplicável, antes de 2025) e brucelose; animais ERAS precisam de nº SISBOV.

## 5. Atendimento veterinário (Res. CFMV 1138/2016)

Todo atendimento registrado deve conter:

### Identificação
`data_hora`, `veterinario_nome`, `veterinario_crmv` (número + UF), `fazenda_id`, `animal_id` (brinco + EID), `peso_estimado`, `motivo_atendimento` (clínico/profilático/reprodutivo).

### Diagnóstico e procedimento
`queixa`, `exame_fisico` (T°C, FC, FR, mucosas, ECC), `diagnostico` texto livre, opcional `cid_suspeita` / `cid_confirmada`.

### Prescrição (campos obrigatórios por CFMV)
`principio_ativo`, `nome_comercial`, `concentracao`, `forma_farmaceutica`, `dose` (`mg/kg` ou `ml_total`), `via_administracao` (IM/SC/IV/oral/tópico), `frequencia`, `duracao_tratamento_dias`, **`periodo_carencia_abate_dias`**, **`periodo_carencia_leite_dias`**, `data_inicio`, `data_fim_tratamento`, **`lote_medicamento`** (importante — rastreabilidade MAPA), `validade`.

### Flags críticos
- `apto_abate_em` = `data_aplicacao + periodo_carencia_abate_dias` (calculado)
- `apto_consumo_leite_em` = idem
- `prenhez_confirmada` (checar contraindicações)
- `receita_arquivada_url` (PDF da receita assinada — exigido em fiscalização SIF e GTA)

## 6. Modelagem adotada no IndexBeef

Com base nos achados acima, o esquema cresce assim (ver `docs/06-modelo-de-dados.md`):

- `Fazenda` ganha `tipo` (fazenda / sítio / retiro / outro), `geo` (ponto WKT via PostGIS), `area_hectares`, `codigo_sisbov`.
- Nova tabela `IdentificacaoEletronica(animal_id, eid_15, vid, modo [FDX/HDX], fabricante, ativo, ativo_desde, inativo_desde)` — **separada de `Animal`** porque brincos podem ser trocados.
- Nova tabela `Dispositivo(fazenda_id, tipo [balanca/bastao_rfid/gps_tracker], modelo, numero_serie, data_instalacao, status, config)`.
- `Pesagem` ganha `dispositivo_id` opcional (auditoria do pareamento peso↔animal).
- Nova tabela `LeituraRfid(dispositivo_id, eid, vid, timestamp, lat, lon, session, animal_id?)` — staging antes de parear com `Animal`.
- Nova tabela `AplicacaoSanitaria(animal_id, tipo [vacina/vermifugo/terapeutico], data, principio_ativo, concentracao, dose, via, carencia_abate_dias, carencia_leite_dias, lote_medicamento, validade, veterinario_crmv, campanha_id?, receita_url?)` — unificada por tipo, carências e obrigatoriedades divergem por `tipo`.
- Nova tabela `Campanha(fazenda_id, tipo, data_inicio, data_fim, protocolo)` para campanhas de rebanho.
- Nova tabela `AtendimentoVeterinario(animal_id, data_hora, veterinario_crmv, motivo, queixa, exame_fisico, diagnostico, prescricoes[])`.
- Nova tabela `TelemetriaGps(dispositivo_id, animal_id?, ts, geo [POINT PostGIS], bateria_pct, atividade, estado)`.
- Nova tabela `Geofence(fazenda_id, nome, poligono [POLYGON PostGIS], tipo [pasto/limite/alerta])` + `EventoGeofence(animal_id, geofence_id, ts, tipo [entrada/saida])`.

## Referências

- IN MAPA 51/2018 — identificação e rastreabilidade
- CNA NT-27/2024 — plano de rastreabilidade individual
- Allflex RS420 User Manual
- Tru-Test Data Link PC Software
- Res. CFMV 1138/2016 — prescrição veterinária
- IN SDA 48/2011 — carência em confinamento
