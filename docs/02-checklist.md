# Checklist executável por fase

Cada item é verificável: ou passa, ou não passa. Marco conforme avanço.
Ao final de cada fase, apresento o resultado e espero aprovação antes de seguir.

---

## Onde estamos: PROJETO ENTREGUE (21/08/2026)

**Todas as fases concluídas.**

| | |
|---|---|
| Suíte | **288 testes verdes** · cobertura 93% nos módulos de cálculo |
| `ruff`, `ruff format`, `mypy` | limpos |
| Funil de qualidade | dentro do baseline, 0,00% de desvio |
| Universo | **580 fundos** de 36.594 classes · 559 varejo |
| Janela | 12 meses = **01/01/2025 a 31/12/2025**, 252 dias úteis, CDI 14,3242% |
| Execução | `uv run ranking --reference-date 2025-12-31`, ~40 s |
| Validação | `uv run ranking --reference-date 2025-12-31 --validate`, minutos |
| Automação | rodando às segundas, 09:00 UTC, comitando em `saida/` |
| **Teste no passado** | **validado**, com liquidez 2/3 e prazo 3/3, contra o critério de 2/3 por perfil (D-044) |

Entregáveis versionados em `saida/`: `ranking.md` · `ranking.json` · `ranking.html` ·
`relatorio_qualidade.md` · `validacao.md`. Mais `README.md`, `docs/` e o repositório.

### O que o veredito de "validado" quer dizer, e o que não quer

Passou no critério congelado antes de rodar. E, na mesma tabela: o Top 5 bateu a mediana dos
elegíveis em **2 de 6** recortes e ficou **abaixo do CDI nos 6**, com vantagem entre −15 e
+21 pontos-base. As medições saem do painel validado inteiro, não do universo elegível no fim,
justamente para que fundo que saiu do universo entre na conta. Ver D-044.

### O que falta, e é tudo do Rafael

- [ ] **Gravar o vídeo de 5 min.** Roteiro minutado e frases prontas em `docs/03-guia-de-defesa.md`.
- [ ] **Colocar o link do vídeo no README** depois de gravado.
- [ ] **Conferir 3 fundos na planilha.** Cota de 02/01/2025 e 30/12/2025 contra o
      `ranking.json`. Única verificação do cálculo que não passa por mim.
- [ ] **Decidir se o repositório vira público** antes de enviar à Decade.

---

## Fase 2: setup e esqueleto de testes (D1 · 20/08)

**Entregável:** projeto que instala do zero e roda uma suíte de testes **vermelha**.

- [x] `uv init` + `pyproject.toml` com a stack aprovada, nada além
- [x] Estrutura de pastas criada, cada uma com `__init__.py` e docstring de uma linha
- [x] `.gitignore` cobrindo `dados/`, `saida/`, `.venv`, `__pycache__`
- [ ] ~~`.pre-commit-config.yaml`~~ **Não feito, de propósito.** A CI aplica
      exatamente os mesmos portões (ruff, format, mypy, pytest) a cada push.
      Um hook local que ninguém instalou é teatro, não guardrail.
- [x] `Dockerfile`. **Desvio declarado:** a imagem é de execução e não de teste
      (`tests/` fica fora via `.dockerignore`). A CI builda a imagem e roda a CLI
      dentro dela; os testes rodam no job de qualidade, que é onde fazem sentido.
- [x] `configs/universe.yaml`, `configs/profiles.yaml`, `configs/sources.yaml` escritos
- [x] Fixtures reais e pequenas em `tests/fixtures/` (20 fundos × 60 dias, congeladas)
- [x] **Testes escritos e falhando** para: as armadilhas conhecidas, as invariantes financeiras,
      os contratos de cada etapa, o pipeline ponta a ponta
- [x] `README.md` esqueleto com o comando de execução
- [x] Repositório Git iniciado, primeiro commit, branch `main` protegida mentalmente
      (trabalho em `feat/*` e faço merge)
