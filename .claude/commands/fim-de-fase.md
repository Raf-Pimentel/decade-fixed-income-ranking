---
description: Encerra uma fase — roda testes, confere o funil, atualiza o diário de decisões e monta o resumo de trade-offs
---

Encerre a fase atual do projeto seguindo o ritual completo. Não pule etapa, e
não declare nada pronto sem ter rodado e colado a saída real.

## 1. Qualidade

Rode e cole a saída de cada um:

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src
uv run pytest --cov=src/ranking --cov-report=term-missing
```

- Suíte verde, sem `skip` que não tenha motivo escrito ao lado.
- Cobertura mínima de 90% **nos módulos de cálculo** (`transform/`, `rank/`).
  Nos outros não há meta — não persiga número onde ele não significa nada.
- Se algo falhar, **conserte antes de continuar o ritual**. Não relate uma fase
  encerrada com a suíte vermelha.

## 2. Funil de qualidade

Se a fase já produz dados, compare o funil com o baseline do `CLAUDE.md`
(36.598 → 7.759 → … → 1.801 → 1.003, tolerância de 3%).

Desvio acima da tolerância não é para ser explicado — é para ser investigado
antes de fechar a fase.

## 3. Checklist

Abra `docs/02-checklist.md` e atualize o estado. Se algo ficou de fora nesta
fase, acrescente à seção de desvios declarados, com o motivo ao lado. Item não
feito é item declarado, não item esquecido.

## 4. Diário de decisões

Em `docs/decisoes.md`:

- Abra uma entrada `D-0XX` para cada decisão não óbvia tomada nesta fase, com
  situação, decisão, motivo, alternativa descartada e o que se aceita perder.
- Se alguma decisão anterior foi revertida, **não apague a original**: nova
  entrada marcada com 🔄, ligada à antiga. As reversões são o material mais
  valioso da apresentação final.
- Atualize a tabela "Linha do tempo" no topo.
- Alimente as seções vivas: **Surpresas**, **Números que valem citar** e o
  **Esqueleto do vídeo**.

## 5. Commit

Mensagem no formato `tipo(escopo): descrição`, corpo explicando o porquê e não
o quê. Confira o que está sendo commitado antes (`git status`), e garanta que
nada de `dados/` ou `saida/` entrou.

## 6. Apresente o resultado

Em português, sem jargão, nesta ordem:

1. **O que ficou pronto** — com números reais, não descrições.
2. **O que encontrei de inesperado** — se algo contrariou o plano, diga.
3. **Trade-offs desta fase** — tabela: decisão, ganho, custo aceito.
4. **O que isso significa para o vídeo** — que trecho novo passa a existir.
5. **O que vem na próxima fase** e o pedido explícito de autorização.

Termine perguntando se pode avançar. **Não emende a fase seguinte.**

## Lembrete

Se em algum momento você descrever um resultado em vez de mostrá-lo, pare e
rode o comando. A pergunta de controle é *"rodou? cola o número"* —
antecipe-a.
