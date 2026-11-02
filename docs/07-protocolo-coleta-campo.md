# 07 · Protocolo de coleta em campo (Pantanal)

Objetivo do primeiro teste: **montar o dataset inicial** e **medir o erro do sistema** contra a realidade (balança, fita e hipômetro).

## Antes da viagem

### Combinar com a fazenda
- [ ] Data de um **manejo que já vai acontecer** (pesagem, vacinação ou diagnóstico de gestação). Assim se aproveita o gado no tronco.
- [ ] Balança funcionando, com exportação dos pesos.
- [ ] Técnico ou zootecnista da fazenda disponível para dar as notas EPMURAS e o ECC.
- [ ] Planilha de cadastro dos animais (brinco, RGN, sexo, nascimento, pai, mãe).
- [ ] Planilha de **DEPs** (PMGZ/ANCP) e lista de animais CEIP.
- [ ] Planilha de diagnóstico de gestação das matrizes (se existir).
- [ ] Autorização de uso das imagens e dos dados para desenvolvimento.

### Equipamentos
- [ ] 2 placas **ArUco 40×40 cm** (PVC/ACM) + abraçadeiras/arame.
- [ ] Celular principal + celular reserva (de preferência com boa câmera; iPhone Pro, se houver, para testar o LiDAR).
- [ ] Tripé + marca no chão (fita ou estaca).
- [ ] Notebook com a **estação de campo** rodando (testada offline antes de viajar).
- [ ] Roteador Wi-Fi portátil.
- [ ] Powerbanks, extensão, nobreak/gerador.
- [ ] Fita métrica, **fita de pesagem**, **hipômetro** e paquímetro grande (para largura de garupa).
- [ ] HD externo ou SSD para backup diário.

## Amostra alvo

| Categoria | Quantidade mínima | Ideal |
|---|---|---|
| Bezerros desmamados | 40 | 80 |
| Garrotes / novilhas de sobreano | 60 | 120 |
| Matrizes (com diagnóstico de gestação) | 50 | 100 |
| Touros | 10 | 30 |
| **Total** | **160** | **330** |

## Procedimento por animal (cerca de 2 a 3 minutos)

1. **Identificar**: ler o brinco e o RGN e registrar no app.
2. **Pesar** na balança e registrar o peso (`origem = balanca`).
3. **Vídeo lateral**: animal parado no corredor ou tronco, placas visíveis, 5 a 10 s, câmera no tripé.
4. **Foto/vídeo traseiro**: 3 a 5 s.
5. **Medidas manuais em um subconjunto** (cerca de 1 a cada 3 animais):
   - altura de cernelha e de garupa (hipômetro);
   - perímetro torácico (fita);
   - comprimento corporal (fita, da espádua ao ísquio);
   - largura de garupa (paquímetro, entre os ílios).
6. **Notas do técnico**: ECC e EPMURAS.
7. **Dados extras**:
   - matrizes: resultado do diagnóstico de gestação e dias de prenhez;
   - touros: perímetro escrotal e resultado andrológico, se houver.

## Equipe sugerida

| Função | Pessoas |
|---|---|
| Manejo do gado no tronco | 2 a 3 (equipe da fazenda) |
| Câmera + app | 1 |
| Medidas manuais + anotação | 1 |
| Técnico (notas) | 1 |

## Ao final de cada dia
- [ ] Backup de todos os arquivos (notebook + HD externo).
- [ ] Conferir se cada animal tem peso + vídeo lateral + identificação.
- [ ] Anotar os problemas (luz, poeira, animal que não parou, placa que não foi detectada).

## Depois da coleta
1. Anotar os keypoints (técnico + desenvolvedor) com a ferramenta do sistema ou o CVAT.
2. Separar os dados em **treino (70%) / validação (15%) / teste (15%)**, **por animal** (nunca o mesmo animal em grupos diferentes).
3. Calcular os erros:
   - medidas da imagem × hipômetro/fita;
   - peso estimado × balança;
   - escores sugeridos × notas do técnico.
4. Relatório de resultados para a fazenda.

## Cuidados
- **Bem-estar animal**: não prolongar a contenção por causa da filmagem. Se o animal não parar, passe para o próximo.
- **Segurança**: o operador da câmera fica fora do corredor.
- **Dados da fazenda**: são do proprietário. Usar apenas para o desenvolvimento combinado.