- [x] **GitHub Actions**: workflow que instala do zero e roda a suíte a cada push
- [x] **Comando `/fim-de-fase`** em `.claude/commands/`: testes, funil, diário, trade-offs

**Verificação:** `uv run pytest` roda e falha com mensagens claras, não com `ImportError`.

---

## Fase 3: extração e validação (D2–D3 · 21–22/08)

**Entregável:** dados brutos baixados, validados e materializados.

- [x] `baixar()` com retry (3 tentativas, espera crescente) e timeout explícito
- [x] Disjuntor: após 5 falhas seguidas no mesmo host, para de tentar e falha claro
- [x] Cache por hash: arquivo já baixado e íntegro não baixa de novo
- [x] `manifesto.json` com nome, tamanho, SHA-256 e horário de cada arquivo
- [x] Validação de que o download é mesmo um ZIP/CSV (a CVM devolve HTML de erro com HTTP 200)
- [ ] **Só o layout L3** (2024 em diante). L2 e L1 não foram escritos: a janela de 12 meses
      não os alcança. Ficam para quem quiser estender o histórico, e o adapter L2→L3 é um
      rename de coluna, conforme medido na D-004
- [ ] **Schema Pandera declarado só para o informe diário**, que é a fronteira onde o dado ruim
      entra. As demais fontes são validadas pelos leitores (tipos explícitos, chave única,
      quarentena) mas sem modelo declarado. O IMA não entra: ver D-030
- [x] Quarentena: linhas rejeitadas vão para arquivo separado com o motivo
- [x] Freio de 5%: mais que isso rejeitado ⇒ pipeline para
- [x] `saida/relatorio_qualidade.md` com o funil comparado ao baseline

**Verificação:** o funil bate com o baseline do `CLAUDE.md` dentro da tolerância.

---

## Fase 4: junção e métricas (D4–D5 · 23–24/08)

**Entregável:** uma linha por fundo com os dez números.

- [x] Junção classe ⨝ fundo ⨝ extrato/lâmina ⨝ série ⨝ CDI ⨝ IMA
- [x] **Teste de junção:** contagem antes e depois bate; nenhum fundo duplicado
- [ ] **Calendário de dias úteis não é explícito.** O conjunto de dias vem da própria série do
      CDI publicada pelo Banco Central, que só tem dia útil. Funcionou, e deu exatamente 252
      dias em 2025, mas é inferência e não declaração. Um feriado que a fonte publique por
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

## Fase 5: ranking e saída (D6 · 25/08)

**Entregável:** Top 5 por perfil, com grau de confiança.

- [x] Percentil dentro do grupo ANBIMA, com winsorização a 1%/99%
- [x] Grupo com menos de 20 fundos é comparado contra o **universo inteiro**, não contra um
      grupo pai inventado. A saída registra qual dos dois aconteceu
- [x] Pesos lidos de `configs/profiles.yaml`, soma validada em 100
- [x] Elegibilidade por perfil aplicada **antes** do percentil, não depois
- [x] Reamostragem em blocos: 1.000 simulações, semente fixa
- [x] Sorteio de pesos dentro das faixas configuradas
- [x] **Estabilidade reportada separando** o que varia do que não varia
      (a taxa é constante e infla a aparência de robustez, e isso precisa ser declarado)
- [x] `ranking.json` validado contra o schema Pydantic de saída
- [x] `ranking.md` legível, com um parágrafo real por fundo
- [x] CLI funciona; funções importáveis funcionam

**Verificação:** rodar duas vezes produz JSON idêntico, exceto `generated_at`, que é
proveniência e não resultado. Verificado por teste.

**Pendente da revisão (D-035), a fazer na Fase 6:** o `ranking.md` volta a ser lista simples,
com a taxa de aparição no JSON e na seção técnica.

---

## Fase 5.5: teste no passado (D7 manhã · 26/08)

