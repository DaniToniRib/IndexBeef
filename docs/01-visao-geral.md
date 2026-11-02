# 01 · Visão geral

## Problema

Na pecuária de corte, para escolher **quais garrotes vão para engorda, quais machos vão para reprodução e quais fêmeas ficam como matrizes**, o criador depende de:

- **Avaliação visual** (EPMURAS), que é subjetiva e varia de avaliador para avaliador;
- **Medidas manuais** (fita, hipômetro), que são trabalhosas e estressam o animal;
- **Balança**, que nem sempre está disponível, principalmente em retiros do Pantanal.

Rebanhos **Nelore PO e CEIP** já têm muito dado genético (DEPs), mas o fenótipo (como o animal *é* de fato) ainda é medido de forma pouco padronizada.

## Objetivo

Criar um sistema que, a partir de **imagens do animal**:

1. meça o porte e a conformação de forma objetiva e repetível;
2. estime o peso atual e projete o peso futuro;
3. gere índices de aptidão para **corte**, **reprodutor** e **matriz**;
4. cruze o fenótipo com a **genética** (DEPs) já existente;
5. acompanhe a **evolução do animal no tempo**.

## Público

| Usuário | Uso principal |
|---|---|
| Criador / gerente da fazenda | Selecionar animais, ranquear lotes |
| Técnico / zootecnista | Avaliar com apoio, corrigir pontos, validar |
| Vaqueiro / peão | Fazer a captura no curral (app simples) |

## Escopo

### Dentro do escopo (MVP)
- Raça **Nelore** (PO e CEIP).
- Categorias: bezerro desmamado, garrote/novilha de sobreano, matriz e touro.
- Captura por **câmera ao vivo, vídeo gravado e foto**.
- Funcionar **offline** na fazenda.

### Fora do escopo (por enquanto)
- Outras raças e cruzamentos.
- Diagnóstico de gestação por imagem (isso é feito por ultrassom ou toque; o sistema apenas **registra** o resultado).
- Exame andrológico (o sistema **registra** o resultado e o perímetro escrotal).
- Rastreabilidade oficial (SISBOV).

## Princípios

1. **Offline primeiro**: o Pantanal não tem internet confiável.
2. **Humano no circuito**: o técnico pode corrigir tudo, e cada correção vira dado de treino.
3. **Transparência**: toda predição mostra o **grau de confiança** e a **versão do modelo**.
4. **Apoio, não laudo**: o sistema recomenda, e a decisão é do criador ou do técnico.
5. **Simples no curral**: poucos toques, letras grandes, funciona sob sol forte.
