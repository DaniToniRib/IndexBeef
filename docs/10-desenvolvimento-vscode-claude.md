# 10 · Desenvolvimento com Claude Code no VS Code

## 1. Pré-requisitos (no seu computador)

| Ferramenta | Para quê |
|---|---|
| **VS Code** | Editor |
| **Git** | Versionamento |
| **Docker Desktop** | Rodar banco, fila, MinIO e os serviços |
| **Python 3.11+** | Backend e visão |
| **Node.js 20+** | Frontend e o Claude Code |
| **Conta GitHub** | Repositório |
| **Assinatura Claude (Pro/Max) ou chave da API** | Claude Code |

## 2. Instalar o Claude Code

No VS Code:
1. Abra **Extensions** (`Ctrl+Shift+X`).
2. Procure **"Claude Code"** (publicada pela Anthropic) e instale.
3. Clique no ícone do Claude na barra lateral e faça login.

Para usar também pelo terminal (opcional), instale o CLI:

```bash
npm install -g @anthropic-ai/claude-code
```

Depois, dentro da pasta do projeto, rode `claude`.

## 3. Clonar e abrir o projeto

```bash
git clone https://github.com/DaniToniRib/IndexBeef.git
```

```bash
cd IndexBeef && code .
```

Extensões recomendadas do VS Code: **Python**, **Pylance**, **Ruff**, **ESLint**, **Prettier**, **Docker**, **GitLens**.

## 4. Como o Claude Code entende o projeto

O arquivo **`CLAUDE.md`** na raiz é lido automaticamente pelo Claude Code em toda sessão. Ele contém:
- o que é o projeto e onde está a documentação;
- as convenções (idioma, unidades, estrutura);
- os comandos para rodar e testar;
- as regras (não colocar mídias no git, pesos de índices no YAML etc.).

Mantenha o `CLAUDE.md` atualizado conforme o projeto evolui.

## 5. Fluxo de trabalho sugerido

1. **Uma tarefa por vez**, seguindo o [roadmap](08-roadmap.md). Exemplo:
   > "Leia docs/09 e crie a estrutura do monorepo com o docker-compose da Fase 0."
2. **Peça o plano antes do código** em tarefas grandes (use o *Plan mode*, `Shift+Tab`):
   > "Planeje o módulo `calibration.py` conforme docs/04, seção 7. Não escreva código ainda."
3. **Revise o diff** que o Claude propõe antes de aceitar.
4. **Peça testes junto**:
   > "Implemente `measurements.py` com testes pytest usando keypoints sintéticos."
5. **Rode e valide**: `docker compose up`, abra `http://localhost:8000/docs`.
6. **Commit pequeno e frequente**, em português:
   > "Faça commit com a mensagem 'feat(worker): calibração ArUco'."
7. **Branch por funcionalidade** (`feat/calibracao-aruco`) e Pull Request para a `main`.

## 6. Primeiros prompts sugeridos (em ordem)

1. `Leia o CLAUDE.md e toda a pasta docs/. Resuma o projeto e a Fase 0 do roadmap.`
2. `Crie a estrutura do monorepo descrita em docs/09 com docker-compose (db, redis, minio, api, worker, web) e um endpoint /health.`
3. `Crie hardware/gerar_placa_aruco.py que gera o PDF da placa ArUco DICT_4X4_50 (IDs 0 e 1) no tamanho real 40x40 cm, com margem de quiet zone e rótulo. Inclua variante --formato a3 só para prototipagem (ver docs/03).`
4. `Implemente os modelos SQLAlchemy e a migração Alembic de acordo com docs/06 (fazenda, lote, animal, pesagem, avaliacao, captura).`
5. `Implemente no worker a extração de frames e a segmentação com YOLO-seg (classe cow), com teste usando um vídeo de exemplo.`
6. `Implemente calibration.py (ArUco + homografia) com teste usando uma imagem sintética.`
7. `Crie a tela web de revisão de keypoints: mostrar o frame e permitir arrastar os 18 pontos do docs/04.`
8. `Implemente measurements.py e virtual_box.py conforme docs/04, seções 8 e 10, com testes.`

## 7. Dicas
- Se o Claude se perder, mande `/clear` e recomece citando o documento certo.
- Use `/init` só se quiser regenerar o `CLAUDE.md` (cuidado para não perder as regras atuais).
- Sempre peça para **rodar os testes** depois de uma mudança.
- Vídeos e fotos de teste ficam em `samples/` (que está no `.gitignore`).
