# Diário de decisões

Registro corrido de cada decisão do projeto, escrita **no momento em que foi tomada**.
Serve para dois fins: impedir que se refaça discussão já encerrada, e deixar pronto o
material pronto para a apresentação final sem precisar reconstruir a trajetória de memória.

**Como uso:** toda decisão não óbvia vira uma entrada, na hora. Se eu reverter uma decisão,
**não apago a original** — abro uma nova entrada marcada como reversão e explico o que mudou.
As reversões são a parte mais valiosa deste arquivo.

**Legenda:** 🎥 = vale entrar no vídeo · 🔄 = reverte uma decisão anterior · 📊 = sustentada por número medido

---

## Linha do tempo

| # | Data | Fase | Decisão | |
|---|---|---|---|---|
| [D-001](#d-001) | 19/08 | 1 | Unidade de análise é a classe, não o fundo | 🎥📊 |
| [D-002](#d-002) | 19/08 | 1 | Taxas vêm do Extrato e da Lâmina, não do `cad_fi.csv` | 🎥📊 |
| [D-003](#d-003) | 19/08 | 1 | Idade do fundo não sai do campo `Data_Inicio` | 🎥📊 |
| [D-004](#d-004) | 19/08 | 1 | Janela de 12 meses | 📊 |
| [D-005](#d-005) | 19/08 | 1 | Arquitetura elaborada: medallion, DuckDB, orquestrador | |
| [D-006](#d-006) | 19/08 | 1 | Três perfis de cliente | |
| [D-007](#d-007) | 19/08 | 1 | ANBIMA descartada por exigir credencial | |
| [D-008](#d-008) | 20/08 | 1 | Comparar cada fundo só dentro do seu grupo | 🎥 |
| [D-009](#d-009) | 20/08 | 1 | **Cortar a infraestrutura** | 🔄 |
| [D-010](#d-010) | 20/08 | 1 | **Dois perfis, não três** | 🔄 |
| [D-011](#d-011) | 20/08 | 1 | Simulação de robustez no ranking | 🎥 |
| [D-012](#d-012) | 20/08 | 1 | Taxa pesa mais que rentabilidade no varejo | 🎥 |
| [D-013](#d-013) | 20/08 | 1 | Só entra fundo com taxa e prazo publicados | 📊 |
| [D-014](#d-014) | 20/08 | 1 | **ANBIMA volta, pelos índices públicos** | 🔄🎥 |
| [D-015](#d-015) | 20/08 | 1 | Funil medido vira teste de regressão | 🎥 |
| [D-016](#d-016) | 20/08 | 1 | Disjuntor restaurado na extração | 🔄 |
| [D-017](#d-017) | 20/08 | 1 | Fase 5.5: testar o método no passado, com critério declarado antes | 🎥 |
| [D-018](#d-018) | 20/08 | 1 | Automação real, aprovação por etapa, e o repo tem que ser defensável | 🎥 |
| [D-019](#d-019) | 20/08 | 2 | Python 3.12 isolado pelo uv; Docker validado pela CI, não localmente | |
| [D-020](#d-020) | 20/08 | 2 | Código em inglês, documentos de trabalho em português | |
| [D-021](#d-021) | 20/08 | 2 | Valores esperados dos testes calculados fora do código | 🎥 |
| [D-022](#d-022) | 20/08 | 2 | CI vermelha de propósito até a Fase 5 | 🎥 |
| [D-023](#d-023) | 20/08 | 2 | Sem pre-commit: a CI já aplica os mesmos portões | |
| [D-024](#d-024) | 20/08 | 3 | O registro da CVM tem linhas repetidas e o join inflava o universo | 🎥📊 |
| [D-025](#d-025) | 20/08 | 3 | O disjuntor conta requisições, não arquivos | |
| [D-026](#d-026) | 20/08 | 3 | O Banco Central recusa janelas longas: a URL do CDI precisa de datas | 📊 |

---

## D-001 — A unidade de análise é a classe, não o fundo 🎥📊
**Quando:** 19/08, Fase 1 · **Situação:** definir o grão do pipeline

Abri o arquivo real antes de escrever qualquer código. O informe diário de dez/2025 tem as
colunas `TP_FUNDO_CLASSE`, `CNPJ_FUNDO_CLASSE` e `ID_SUBCLASSE` — a Resolução CVM 175
reorganizou os fundos em classes, e desde **janeiro de 2024** o dado é publicado por classe.

**Decisão:** todo o pipeline trabalha no grão de classe, com `cnpj_classe` como chave.

**Por quê:** é o que a fonte publica hoje. Qualquer reconciliação para o grão antigo seria
invenção minha.

**O que aceito perder:** séries anteriores a 2021 ficam menos acessíveis.

**Por que importa para a apresentação:** quem escreve o código assumindo o formato antigo
faz o cruzamento errado **e não recebe erro nenhum** — o programa roda e entrega números
errados em silêncio. É o tipo de erro que só se evita indo olhar o arquivo.

---

## D-002 — Taxas vêm do Extrato e da Lâmina 🎥📊
**Quando:** 19/08, Fase 1 · **Situação:** de onde tirar taxa de administração

Testei o `cad_fi.csv`, que é o arquivo que aparece em qualquer tutorial de dados da CVM.
Medi: cobre **10,3%** das classes de renda fixa de hoje e tem **0%** de `TAXA_ADM` preenchida.
Está obsoleto desde a RCVM 175.

**Decisão:** taxa e prazo de resgate vêm de `extrato_fi_YYYY.csv` (117 colunas) e da lâmina.

**Alternativa descartada:** insistir no `cad_fi.csv` com imputação — seria imputar 100% do dado.

---

## D-003 — A idade do fundo não sai do `Data_Inicio` 🎥📊
**Quando:** 19/08, Fase 1 · **Situação:** definir filtro de maturidade mínima

O campo `Data_Inicio` do registro de classes é idêntico ao `Data_Adaptacao_RCVM175`. Ou seja:
é a data em que o fundo se adaptou à nova regra, não a data em que nasceu.

| CNPJ | `Data_Inicio` | Constituição real |
|---|---|---|
| 00068305000135 | 2025-05-12 | 1994-05-26 |
| 00089915000115 | 2024-10-01 | 1994-06-21 |

Pelo campo errado, 66% do universo teria menos de 1 ano. Pela data real, a idade mediana é
**7,4 anos**.

**Decisão:** idade sempre de `registro_fundo.Data_Constituicao` ou da primeira cota observada.
Vira teste automatizado com o CNPJ `00068305000135` como caso.

**Impacto se eu não tivesse notado:** um filtro inocente de "fundos com mais de um ano"
descartaria dois terços do universo, incluindo fundos de trinta anos.

---

## D-004 — Janela de 12 meses 📊
**Quando:** 19/08, Fase 1 · **Situação:** quanto histórico usar

Medi a cobertura real das 1.801 classes conforme estico a janela: 6m = 97% · **12m = 93%** ·
24m = 82% · 36m = 74% · 60m = 61%. Cada ano a mais custa cerca de 10% do universo.

**Decisão:** 12 meses para pontuar; 3, 6 e 24 meses reportados junto. Parâmetro em YAML.

**Por quê:** além da cobertura, 2021–2023 teve a Selic indo de 2% a 13,75% — regime diferente
do de 2025. Janela longa também enche a amostra de fundos velhos e grandes que sobreviveram.

**Correção factual no meio do caminho:** eu havia afirmado que a quebra de layout era em
nov/2024. Fui verificar mês a mês: é **jan/2024**. Existem três layouts (2000–2020, 2021–2023,
2024 em diante), e converter o do meio para o atual é só renomear coluna — bem mais barato do
que eu tinha dito. O limite da janela é estatístico, não técnico.

---

## D-005 — Arquitetura elaborada *(revertida em D-009)*
**Quando:** 19/08, Fase 1

Propus camadas bronze/silver/gold, DuckDB junto com Polars, disjuntor, logging estruturado,
e um caminho de produção com orquestrador.

**Raciocínio na época:** demonstrar domínio de arquitetura de dados e um caminho de escala crível.

---

## D-006 — Três perfis de cliente *(revertida em D-010)*
**Quando:** 19/08, Fase 1

Varejo Liquidez, Varejo Rendimento e Qualificado.

---

## D-007 — ANBIMA descartada *(revertida em D-014)*
**Quando:** 19/08, Fase 1

Constatei que `data.anbima.com.br` exige credencial. Como a `Classificacao_Anbima` já vem
dentro do registro da CVM, concluí que dava para entregar sem a ANBIMA.

---

## D-008 — Comparar cada fundo só dentro do seu grupo 🎥
**Quando:** 20/08, Fase 1 · **Situação:** como normalizar métricas entre fundos diferentes

**Decisão:** cada métrica vira a posição relativa do fundo **dentro do seu grupo ANBIMA**, não
uma nota absoluta comparada com todo mundo.

**Por quê:** em 2025 os fundos que mais renderam foram os que tomaram mais risco de crédito.
Um ranking por rentabilidade, ou até por Sharpe global, entregaria automaticamente os cinco
fundos mais arriscados — e o problema deles simplesmente ainda não tinha aparecido. Comparar
um fundo de título público com um de dívida privada pela rentabilidade nominal não é comparar,
é premiar risco.

**O que aceito perder:** grupos pequenos dão percentil ruidoso. Mitigo fundindo grupos com
menos de 20 fundos ao grupo pai.

---

## D-009 — Cortar a infraestrutura 🔄
**Quando:** 20/08, Fase 1 · **Reverte:** D-005

A revisão apontou overengineering. Reavaliei e concordei.

**Decisão:** fora DuckDB, camadas de data lake, orquestrador, logging estruturado. Ficam
Polars, Parquet e uma pasta de saída.

**Por quê:** são ~1.000 fundos e ~200 MB. O projeto roda em minutos num notebook. Eu tinha
investido em infraestrutura de escala num problema que não tem problema de escala — e
economizado em estatística num problema que é inteiramente estatístico. Construí o encanamento
e não testei a água.

**O que fica:** validação de dados, point-in-time, manifesto com hash e testes. Esses carregam
peso de verdade — o dado da CVM é sujo e a CVM sobrescreve arquivo sem versionar.

---

## D-010 — Dois perfis, não três 🔄
**Quando:** 20/08, Fase 1 · **Reverte:** D-006

**Decisão:** Varejo e Qualificado.

**Por quê:** é a divisão que a própria CVM faz no campo `Publico_Alvo`, e é ela que determina
o que o cliente pode legalmente comprar. O terceiro perfil era invenção minha e triplicava o
trabalho de redação por ganho marginal.

---

## D-011 — Simulação de robustez no ranking 🎥
**Quando:** 20/08, Fase 1 · **Situação:** o ranking é confiável o suficiente para ser publicado como lista ordenada?

A revisão perguntou por que a simulação não tinha sido considerada. Foi ponto cego real: eu havia
escrito que a maior fraqueza do método era estimar qualidade com 12 meses de dados, e não
propus nenhuma ferramenta para **medir** essa incerteza.

Com 12 meses de dados diários, o erro sobre a medida de "retorno por unidade de risco" é da
ordem de **±1,5** — maior que as diferenças que eu ia ranquear. A diferença entre o 1º e o
15º colocado, muitas vezes, não existe.

**Decisão:** antes de publicar, mil simulações reembaralhando os retornos em blocos e sorteando
variações nos pesos. O Top 5 final são os cinco que mais aparecem no topo, e cada um sai com
o número: *"apareceu no Top 5 em 91% das simulações"*.

**Alternativa descartada:** simular trajetórias futuras a partir dos parâmetros estimados nos
mesmos 12 meses. Isso não adiciona informação — só reveste o número de falsa precisão.

**Limitação que declaro junto:** reembaralhar o que aconteceu nunca cria um evento que não
aconteceu. Se nenhum fundo teve problema de crédito em 2025, nenhuma simulação vai produzir um.
A simulação mede azar de amostra, não risco de cauda.

---

## D-012 — Taxa pesa mais que rentabilidade no varejo 🎥
**Quando:** 20/08, Fase 1 · **Situação:** definir os pesos

**Decisão:** no perfil varejo, taxa de administração pesa 25 e prazo de resgate 20, contra 15
de ganho sobre o benchmark.

**Por quê:** a taxa é o único número que se sabe com certeza sobre **2026**. A rentabilidade de
2025 é, em boa parte, benchmark que todo fundo pegou igual, mais um prêmio de crédito que ainda
não deu problema. A taxa vai ser cobrada no ano que vem exatamente como foi neste. Dar peso
maior ao que persiste é mais defensável do que dar peso maior ao que não persiste.

**Contraintuitivo?** Sim, e é justamente por isso que está documentado.

---

## D-013 — Só entra fundo com taxa e prazo publicados 📊
**Quando:** 20/08, Fase 1 · **Situação:** o que fazer com 44% do universo sem dado de taxa

**Decisão:** fundo sem taxa e prazo de resgate conhecidos não entra no ranking. Universo cai
de 1.801 para **1.003**.

**Por quê:** não é conveniência de dados — é o mínimo de uma recomendação responsável. Não dá
para indicar um fundo sem dizer ao cliente quanto ele custa e em quantos dias o dinheiro volta.

**Alternativa descartada:** imputar a taxa pela mediana do grupo. Rejeitada porque a taxa é o
maior peso do varejo; imputar o maior peso é inventar o resultado.

**Efeito colateral medido, e é desigual:**

| Público-alvo | Fundos | Com taxa e prazo | |
|---|---:|---:|---:|
| Público Geral | 1.369 | 871 | 64% |
| Qualificado | 278 | 79 | 28% |

**A lacuna é regulatória, não técnica:** fundos de varejo são obrigados a publicar lâmina;
fundos para qualificado têm obrigação mais leve. Isso enfraquece o ranking do perfil qualificado,
e vai declarado na entrega.

---

## D-014 — ANBIMA volta, pelos índices públicos 🔄🎥
**Quando:** 20/08, Fase 1 · **Reverte:** D-007

Testei o download direto: o Excel dos índices IMA responde 200 e baixa 257 KB **sem credencial**.
Só a base de fundos é fechada. Eu havia generalizado indevidamente a partir de uma parte da fonte.

**Decisão:** os índices IMA entram como fonte, e o benchmark passa a ser escolhido por grupo.

| Grupo | Comparado com |
|---|---|
| Pós-fixado, soberano curto, crédito | CDI |
| Indexado à inflação | IMA-B |
| Prefixado | IRF-M |

**Por quê isso melhora o resultado, e não é só cumprir requisito:** comparar todo fundo com o
CDI está errado. Um fundo de IMA-B parece péssimo contra o CDI num ano de juros altos, quando
na verdade só está fazendo exatamente o que promete. O "ganho sobre o benchmark" só significa
alguma coisa se o benchmark for o certo.

**Custo:** um arquivo a mais, um cruzamento a mais.

---

## D-015 — O funil medido vira teste de regressão 🎥
**Quando:** 20/08, Fase 1 · **Situação:** como garantir qualidade sem ferramenta pesada

Na Fase 1 medi o funil de elegibilidade nos arquivos reais: 36.598 classes → 7.759 renda fixa
→ … → 1.801 → 1.003.

**Decisão:** esses números viram o **baseline esperado**. Toda execução imprime o funil e compara.
Desvio acima da tolerância para o pipeline.

**Por quê:** é o teste de fumaça mais barato que existe aqui, e pega o erro mais perigoso. Um
cruzamento quebrado que corta metade do universo é praticamente invisível numa revisão de
código, mas grita num relatório que diz "esperado 1.003, obtido 412".

---

## D-016 — Disjuntor restaurado na extração 🔄
**Quando:** 20/08, Fase 1 · **Reverte:** parte de D-009

Ao revisar o pedido original, encontrei "tolerância a falhas (circuit breakers/retries)"
como requisito explícito. Eu tinha cortado o disjuntor junto com a infraestrutura.

**Decisão:** volta, na versão mínima — após 5 falhas seguidas no mesmo servidor, para de insistir
e falha com mensagem clara. São ~15 linhas.

**Lição registrada:** "sem overengineering" não autoriza remover requisito do cliente. Autoriza
implementá-lo da forma mais simples que funcione.

---

## D-017 — Testar o método no passado, com o critério declarado antes 🎥
**Quando:** 20/08, Fase 1 · **Situação:** o plano diz que o método é razoável, mas não mostra que funciona

Tudo o que eu tinha até aqui era argumento. Nada era evidência. É a primeira pergunta que
alguém experiente faz: *"tá, mas funciona?"*

**Decisão:** entra uma **Fase 5.5** entre o ranking e a documentação. Monto o ranking com dados
até três datas de corte de 2025 — 31/03, 30/06 e 30/09 — e meço como cada Top 5 se comportou
no período seguinte, que o ranking não viu.

**Contra o que comparo:** a mediana do grupo, o benchmark do grupo, e **1.000 carteiras de cinco
fundos sorteados ao acaso**. A terceira é a que importa: responde se meu método bate o acaso.
É o controle que quase ninguém faz.

**Por que cabe no prazo:** se o point-in-time estiver correto, cada rodada é um comando —
`python -m ranking --data-ref 2025-06-30`. Nenhum código novo. O custo está em medir e escrever,
não em programar. Isso é o retorno concreto da disciplina de point-in-time, que até agora era
só uma boa prática no papel. **E o teste audita a si mesmo:** se for difícil de rodar, é porque
o point-in-time está furado.

**Critério de sucesso, congelado antes de rodar:**
> acima do percentil 60 da distribuição de carteiras aleatórias em pelo menos 2 das 3 datas.

**Regra dura que vale mais que o resultado:** proibido mexer em pesos, cortes ou métricas depois
de ver o teste. Ajustar até passar não valida nada — decora o segundo semestre de 2025. É a
forma mais comum de fraudar a si mesmo em finanças quantitativas, e quase sempre é feita sem
má intenção. Virou a regra 11 do `CLAUDE.md`.

**E se falhar:** reporto que falhou e digo o que mudaria. Um método falseável que falhou é mais
sério que um Top 5 nunca testado.

**Detalhe decidido agora para não ser decidido convenientemente depois:** se um dos cinco parar
de publicar cota no período seguinte, ele fica na carteira com o último valor conhecido e sai
marcado como descontinuado. Removê-lo seria o próprio viés de sobrevivência que eu critico.

**O que este teste não prova:** que funciona em 2026. Prova que funcionou em três recortes de um
ano só, com um regime de juros só.

---

## D-018 — Automação real, aprovação por etapa, e o repositório precisa ser defensável 🎥
**Quando:** 20/08, Fase 1 · **Situação:** como conduzir o desenvolvimento nos 8 dias

**Decisão 1 — mostrar em vez de descrever.** O enunciado pede que o caminho para execução diária
sem humano no loop seja "claro e viável". Quase todo candidato vai descrever isso num parágrafo.
Vamos **rodar**: uma automação do GitHub executa o pipeline do zero semanalmente e publica o
`ranking.json`. A diferença entre "seria viável" e "está rodando, olha o histórico" é grande, e
é exatamente o critério de escalabilidade e robustez da avaliação. Custo: ~1h, e vira a CI.

**Decisão 2 — aprovação por etapa, não por fase.** Dentro de cada fase, apresento cada bloco e
espero o ok antes de seguir.

**Por quê, e essa é a razão de verdade:** o maior risco do projeto não é entregar pouco. É chegar
em 27/08 com um repositório grande que não se consegue defender no vídeo. A Decade vai
perguntar por que tal escolha foi feita; se a resposta for "o assistente sugeriu", o projeto morre
ali, independente da qualidade do código. **Regra adotada: módulo que não se consegue explicar
em duas frases é módulo para simplificar ou apagar.**

**Decisão 3 — página visual do ranking** para a apresentação, feita na Fase 6.

**Recusado:** gancho automático rodando testes a cada arquivo salvo. Era o guardrail que não
dependia da minha disciplina; sem ele, rodar a suíte volta a ser responsabilidade manual minha.
Registrado no `CLAUDE.md` para eu não esquecer que essa rede de segurança não existe.

**Verificação de controle:** *"rodou? cola o número."* O modo de falha mais
comum é descrever a saída em vez de mostrá-la.

---

## D-019 — Python 3.12 isolado pelo uv; Docker validado pela CI
**Quando:** 20/08, Fase 2 · **Situação:** a máquina de desenvolvimento tem Python 3.14 e não tem Docker

O 3.14 é recente demais: Polars e Pandera podem não ter pacote pronto, e descobrir isso na
Fase 4 custaria caro.

**Decisão:** o `uv` baixa e fixa o **3.12.14** só para este projeto, sem tocar no Python do
sistema. O `.python-version` e o `uv.lock` garantem que a CI use exatamente o mesmo.

**Obstáculo real encontrado:** o `uv` falhou ao criar um atalho de versão no Windows (exige
permissão de symlink). Contornado apontando o caminho do interpretador direto. Não acontece
no Linux da CI.

**Sobre o Docker:** em vez de pedir a instalação do Docker Desktop, o `Dockerfile` é
**construído e executado pela CI**. É evidência melhor que um teste local: prova que a imagem
funciona numa máquina que nunca viu o projeto — que é exatamente o que o enunciado pede.

---

## D-020 — Código em inglês, documentos de trabalho em português
**Quando:** 20/08, Fase 2 · **Situação:** em que idioma escrever o repositório

**Decisão:** código, comentários, `README.md` e `ranking.md` em inglês. O desenho
(`01-solution-design.md`) e este diário em português.

**Por quê:** o case veio em inglês e um dos critérios de avaliação é "outro time consegue
consumir sem você". Já o desenho e o diário são material da apresentação final, que será
defendê-los em português.

**Custo aceito:** o repositório é bilíngue, o que é levemente estranho. A alternativa —
tudo em português — tornaria o código menos consumível por quem avalia.

---

## D-021 — Os valores esperados dos testes são calculados fora do código 🎥
**Quando:** 20/08, Fase 2 · **Situação:** contra o que comparar o resultado das fórmulas

**Decisão:** os números de referência foram calculados por um script independente, direto do
CSV congelado, e escritos à mão no `conftest.py`:

```
00068305000135  -> 64 observações, retorno 0.031724441185
42592315000115  -> 64 observações, retorno 0.027386613839
CDI acumulado   -> 0.035903629100
```

**Por quê:** se eu gerasse esses números com a própria implementação, o teste provaria apenas
que o código concorda consigo mesmo. Verificação precisa de uma testemunha independente.

**Efeito colateral interessante:** os dois fundos renderam **menos que o CDI** no trimestre
(3,17% e 2,74% contra 3,59%). É exatamente o tipo de coisa que o ranking existe para capturar,
e já apareceu na fixture.

---

## D-022 — A CI fica vermelha de propósito até a Fase 5 🎥
**Quando:** 20/08, Fase 2 · **Situação:** teste antes do código significa suíte falhando

**Decisão:** a CI roda desde o primeiro push e **falha**, porque os 92 testes referenciam
módulos que ainda não existem. O `README.md` explica isso na primeira tela.

**Por quê:** a alternativa seria marcar tudo como "esperado falhar" ou não ligar a CI ainda —
as duas escondem o estado real. Uma suíte vermelha por ausência de implementação é o estado
correto de um projeto escrito com teste primeiro.

**O que aceito perder:** quem olhar o repositório antes da Fase 5 vê um X vermelho. Mitigado
por dizer, em vez de esconder.

---

## D-023 — Sem pre-commit
**Quando:** 20/08, Fase 2 · **Situação:** o checklist previa `.pre-commit-config.yaml`

**Decisão:** não criar. A CI aplica exatamente os mesmos portões — ruff, format, mypy,
pytest — a cada push.

**Por quê:** um hook local que ninguém instalou não protege nada; só parece que protege.
Duplicar a configuração em dois lugares cria a chance de eles divergirem.

**Consequência assumida:** com a recusa também do gancho automático de testes
(D-018), **rodar a suíte antes de declarar algo pronto é responsabilidade manual minha**. A
CI pega no push o que eu deixar passar, mas o ciclo de retorno fica mais lento.

---

## D-024 — O registro da CVM tem linhas repetidas, e o join inflava o universo 🎥📊
**Quando:** 20/08, Fase 3 · **Situação:** rodar os leitores contra os arquivos completos

Ao validar os leitores nos 36.598 registros reais, o funil reproduziu o baseline **com um
desvio consistente de +2% em todas as etapas**. Dois por cento não é ruído: é sinal.

Causa: `registro_fundo.csv` tem **89.749 linhas para 88.617 ids únicos** — 1.046 fundos
aparecem repetidos, com linhas idênticas. `registro_classe.csv` repete outros 4. Um `left
join` comum multiplica cada classe pertencente a um fundo duplicado.

**Decisão:** os leitores de registro colapsam chaves repetidas antes de qualquer junção
(última ocorrência vence, assumindo que correções são anexadas ao fim), e `read_registry`
**falha explicitamente** se a junção mudar a contagem de linhas.

**O que isso ensina, e é o ponto para o vídeo:** o funil de qualidade *passou*. Os 2% de
inflação couberam dentro da tolerância de 3%, então o guardrail que eu tinha criado
justamente para pegar erro de junção **não pegou este**. Um universo 2% maior sobreviveria
até a entrega sem ninguém notar.

Correção adicionada: junção que muda a contagem de linhas agora levanta erro, independente
de tolerância. Verificação de percentual não substitui invariante exata.

**Resultado depois da correção:** seis das oito etapas do funil batem exatamente (0,00%),
maior desvio 1,09%.

**Efeito colateral:** o baseline de `registered_classes` passou de 36.598 para **36.594** —
o número correto de classes distintas. Não é ajuste para fazer passar; é correção de um erro
de medição meu na Fase 1, onde contei linhas em vez de chaves.

---

## D-025 — O disjuntor conta requisições, não arquivos
**Quando:** 20/08, Fase 3 · **Situação:** um teste falhou e expôs ambiguidade no desenho

Escrevi "para depois de 5 falhas seguidas no mesmo servidor" sem definir o que é uma falha.
Um teste falhou por causa disso, e a falha estava no teste — mas revelou que a decisão nunca
tinha sido tomada de verdade.

**Decisão:** conta **requisições** falhas, não downloads falhos.

**Por quê:** o servidor experimenta requisições. Contando arquivos, uma política de 3 tentativas
dispararia 15 requisições contra um servidor morto antes do disjuntor perceber. O objetivo do
disjuntor é parar de martelar — então a unidade tem que ser aquilo que o servidor vê.

---

## D-026 — O Banco Central recusa janelas longas 📊
**Quando:** 20/08, Fase 3 · **Situação:** o primeiro download real falhou com HTTP 406

A URL do CDI na configuração pedia a série inteira, sem intervalo. O Banco Central respondeu
**406 Not Acceptable**. Medido: 11 anos é recusado, 14 meses é servido, série inteira sempre falha.

**Decisão:** a URL do CDI passa a carregar `{start}` e `{end}`, preenchidos a partir da data de
referência e da janela. As datas vão em formato dia-primeiro, que é o que o Banco Central espera —
enviá-las mês-primeiro buscaria uma janela diferente **com sucesso**, que é pior que falhar.

**Limitação registrada:** um backfill de mais de ~10 anos precisa ser fatiado em várias chamadas.

**Como apareceu:** só rodando de verdade. Nenhum teste com transporte simulado pegaria isso, e é
por isso que rodar contra os servidores reais no fim de cada bloco não é opcional.

**Segundo defeito na mesma rodada:** o CDI foi salvo em disco com o nome `2025`, porque eu derivava
o nome do arquivo da URL e essa é uma API com query string. Cada fonte agora **declara** seu nome
de arquivo na configuração.

---

# Material para a apresentação

*Seção viva — vou alimentando conforme o projeto anda.*

## Surpresas (o que eu não esperava encontrar)

1. O arquivo de cadastro que todo tutorial usa está obsoleto: 10% de cobertura, zero taxas.
2. A data de início do fundo no registro é mentira — diz 2025 para fundos de 1994.
3. A quebra de layout do informe diário é em jan/2024, não em nov/2024 como eu supunha.
4. A ANBIMA não é fechada: os índices baixam sem credencial. Eu tinha desistido cedo demais.
6. Escrever o teste primeiro pegou um erro de desenho antes de virar código: dois testes
   especificavam leitura de arquivo dentro do módulo de cálculo. Corrigido de graça.
5. A falta de dado de taxa não é aleatória — segue a regulação. Varejo é obrigado a divulgar
   lâmina; qualificado não. Por isso a cobertura cai de 64% para 28%.

## Números que valem citar

| Número | |
|---|---|
| 36.598 → 1.003 | o funil inteiro, de todas as classes registradas ao universo investável |
| R$ 4,4 trilhões | patrimônio do universo antes do corte de divulgação |
| 10,3% e 0% | cobertura e preenchimento de taxa do `cad_fi.csv` |
| 66% vs 5,3% | fundos "com menos de 1 ano" pelo campo errado vs pelo certo |
| 7,4 anos | idade real mediana dos fundos |
| 89.749 linhas / 88.617 ids | o registro de fundos da CVM repete 1.046 fundos — o join inflava o universo em 2% |
| 31 MB em 2,7 s | as cinco fontes baixadas do zero, com repetição, disjuntor e verificação de conteúdo |
| 92 testes vermelhos | escritos antes de existir uma linha de implementação |
| 3,17% e 2,74% vs 3,59% | dois fundos da amostra renderam **menos que o CDI** no 4º tri de 2025 |
| ±1,5 | incerteza sobre a medida de retorno ajustado ao risco com 12 meses |
| 93% → 61% | cobertura do universo conforme a janela vai de 12 para 60 meses |

## Esqueleto do vídeo (5 min)

| Tempo | Assunto | Apoio |
|---|---|---|
| 0:00–0:40 | O problema e o que entreguei | funil 36.598 → 1.003 |
| 0:40–1:40 | Fui olhar o dado antes de codar — as três armadilhas | D-001, D-002, D-003 |
| 1:40–2:40 | Como decido o que é "melhor" — grupo, perfil, e por que a taxa pesa mais | D-008, D-012 |
| 2:40–3:20 | **Funciona?** O teste no passado e o percentil contra carteiras aleatórias | D-017, `saida/validacao.md` |
| 3:20–4:00 | **A decisão que menos me convence** | D-011 e a seção "o que fica em aberto" |
| 4:00–4:30 | O que o projeto não vê: a carteira | CDA como próximo passo |
| 4:30–5:00 | Caminho para produção | um comando, uma função, um agendador |
