# Checklist executável por fase

Cada item é verificável — ou passa, ou não passa. Marco conforme avanço.
Ao final de cada fase, apresento o resultado e espero aprovação antes de seguir.

---

## Onde estamos — checkpoint de 20/08/2026

**Fases 2, 3 e 4 concluídas.** Faltam a 5, a 5.5 e a 6.

| | |
|---|---|
| Commits | 9, todos no GitHub (repositório privado) |
| Suíte | **169 testes verdes**; 26 ainda vermelhos por desenho (Fase 5) |
| Cobertura nos módulos de cálculo | **93%** (meta: 90%) |
| `ruff`, `ruff format`, `mypy` | limpos |
| Funil de qualidade | **0,00% de desvio** nas 10 etapas |
| Universo final | **975 fundos** — 854 varejo, 69 qualificado, 52 profissional |
| Tempo de execução | 6,3M linhas lidas, validadas e reduzidas a painel em **~4s** |

**Números já apurados sobre os dados reais:** CDI 2025 = 14,3242% em 252 dias úteis ·
apenas **37% dos fundos bateram o CDI** · mediana do excesso = **−0,22%**.

### Decisão aberta, aguardando o Rafael

Depois da resposta da Decade (*"foque no que for mais acionável para o varejo"*), medi que
**58% do universo de varejo é D+0**. Um ranking único de varejo entregaria os mesmos cinco
fundos para quem precisa do dinheiro amanhã e para quem investe por três anos.

Proposta: reabrir a D-010 e passar de dois perfis (varejo / qualificado) para **dois perfis de
varejo por horizonte** — liquidez (D+0/D+1, 492 fundos) e prazo (D+2 a D+30, 232 fundos) —
mantendo o qualificado como apêndice declarado como amostra enviesada (69 fundos, 28% de
divulgação). **Não implementar até haver decisão.**

### O que depende do Rafael, não de mim

- [ ] **Conferir 3 fundos na planilha.** Pegar a cota de 02/01/2025 e 30/12/2025 de três fundos,
      calcular o retorno e comparar com o `ranking.json`. É a verificação independente mais
      valiosa do projeto: eu não sou testemunha confiável do meu próprio cálculo.
- [ ] Decidir a questão dos perfis acima.
- [ ] Olhar o Top 5 quando sair e dizer se algum fundo parece estranho.

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

- [x] `baixar()` com retry (3 tentativas, espera crescente) e timeout explícito
- [x] Disjuntor: após 5 falhas seguidas no mesmo host, para de tentar e falha claro
- [x] Cache por hash — arquivo já baixado e íntegro não baixa de novo
- [x] `manifesto.json` com nome, tamanho, SHA-256 e horário de cada arquivo
- [x] Validação de que o download é mesmo um ZIP/CSV (a CVM devolve HTML de erro com HTTP 200)
- [ ] **Só o layout L3** (2024 em diante). L2 e L1 não foram escritos: a janela de 12 meses
      não os alcança. Ficam para quem quiser estender o histórico — o adapter L2→L3 é um
      rename de coluna, conforme medido na D-004
- [ ] **Schema Pandera declarado só para o informe diário**, que é a fronteira onde o dado ruim
      entra. As demais fontes são validadas pelos leitores (tipos explícitos, chave única,
      quarentena) mas sem modelo declarado. O IMA não entra — ver D-030
- [x] Quarentena: linhas rejeitadas vão para arquivo separado com o motivo
- [x] Freio de 5%: mais que isso rejeitado ⇒ pipeline para
- [x] `saida/relatorio_qualidade.md` com o funil comparado ao baseline

**Verificação:** o funil bate com o baseline do `CLAUDE.md` dentro da tolerância.

---

## Fase 4 — Junção e métricas (D4–D5 · 23–24/08)

**Entregável:** uma linha por fundo com os dez números.

- [x] Junção classe ⨝ fundo ⨝ extrato/lâmina ⨝ série ⨝ CDI ⨝ IMA
- [x] **Teste de junção:** contagem antes e depois bate; nenhum fundo duplicado
- [ ] **Calendário de dias úteis não é explícito.** O conjunto de dias vem da própria série do
      CDI publicada pelo Banco Central, que só tem dia útil. Funcionou — deu exatamente 252
      dias em 2025 — mas é inferência, não declaração. Um feriado que a fonte publique por
      engano passaria
- [x] Escolha point-in-time do registro de extrato vigente em `data_ref`
- [x] Métricas implementadas: rentabilidade, ganho sobre benchmark, oscilação,
      retorno por unidade de risco, pior queda, dias no vermelho, taxa, prazo,
      tamanho, estabilidade do passivo
- [ ] **Benchmark por grupo não entrou.** CDI para todos. Medido antes de decidir: 91,8% do
      varejo é servido por CDI, 8,2% seria IMA-B, prefixado puro é zero. O arquivo do IMA é
      Excel binário e a alternativa em texto é foto do dia, não série. Ver D-030
- [x] Invariantes testadas (lista no `CLAUDE.md`)
- [~] **Dois** fundos conferidos contra cálculo independente (`tests/conftest.py`), mas o
      cálculo é meu. A conferência em planilha, por outra pessoa, continua pendente e está
      na lista do Rafael acima

**Verificação:** rentabilidade de 2 fundos bate até a 9ª casa decimal com um cálculo feito
fora do código. Falta a conferência humana independente.

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
