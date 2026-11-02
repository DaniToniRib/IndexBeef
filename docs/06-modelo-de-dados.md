# 06 · Modelo de dados

## Diagrama de entidades

```
Fazenda 1─* Lote 1─* Animal
                       │
                       ├─* Pesagem
                       ├─* Avaliacao 1─* Captura 1─* Frame
                       │       ├─1 Medidas
                       │       ├─1 CaixaVirtual
                       │       ├─1 Escores (Frame, ECC, EPMURAS)
                       │       ├─* Keypoint (por frame, com flag "corrigido")
                       │       └─* Predicao (peso, projeção, índices)
                       ├─* EventoReprodutivo (diagnóstico de gestação, parto, desmama)
                       ├─* ExameAndrologico
                       └─1 DadosGeneticos (DEPs importadas)

Animal ─ pai_id / mae_id → Animal (genealogia)
ModeloVersao 1─* Predicao
Usuario *─* Fazenda (papéis: admin, técnico, operador)
```

## Tabelas principais (PostgreSQL)

> Todas as tabelas têm: `id UUID PK` (gerado na origem), `criado_em`, `atualizado_em`, `origem_estacao` e `sincronizado_em`.

### fazenda
| Campo | Tipo | Nota |
|---|---|---|
| nome | text | |
| municipio, uf | text | |
| bioma | text | ex.: "Pantanal" |
| geo | point | opcional |

### lote
| Campo | Tipo |
|---|---|
| fazenda_id | FK |
| nome | text |
| categoria | enum (bezerro, garrote, novilha, matriz, touro) |

### animal
| Campo | Tipo | Nota |
|---|---|---|
| fazenda_id, lote_id | FK | |
| brinco | text | identificação de manejo |
| rgn / rgd | text | registro ABCZ |
| ceip | bool | animal certificado CEIP |
| rfid | text | opcional |
| raca | text | default "Nelore" |
| variedade | enum (padrao, mocho) | |
| sexo | enum (M, F) | |
| nascimento | date | |
| pai_id, mae_id | FK animal | nullable |
| situacao | enum (ativo, vendido, morto, descartado) | |

### pesagem
| Campo | Tipo | Nota |
|---|---|---|
| animal_id | FK | |
| data | date | |
| peso_kg | numeric | |
| origem | enum (balanca, estimado, fita) | |
| avaliacao_id | FK | se for estimado |

### avaliacao
| Campo | Tipo | Nota |
|---|---|---|
| animal_id | FK | |
| data_hora | timestamptz | |
| avaliador_id | FK usuario | |
| status | enum (capturada, processando, revisar, concluida, erro) | |
| versao_pipeline | text | |
| observacoes | text | |

### captura
| Campo | Tipo | Nota |
|---|---|---|
| avaliacao_id | FK | |
| tipo | enum (ao_vivo, video, foto) | |
| vista | enum (lateral, traseira, dorsal, frontal) | |
| arquivo_url | text | MinIO/S3 |
| dispositivo | text | modelo do celular |
| px_por_cm | numeric | |
| erro_calibracao_px | numeric | |

### frame
| Campo | Tipo |
|---|---|
| captura_id | FK |
| indice | int |
| arquivo_url | text |
| score_qualidade | numeric |
| selecionado | bool |
| mascara_url | text |

### keypoint
| Campo | Tipo | Nota |
|---|---|---|
| frame_id | FK | |
| ponto_id | int | ver tabela do doc 04 |
| x, y | numeric | pixels |
| confianca | numeric | |
| corrigido | bool | corrigido manualmente (vira dado de treino) |
| corrigido_por | FK usuario | |

### medidas
Uma linha por avaliação, com as colunas: `altura_cernelha`, `altura_garupa`, `comprimento_corporal`, `profundidade_toracica`, `comprimento_garupa`, `largura_garupa`, `inclinacao_garupa`, `altura_cupim`, `umbigo_chao`, `angulo_jarrete`, `area_tronco` e `perimetro_toracico_est`. Cada medida tem a coluna `_conf` correspondente.
Também é possível guardar as **medidas manuais de referência** (`*_manual`) para validação.

### caixa_virtual
`avaliacao_id`, `c_cm`, `p_cm`, `l_cm`, `volume_l`, `ipl`, `compacidade`, `indice_comprimento`.

### escores
`avaliacao_id`, `frame_score`, `ecc`, `e`, `p`, `m`, `u`, `r`, `a`, `s`. Cada letra tem um campo `_sugerido` (sistema) e um `_final` (técnico).

### predicao
| Campo | Tipo |
|---|---|
| avaliacao_id | FK |
| tipo | enum (peso_atual, peso_18m, peso_24m, peso_30m, indice_garrote, indice_reprodutor, indice_matriz) |
| valor | numeric |
| faixa_min, faixa_max | numeric |
| confianca | numeric |
| explicacao | jsonb (principais componentes) |
| modelo_versao_id | FK |

### evento_reprodutivo
`animal_id`, `tipo` (cobertura, IATF, diagnostico_gestacao, parto, aborto, desmama), `data`, `resultado`, `dias_gestacao`, `touro_id`, `bezerro_id`, `peso_desmama_bezerro`.

### exame_andrologico
`animal_id`, `data`, `perimetro_escrotal_cm`, `resultado` (apto, inapto, questionavel), `veterinario`, `observacoes`.

### dados_geneticos
`animal_id`, `programa` (PMGZ, ANCP, Geneplus, ...), `safra`, `deps jsonb` (por exemplo `{"P120": ..., "P210": ..., "P450": ..., "PE": ..., "IPP": ..., "STAY": ..., "PP30": ..., "AOL": ..., "ACAB": ..., "MP120": ...}`), `indice_programa`, `deca`, `data_importacao`.

### modelo_versao
`nome` (segmentacao, keypoints_lateral, peso, ecc...), `versao`, `metricas jsonb`, `artefato_url`, `ativo`.

## Importações
- **CSV/Excel** de cadastro de animais (brinco, RGN, sexo, nascimento, pai, mãe).
- **CSV** de DEPs do programa de melhoramento.
- **CSV** de pesagens da balança (muitas balanças eletrônicas exportam nesse formato).
