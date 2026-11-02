# 05 · Avaliações e índices

> ⚠️ **Todos os pesos e limiares deste documento são INICIAIS e HIPOTÉTICOS.** Eles devem ser calibrados com os dados do teste de campo e validados por zootecnista. Ficam em arquivo de configuração (`config/indices.yaml`), não no código.

## 1. Peso estimado

### Fase 0: fórmula de referência (sem dados)
Usar uma fórmula baseada em **perímetro torácico** e **comprimento**, do tipo:

```
Peso (kg) ≈ k · PT² · CC          (PT e CC em metros)
```

O coeficiente `k` será ajustado para Nelore no campo. O valor inicial vem de literatura de fita de pesagem e deve ser validado contra a balança.

> Fita de pesagem calibrada para taurinos tende a errar em zebuínos. Por isso o ajuste para Nelore é obrigatório.

### Fase 1+: modelo treinado
- Regressão (**Gradient Boosting**, por exemplo LightGBM) com as entradas: medidas, área da silhueta, volume da caixa, idade, sexo, categoria e ECC.
- Alvo: **peso de balança** pareado com a captura (no mesmo dia).
- Métricas: **MAPE** (meta < 5%) e erro absoluto médio (kg).

## 2. Projeção de peso futuro
- Entradas: peso estimado atual, idade, **GMD histórico** (diferença entre avaliações), Frame score, ECC e DEPs de peso (P210, P365, P450).
- MVP: curva de crescimento de referência para Nelore (Brody ou von Bertalanffy) ajustada pelo Frame e pelas DEPs.
- Saída: peso projetado aos **18, 24 e 30 meses**, com faixa (mínimo–máximo).

## 3. Frame score
- Baseado em **altura de garupa × idade** (metodologia BIF), com tabela adaptada para zebuínos.
- Escala de 1 a 9. Para Nelore de corte, frames moderados (por exemplo 4–6) tendem a combinar tamanho com precocidade de acabamento. **Faixa ideal a validar com o técnico.**

## 4. ECC (Escore de Condição Corporal)
- Escala de **1 a 9** (ou 1–5, configurável).
- Fase 0: o técnico informa e o sistema registra.
- Fase 1+: classificador de imagem (lateral + traseira) treinado com as notas do técnico.
- Uso crítico para **matriz**: ECC ao parto e na estação de monta.

## 5. EPMURAS assistido

| Letra | Característica | Por imagem? | Fonte no sistema |
|---|---|---|---|
| **E** | Estrutura (tamanho, capacidade corporal) | ✅ Bom | Medidas, caixa virtual |
| **P** | Precocidade (profundidade, cobertura) | ✅ Bom | Compacidade, IPL, ECC |
| **M** | Musculosidade | 🟡 Médio | Vista traseira (curvatura do posterior) |
| **U** | Umbigo | 🟡 Médio | Distância umbigo–chão, tamanho relativo |
| **R** | Caracterização racial | 🟡 Médio | Cupim, cabeça, pelagem (classificador) |
| **A** | Aprumos | 🟡 Médio | Ângulos de jarrete e quartela |
| **S** | Sexualidade | 🟡 Parcial | Machos: cupim, cabeça, **perímetro escrotal (manual)**; fêmeas: feminilidade |

Cada letra recebe uma **sugestão** do sistema (escala usada pela fazenda/ABCZ, por exemplo 1–6) e o técnico **confirma ou altera**.

## 6. Índices de aptidão (0–100)

Cada índice é uma **soma ponderada de componentes normalizados** (percentil dentro do grupo de contemporâneos: mesma fazenda, sexo e faixa de idade).

### 🥩 Índice Garrote/Bezerro: enchimento de carcaça e ganho

| Componente | Peso inicial |
|---|---|
| Índice de preenchimento lateral (IPL) | 20% |
| Compacidade (PT/AC) | 15% |
| Comprimento corporal relativo | 10% |
| Largura de garupa | 10% |
| Musculosidade (M) | 15% |
| GMD / peso ajustado para a idade | 15% |
| DEPs de crescimento e carcaça (P450, AOL, ACAB) | 15% |

### 🐂 Índice Reprodutor

| Componente | Peso inicial |
|---|---|
| Estrutura + precocidade (E, P) | 20% |
| Aprumos (A) | 15% |
| Umbigo/bainha (U) | 10% |
| Caracterização racial e sexualidade (R, S) | 10% |
| Perímetro escrotal ajustado para a idade (manual) | 15% |
| DEPs (PE, IPP, P450, índice do programa) | 30% |
| **Eliminatórios** | Aprumo grave, umbigo/prepúcio muito pendular, defeito genético, andrológico reprovado |

### 🐄 Índice Matriz: gestar e desmamar bons bezerros

O objetivo é identificar fêmeas com **capacidade de carregar e parir bem um bezerro grande e desmamá-lo pesado**.

| Componente | Peso inicial | Por quê |
|---|---|---|
| **Capacidade corporal** (PT, IPL, volume da caixa) | 20% | Espaço para a gestação e reserva corporal |
| **Garupa**: largura (LG) e comprimento (CG) | 15% | Abertura pélvica e facilidade de parto |
| **Inclinação de garupa** (faixa moderada) | 5% | Garupa muito plana ou muito caída prejudica o parto |
| Aprumos (A) | 10% | Longevidade no pasto (fundamental no Pantanal) |
| Umbigo (U) | 5% | Menos lesões e problemas no campo |
| Feminilidade / caracterização (R, S) | 5% | — |
| **ECC adequado** para a fase (ex.: 5–6 ao parto) | 10% | Retorno ao cio e produção de leite |
| **DEPs maternas** (STAY, PP30, IPP, MP120, P120 materno) | 30% | Habilidade materna e precocidade sexual comprovadas geneticamente |

Dados complementares registrados (não vêm da imagem):
- **Diagnóstico de gestação** (data, resultado, tempo de prenhez), por ultrassom ou toque.
- Histórico reprodutivo: idade ao primeiro parto, intervalo entre partos, peso à desmama dos bezerros.
- **Peso dos bezerros desmamados** daquela vaca, que é a verdade final do índice e serve para validá-lo.

**Acompanhamento da prenhe**: avaliações mensais da vaca gestante para monitorar ECC e capacidade corporal ao longo da gestação, com alerta se o ECC cair.

## 7. Apresentação ao usuário

- Cada índice com **nota (0–100)**, **faixa** (🟢 superior, 🟡 médio, 🔴 inferior) e **posição no lote** (ranking).
- Mostrar **os três componentes que mais pesaram** ("explicação").
- Sempre exibir a **confiança** e o aviso: *"Recomendação de triagem — confirme com avaliação técnica."*
