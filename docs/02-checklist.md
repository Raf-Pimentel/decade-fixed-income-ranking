# Estado do projeto, e o que foi deixado de fora

Este arquivo responde três perguntas: onde o projeto está, o que **não** foi feito e por quê, e
o que ainda falta. O histórico de execução fase a fase vive no diário de decisões.

---

## Onde estamos

| | |
|---|---|
| Suíte | **309 testes verdes** · cobertura 93% nos módulos de cálculo |
| `ruff`, `ruff format`, `mypy` | limpos |
| Funil de qualidade | dentro do baseline |
| Universo | **514 fundos** de 36.594 classes · 496 varejo |
| Perfis | 195 elegíveis na reserva de emergência · 348 no de dois anos |
| Janela | 12 meses, **01/01/2025 a 31/12/2025**, 252 dias úteis, CDI 14,3242% |
| Execução | `uv run ranking --reference-date 2025-12-31`, cerca de 40 s |
| Validação | acrescentar `--validate`, alguns minutos |
| Automação | construída e comprovada pelo commit `76102a4`, agendamento comentado |
| Teste no passado | **validado**, 3/3 nos dois perfis contra o critério de 2/3 |
| Decisões registradas | 49, com 6 reversões preservadas |
| Tag | `v1.0.0` |

Entregáveis versionados em `saida/`: `ranking.md` · `ranking.json` · `ranking.html` ·
`relatorio_qualidade.md` · `validacao.md` · `top10.md`.

### O que o veredito de "validado" quer dizer, e o que não quer

Passou no critério congelado antes de rodar. E, na mesma tabela: o Top 5 bateu a mediana dos
elegíveis em **6 de 6** recortes, com vantagem entre **+8 e +22 pontos-base**, e ficou **abaixo
do CDI nos 6**. As medições saem do painel validado inteiro, não do universo elegível no fim,
justamente para que fundo que saiu do universo entre na conta.

Esses números eram 2 de 6, com vantagem de −15 a +21 pontos-base, até 24/08. O que mudou foi a
taxa deixar de ser lida no extrato e passar a ser medida contra o fundo que cada classe compra.
O critério de sucesso não se moveu, e a regra foi escrita antes daquela execução. Ver D-047.

---

## O que foi deliberadamente não feito

Cada item aqui é uma escolha com motivo, não uma pendência esquecida.

**Sem gancho de pré-commit.** A CI aplica exatamente os mesmos portões, `ruff`, `format`,
`mypy` e `pytest`, a cada push. Um hook local que ninguém instalou é teatro, não guardrail. A
consequência aceita é que rodar a suíte antes de commitar é responsabilidade manual.

**A imagem Docker é de execução, não de teste.** `tests/` fica fora via `.dockerignore`. A CI
constrói a imagem e roda a CLI dentro dela; os testes rodam no job de qualidade, que é onde
fazem sentido.

**Só o layout L3 do informe diário** (2024 em diante). L2 e L1 não foram escritos porque a
janela de doze meses não os alcança. O adapter L2→L3 é um rename de coluna, conforme medido em
D-004.

**Schema Pandera declarado só para o informe diário**, que é a fronteira por onde o dado ruim
entra. As demais fontes são validadas pelos leitores, com tipos explícitos, chave única e
quarentena, mas sem modelo declarado.

**O calendário de dias úteis não é explícito.** O conjunto de dias vem da própria série do CDI
do Banco Central, que só publica dia útil. Funcionou e deu exatamente 252 dias em 2025, mas é
inferência e não declaração: um feriado que a fonte publicasse por engano passaria.

**Benchmark por grupo não entrou.** CDI para todos. Medido antes de decidir: 91,8% do varejo é
corretamente servido pelo CDI, 8,2% precisaria de IMA-B, e prefixado puro é zero. O arquivo do
IMA é Excel binário e a alternativa em texto é foto do dia, não série histórica. Ver D-030.

**A conferência do cálculo ainda não passou por outra pessoa.** Dois fundos batem até a nona
casa decimal contra um cálculo independente em `tests/conftest.py`, mas esse cálculo também é
meu. A conferência em planilha continua pendente e está na lista abaixo.

**O agendamento semanal está comentado.** O workflow rodou sozinho e publicou o commit
`76102a4`, então a automação está comprovada. O gatilho fica desligado enquanto o case é
avaliado, para que `saida/` não seja sobrescrito com números que ninguém conferiu. O disparo
manual continua valendo.

Duas limitações de método que também são escolhas, e estão explicadas no desenho: **os pesos
são declarados e não deduzidos**, e **o corte de cotistas não separa varejo de institucional**.

---

## O que falta

- [ ] **Gravar o vídeo de 5 min.**
- [ ] **Colocar o link do vídeo no README** depois de gravado.
- [ ] **Conferir 3 fundos na planilha.** Cota de 02/01/2025 e 30/12/2025 contra o
      `ranking.json`. É a única verificação do cálculo que não passa por mim.
- [ ] **Revisão final do repositório** com olhar de quem nunca viu.

---

## Guardrails de processo

| Momento | Pergunta que eu faço | Se a resposta for não |
|---|---|---|
| Antes de escrever função | Existe teste vermelho? | escrevo o teste |
| Antes de adicionar biblioteca | Está na stack aprovada? | justifico no doc ou desisto |
| Antes de criar abstração | Tem 2+ usos concretos hoje? | escrevo direto, sem abstrair |
| Antes de commitar | Suíte verde, `ruff` e `mypy` limpos? | conserto antes |
| Ao achar número no código | Deveria estar em YAML? | movo |
| Ao terminar etapa | Funil bate com o baseline? | investigo antes de seguir |
| Ao terminar fase | Trade-offs listados? | listo e apresento |