**Entregável:** `saida/validacao.md` respondendo se o método funciona.

**Regra que vale antes de tudo:** o critério de sucesso e a regra do fundo descontinuado
estão escritos na seção 8.1 do desenho e **não podem ser alterados depois de ver o resultado**.
Se eu sentir vontade de mexer, é sinal de que o resultado não agradou, e é exatamente aí que
não se mexe.

- [x] Rodar o pipeline com `--reference-date` em 2025-03-31, 2025-06-30 e 2025-09-30
- [x] **Auditoria de point-in-time:** confirmar que nenhuma linha posterior à data de corte
      entrou. Se entrou, é bug grave na Etapa 1 e o teste inteiro está contaminado
- [x] Congelar os três Top 5 em arquivo, antes de medir qualquer coisa
- [x] Medir o retorno realizado de cada Top 5 no período seguinte (peso igual entre os cinco)
- [x] Comparar com a mediana dos elegíveis na data de corte
- [x] Comparar com o benchmark do grupo (CDI / IMA-B / IRF-M)
- [x] Gerar 1.000 carteiras de 5 fundos sorteados do universo elegível, com semente fixa
- [x] Reportar **o percentil do meu Top 5 na distribuição aleatória**, que é o número principal
- [x] Reportar quantos dos 5 bateram a mediana individualmente
- [x] Marcar fundos descontinuados no período, se houver
- [x] Aplicar o critério declarado: acima do percentil 60 em ao menos 2 das 3 datas
- [x] **Se falhar, escrever que falhou.** Não falhou, mas dois erros meus foram corrigidos
      na direção mais dura: o critério passou a ser aplicado **por perfil** (era 2 de 6
      pares, virou 2 de 3 por perfil), e o relatório mostra a vantagem em pontos-base ao
      lado do percentil, para ninguém ler p98% como ganho grande
- [x] Registrar o resultado em `docs/decisoes.md`, seja ele qual for

**Verificação:** `saida/validacao.md` existe, tem os três cortes × dois perfis, e a conclusão
está escrita em uma frase sem rodeio.

**Resultado:** validado. `varejo_liquidez` passou em 3 de 3 (p92, p100, p98); `varejo_prazo`
em 2 de 3 (p84, p97, p51). Vantagem sobre a mediana entre −8 e +31 pontos-base.

---

## Fase 6: documentação ✓

- [x] `README.md`: o que é, como instalar, como rodar, o que sai, quanto demora, e o que o
      método **não** faz
- [x] `ranking.md` como **lista simples**: a taxa de aparição saiu da vitrine e vive no
      `ranking.json` e na seção técnica (D-035, ponto 4)
- [x] **Duas limitações em destaque** acima das outras: risco de crédito escondido e doze
      meses não preverem 2026
- [x] Concentração em poucas gestoras declarada e explicada
- [x] **Arbitrariedade dos pesos** nomeada como limitação de primeira ordem, com o argumento
      de que o projeto entrega a máquina e não os pesos ótimos
- [x] `docs/decisoes.md` consolidado: 46 decisões, 6 reversões preservadas
- [x] **Execução automática construída e comprovada** (`weekly-ranking.yml`). Rodou sozinha e
      publicou o commit `76102a4`. O gatilho agendado fica comentado enquanto o case está
      sendo avaliado, para que `saida/` não seja sobrescrito; o disparo manual continua
- [x] **Página visual do ranking** (`saida/ranking.html`), regenerada a cada execução e com o
      veredito do teste no passado embutido
- [ ] Vídeo de 5 min. Roteiro minutado pronto em `docs/decisoes.md`, gravação é do Rafael
- [ ] Link do vídeo no README, depois de gravado

## D8: vídeo e revisão final

- [ ] Vídeo ≤ 5 min: desenho · a decisão que menos me convence · caminho para produção
- [ ] Revisão final do repositório com olhar de quem nunca viu
- [x] Tag `v1.0.0`

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
