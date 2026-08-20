# CLAUDE.md — contrato de trabalho deste projeto

> Leia este arquivo antes de escrever qualquer linha de código. Ele existe para me
> impedir de derivar do plano, de reintroduzir complexidade cortada, e de esquecer
> armadilhas já descobertas. Se algo aqui conflitar com uma ideia nova, **este arquivo ganha**
> — a menos que haja decisão explícita em contrário.

## O que é o projeto

Ranking dos 5 melhores fundos de renda fixa brasileiros em 31/12/2025, por perfil de
cliente (varejo e qualificado), a partir de dados públicos da CVM e da ANBIMA.
Entrega: repositório GitHub + `ranking.md` + `ranking.json` + README + vídeo de 5 min.
Prazo: **28/08/2026, 20h**.

Desenho completo: `docs/01-solution-design.md`. Checklist executável: `docs/02-checklist.md`.
Diário de decisões: `docs/decisoes.md`.

**Fases:** 1 planejamento (feita) · 2 setup e TDD · 3 extração e validação · 4 junção e
métricas · 5 ranking e saída · **5.5 teste no passado** · 6 documentação.

---

## As 10 regras inegociáveis

1. **Teste antes do código.** Nenhuma função nasce sem um teste que falha primeiro.
   Se eu me pegar escrevendo implementação sem teste vermelho, paro e escrevo o teste.
2. **Nenhum dado atravessa etapa sem passar por um schema declarado.** Os schemas
   ficam em `src/ranking/contratos/`. Validação é explícita, nunca implícita.
3. **Point-in-time sempre.** Toda função recebe `data_ref`. Nenhuma linha com data
   posterior entra no cálculo. Sem exceção, nem "só para testar".
4. **Rodar duas vezes com a mesma `data_ref` dá o mesmo resultado.** Se não der,
   é bug, não característica.
5. **Toda decisão não óbvia vira uma entrada em `docs/decisoes.md` no momento em que é
   tomada** — nunca no final do projeto. Se eu reverter uma decisão, **não apago a original**:
   abro entrada nova marcada como reversão. As reversões são o material mais valioso da
   apresentação final. Ao fim de cada fase, alimento também as seções "Surpresas",
   "Números que valem citar" e "Esqueleto do vídeo" do mesmo arquivo.
6. **Nenhuma dependência nova sem justificativa escrita.** A lista aprovada está abaixo.
7. **Números mágicos moram em YAML**, nunca no código. Universo, pesos, janelas, cortes.
8. **Se o funil de elegibilidade divergir do baseline** (tabela abaixo) em mais de 5%,
   o pipeline para e eu investigo antes de seguir.
9. **Commit só com a suíte verde.** Sem `--no-verify`, sem teste comentado, sem `skip`
   que não tenha um motivo escrito ao lado.
10. **Parar e apresentar a cada etapa, não só a cada fase.** O ritmo definido é
    de aprovação por etapa (ex.: dentro da Fase 3, apresento a extração, espero o ok, depois
    a validação). Objetivo: dominar o código o suficiente para defendê-lo no vídeo — módulo
    que não se consegue explicar em duas frases é módulo para simplificar ou apagar.
11. **Proibido ajustar pesos, cortes ou métricas depois de ver o resultado do teste no passado
    (Fase 5.5).** Se eu mexer até passar, não validei nada — decorei o segundo semestre de 2025.
    O critério de sucesso está congelado na seção 8.1 do desenho. Resultado ruim se reporta,
    não se conserta.

---

## Armadilhas dos dados — já custaram investigação, não redescobrir

| # | Armadilha | Defesa obrigatória |
|---|---|---|
| 1 | **O informe diário é por CLASSE, não por fundo**, desde jan/2024. As colunas são `CNPJ_FUNDO_CLASSE` e `ID_SUBCLASSE`. Usar o formato antigo cruza errado **e não gera erro nenhum** | Teste que falha se a coluna esperada não existir; join sempre por `cnpj_classe` normalizado |
| 2 | **`cad_fi.csv` está obsoleto.** Cobre 10,3% das classes de renda fixa e tem 0% de `TAXA_ADM` preenchida | Taxa e prazo vêm de `EXTRATO` e `LAMINA`. `cad_fi.csv` só como último recurso |
| 3 | **`Data_Inicio` do registro NÃO é a idade do fundo** — é a data de adaptação à RCVM 175 (idêntica a `Data_Adaptacao_RCVM175`). 66% do universo parece ter menos de 1 ano; a idade real mediana é **7,4 anos** | Idade sempre de `registro_fundo.Data_Constituicao` ou da 1ª cota observada. Teste com o caso `00068305000135` (registro diz 2025-05-12, real é 1994-05-26) |
| 4 | **CNPJ vem em dois formatos.** `registro_classe`: `00332266000131` · `inf_diario`: `00.017.024/0001-53` | Normalizar para 14 dígitos na leitura, sempre. Teste de propriedade |
| 5 | **Linhas de subclasse duplicam a série.** `ID_SUBCLASSE` preenchido = linha de subclasse | Filtrar `ID_SUBCLASSE` nulo para obter o nível classe |
| 6 | **A CVM sobrescreve arquivos** em retificação, sem versionar | `manifesto.json` com SHA-256 de cada arquivo baixado |
| 7 | **Encoding é `latin-1`, separador `;`** | Fixado no leitor, com teste de regressão |
| 8 | **Amortização derruba a cota sem prejuízo real** | Variação diária > 20% é marcada, **não descartada** |

---

## Baseline de qualidade — o funil tem que bater

Medido em 19/08/2026 sobre os arquivos reais. **É o teste de regressão dos dados.**
Se o pipeline produzir números diferentes, ou a CVM mudou algo ou eu quebrei alguma coisa.

