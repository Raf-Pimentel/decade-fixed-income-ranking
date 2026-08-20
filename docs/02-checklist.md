# Checklist executável por fase

Cada item é verificável — ou passa, ou não passa. Marco conforme avanço.
Ao final de cada fase, apresento o resultado e espero aprovação antes de seguir.

---

## Fase 2 — Setup e esqueleto de testes (D1 · 20/08)

**Entregável:** projeto que instala do zero e roda uma suíte de testes **vermelha**.

- [x] `uv init` + `pyproject.toml` com a stack aprovada, nada além
- [x] Estrutura de pastas criada, cada uma com `__init__.py` e docstring de uma linha
- [x] `.gitignore` cobrindo `dados/`, `saida/`, `.venv`, `__pycache__`
- [ ] ~~`.pre-commit-config.yaml`~~ — **não feito, de propósito.** A CI aplica
      exatamente os mesmos portões (ruff, format, mypy, pytest) a cada push.
      Um hook local que ninguém instalou é teatro, não guardrail.
- [x] `Dockerfile` — **desvio declarado:** a imagem é de execução, não de teste
      (`tests/` fica fora via `.dockerignore`). A CI builda a imagem e roda a CLI
      dentro dela; os testes rodam no job de qualidade, que é onde fazem sentido.
- [x] `configs/universo.yaml`, `configs/perfis.yaml`, `configs/fontes.yaml` escritos
- [x] Fixtures reais e pequenas em `tests/fixtures/` (20 fundos × 60 dias, congeladas)
- [x] **Testes escritos e falhando** para: as 8 armadilhas, as invariantes financeiras,
      os contratos de cada etapa, o pipeline ponta a ponta
- [x] `README.md` esqueleto com o comando de execução
- [x] Repositório Git iniciado, primeiro commit, branch `main` protegida mentalmente
      (trabalho em `feat/*` e faço merge)
- [x] **GitHub Actions**: workflow que instala do zero e roda a suíte a cada push
- [x] **Comando `/fim-de-fase`** em `.claude/commands/` — testes, funil, diário, trade-offs

**Verificação:** `uv run pytest` roda e falha com mensagens claras, não com `ImportError`.

---

## Fase 3 — Extração e validação (D2–D3 · 21–22/08)

**Entregável:** dados brutos baixados, validados e materializados.

- [ ] `baixar()` com retry (3 tentativas, espera crescente) e timeout explícito
- [ ] Disjuntor: após 5 falhas seguidas no mesmo host, para de tentar e falha claro
- [ ] Cache por hash — arquivo já baixado e íntegro não baixa de novo
- [ ] `manifesto.json` com nome, tamanho, SHA-256 e horário de cada arquivo
- [ ] Validação de que o download é mesmo um ZIP/CSV (a CVM devolve HTML de erro com HTTP 200)
- [ ] Leitores para os 3 layouts do informe diário (L1/L2/L3) — L3 obrigatório, L2 se der tempo
- [ ] Schemas Pandera para: informe diário, registro classe, registro fundo, extrato, lâmina, CDI, IMA
- [ ] Quarentena: linhas rejeitadas vão para arquivo separado com o motivo
- [ ] Freio de 5%: mais que isso rejeitado ⇒ pipeline para
- [ ] `saida/relatorio_qualidade.md` com o funil comparado ao baseline

**Verificação:** o funil bate com o baseline do `CLAUDE.md` dentro da tolerância.

---

## Fase 4 — Junção e métricas (D4–D5 · 23–24/08)

**Entregável:** uma linha por fundo com os dez números.

- [ ] Junção classe ⨝ fundo ⨝ extrato/lâmina ⨝ série ⨝ CDI ⨝ IMA
- [ ] **Teste de junção:** contagem antes e depois bate; nenhum fundo duplicado
- [ ] Calendário de dias úteis explícito (não inferir dos dados)
- [ ] Escolha point-in-time do registro de extrato vigente em `data_ref`
- [ ] Métricas implementadas: rentabilidade, ganho sobre benchmark, oscilação,
      retorno por unidade de risco, pior queda, dias no vermelho, taxa, prazo,
      tamanho, estabilidade do passivo
- [ ] **Benchmark por grupo:** CDI para pós-fixado, IMA-B para indexado a inflação,
      IRF-M para prefixado — comparar tudo com CDI seria errado
- [ ] Invariantes testadas (lista no `CLAUDE.md`)
- [ ] Teste contra cálculo independente: 3 fundos conferidos à mão em planilha

**Verificação:** rentabilidade de 3 fundos bate com cálculo manual até a 4ª casa.

---

## Fase 5 — Ranking e saída (D6 · 25/08)