| Etapa | Esperado | Tolerância |
|---|---:|---|
| Classes no registro | 36.598 | ±2% |
| Classificação = Renda Fixa | 7.759 | ±2% |
| Em funcionamento normal | 7.337 | ±2% |
| Condomínio aberto | 6.580 | ±2% |
| Não exclusivo | 3.498 | ±2% |
| Com série em dez/25 | 3.268 | ±2% |
| PL ≥ R$ 10 mi | 2.944 | ±3% |
| ≥ 10 cotistas | **1.801** | ±3% |
| Com taxa e prazo publicados | **1.003** | ±3% |
| — dos quais Público Geral | 871 | ±3% |
| — dos quais Qualificado | 79 | ±5% |

Cobertura histórica esperada: 12m = 1.675 (93%) · 24m = 1.481 (82%) · 36m = 1.326 (74%).

Este funil é impresso a cada execução em `saida/relatorio_qualidade.md`.

---

## Ciclo TDD que eu sigo

Para cada unidade de trabalho, nesta ordem, sem pular:

1. **Vermelho** — escrevo o teste com o caso mais simples possível. Rodo. Vejo falhar.
   Se passar de primeira, o teste está errado.
2. **Verde** — escrevo o mínimo para passar. Feio é permitido aqui.
3. **Refatoro** — limpo com a suíte verde. Só agora penso em elegância.
4. **Caso de borda** — adiciono o teste do caso chato (série vazia, um ponto só, todos
   os valores iguais, NaN no meio, fundo que nasceu no meio do período).
5. **Commit** — mensagem no formato `tipo(escopo): descrição`.

**Ordem de escrita dentro de cada etapa:** contrato de dados → teste → função → integração.

### Onde os testes são obrigatórios

| Tipo | Onde | O que garante |
|---|---|---|
| **Invariante financeira** | toda função de `metricas/` | cota constante ⇒ retorno 0 · cota que dobra ⇒ 100% · retorno diário composto = retorno ponta a ponta · drawdown ≤ 0 · vol ≥ 0 |
| **Contrato** | toda fronteira de etapa | schema, tipos, obrigatoriedade, faixas, unicidade |
| **Armadilha** | uma por linha da tabela acima | regressão das 8 armadilhas conhecidas |
| **Integração** | pipeline completo | roda ponta a ponta em fixture pequena e produz o JSON válido |
| **Golden file** | saída final | o `ranking.json` de uma fixture congelada não muda sem eu querer |

Fixtures ficam em `tests/fixtures/`: recortes **reais e pequenos** (20 fundos, 60 dias),
congelados no repositório. Nunca baixar da internet dentro de um teste.

---

## Stack aprovada — nada além disto sem justificar

`polars` · `numpy` · `httpx` · `tenacity` · `pandera` · `pydantic` · `typer` · `pyyaml`
· `pytest` · `pytest-cov` · `ruff` · `mypy` · `uv`

## Lista negra — já foi avaliado e cortado, não reintroduzir

DuckDB · Spark/Dask · Airflow/Prefect/Dagster · camadas bronze/silver/gold ·
structlog · Great Expectations · banco de dados · API REST · cache distribuído ·
mais de 2 perfis de cliente · qualquer abstração com "Factory", "Manager" ou "Strategy" no nome.

**Regra de ouro contra overengineering:** se um componente não aparece no
`docs/01-solution-design.md`, ele não deveria existir. Se eu achar que precisa, atualizo
o documento primeiro e explico por quê.

---

## Definition of Done de uma fase

Uma fase só está pronta quando **todas** forem verdadeiras:

- [ ] Suíte verde, sem `skip` sem motivo escrito
- [ ] Cobertura ≥ 90% nos módulos de cálculo (o resto não tem meta)
- [ ] `ruff check` e `mypy` limpos
- [ ] Funil de qualidade dentro da tolerância do baseline
- [ ] Decisões novas registradas em `docs/decisoes.md`
- [ ] Roda do zero: `docker build` + `docker run` funciona
- [ ] Apresentado para revisão, com trade-offs listados

## Extras aprovados (20/08)

| Extra | Quando | O que é |
|---|---|---|
| **Execução automática real** | Fase 2 monta, Fase 6 valida | GitHub Actions roda o pipeline do zero semanalmente e publica o `ranking.json`. Converte "seria viável rodar diariamente" em "está rodando". Também serve de CI |
| **Comando `/fim-de-fase`** | Fase 2 | Roda testes, confere o funil contra o baseline, atualiza `docs/decisoes.md` e monta o resumo de trade-offs |
| **Página visual do ranking** | Fase 6 | Top 5, métricas e resultado do teste no passado, para o vídeo e a apresentação |

**Recusado:** gancho automático de testes. Consequência: **rodar a suíte é responsabilidade
minha e manual.** Nunca declarar "pronto" sem ter rodado e colado a saída.

## Comandos

```bash
uv sync                                  # instalar
uv run pytest -q                         # testes
uv run pytest --cov=src --cov-report=term-missing
uv run ruff check . && uv run mypy src   # qualidade
uv run python -m ranking --data-ref 2025-12-31
```

## Fontes de dados (URLs verificadas em 19/08/2026)

| Dado | URL |
|---|---|
| Informe diário | `https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_YYYYMM.zip` |
| Registro fundo/classe | `https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip` |
| Extrato | `https://dados.cvm.gov.br/dados/FI/DOC/EXTRATO/DADOS/extrato_fi_YYYY.csv` |
| Lâmina | `https://dados.cvm.gov.br/dados/FI/DOC/LAMINA/DADOS/lamina_fi_YYYYMM.zip` |
| CDI (BCB série 12) | `https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json` |
| ANBIMA IMA | `https://www.anbima.com.br/informacoes/ima/arqs/ima_completo.xls` |