**Entregável:** Top 5 por perfil, com grau de confiança.

- [ ] Percentil dentro do grupo ANBIMA, com winsorização a 1%/99%
- [ ] Grupo com menos de 20 fundos é fundido ao grupo pai (senão o percentil é ruído)
- [ ] Pesos lidos de `configs/perfis.yaml`, soma validada em 100
- [ ] Elegibilidade por perfil aplicada **antes** do percentil, não depois
- [ ] Reamostragem em blocos: 1.000 simulações, semente fixa
- [ ] Sorteio de pesos dentro das faixas configuradas
- [ ] **Estabilidade reportada separando** o que varia do que não varia
      (a taxa é constante e infla a aparência de robustez — declarar isso)
- [ ] `ranking.json` validado contra o schema Pydantic de saída
- [ ] `ranking.md` legível, com um parágrafo real por fundo
- [ ] CLI funciona; funções importáveis funcionam

**Verificação:** golden file — rodar duas vezes produz JSON idêntico.

---

## Fase 5.5 — Teste no passado (D7 manhã · 26/08)

**Entregável:** `saida/validacao.md` respondendo se o método funciona.

**Regra que vale antes de tudo:** o critério de sucesso e a regra do fundo descontinuado
estão escritos na seção 8.1 do desenho e **não podem ser alterados depois de ver o resultado**.
Se eu sentir vontade de mexer, é sinal de que o resultado não agradou — e é exatamente aí que
não se mexe.

- [ ] Rodar o pipeline com `--data-ref 2025-03-31`, `2025-06-30` e `2025-09-30`
- [ ] **Auditoria de point-in-time:** confirmar que nenhuma linha posterior à data de corte
      entrou. Se entrou, é bug grave na Etapa 1 e o teste inteiro está contaminado
- [ ] Congelar os três Top 5 em arquivo, antes de medir qualquer coisa
- [ ] Medir o retorno realizado de cada Top 5 no período seguinte (peso igual entre os cinco)
- [ ] Comparar com a mediana dos elegíveis na data de corte
- [ ] Comparar com o benchmark do grupo (CDI / IMA-B / IRF-M)
- [ ] Gerar 1.000 carteiras de 5 fundos sorteados do universo elegível, com semente fixa
- [ ] Reportar **o percentil do meu Top 5 na distribuição aleatória** — é o número principal
- [ ] Reportar quantos dos 5 bateram a mediana individualmente
- [ ] Marcar fundos descontinuados no período, se houver
- [ ] Aplicar o critério declarado: acima do percentil 60 em ao menos 2 das 3 datas
- [ ] **Se falhar, escrever que falhou** e o que eu mudaria — sem tocar nos pesos
- [ ] Registrar o resultado em `docs/decisoes.md`, seja ele qual for

**Verificação:** `saida/validacao.md` existe, tem os três cortes, e a conclusão está escrita
em uma frase sem rodeio.

---

## Fase 6 — Documentação (D7 tarde · 26/08)

- [ ] `README.md`: o que é, como instalar, como rodar, o que sai, quanto demora
- [ ] Rodar do zero em máquina limpa via Docker e cronometrar
- [ ] `ranking.md` com a racionalidade por fundo e as métricas que decidiram
- [ ] `docs/decisoes.md` consolidado
- [ ] Seção destacada: **a decisão de maior incerteza**, com o porquê
- [ ] Limitações escritas sem suavizar
- [ ] Link do vídeo no README
- [ ] **Execução semanal automática ligada** — workflow agendado que roda o pipeline do zero
      e publica o `ranking.json`. Confirmar que rodou de verdade ao menos uma vez, sem mim
- [ ] **Página visual do ranking** — Top 5, métricas e o resultado do teste no passado

---

## D8 — Folga e vídeo (27/08)

- [ ] Vídeo ≤ 5 min: desenho · a decisão que menos me convence · caminho para produção
- [ ] Revisão final do repositório com olhar de quem nunca viu
- [ ] Tag `v1.0.0`

---

## Guardrails de processo (valem todos os dias)

| Momento | Pergunta que eu faço | Se a resposta for não |
|---|---|---|
| Antes de escrever função | Existe teste vermelho? | escrevo o teste |
| Antes de adicionar biblioteca | Está na stack aprovada? | justifico no doc ou desisto |
| Antes de criar abstração | Tem 2+ usos concretos hoje? | escrevo direto, sem abstrair |
| Antes de commitar | Suíte verde, ruff e mypy limpos? | conserto antes |
| Ao achar número no código | Deveria estar em YAML? | movo |
| Ao terminar etapa | Funil bate com o baseline? | investigo antes de seguir |
| Ao terminar fase | Trade-offs listados? | listo e apresento |
