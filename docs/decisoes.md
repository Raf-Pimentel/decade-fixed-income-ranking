# Diário de decisões

Registro corrido de cada decisão do projeto, escrita **no momento em que foi tomada**.
Serve para dois fins: me impedir de refazer discussão já encerrada, e dar ao Rafael o
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

O Rafael apontou overengineering. Reavaliei e concordei.

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

O Rafael perguntou por que eu não tinha considerado simulação. Foi ponto cego real: eu havia
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

Ao revisar o pedido original do Rafael, encontrei "tolerância a falhas (circuit breakers/retries)"
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
em 27/08 com um repositório grande que o Rafael não consegue defender no vídeo. A Decade vai
perguntar por que tal escolha foi feita; se a resposta for "o assistente sugeriu", o projeto morre
ali, independente da qualidade do código. **Regra adotada: módulo que ele não consegue explicar
em duas frases é módulo para simplificar ou apagar.**

**Decisão 3 — página visual do ranking** para a apresentação, feita na Fase 6.

**Recusado:** gancho automático rodando testes a cada arquivo salvo. Era o guardrail que não
dependia da minha disciplina; sem ele, rodar a suíte volta a ser responsabilidade manual minha.
Registrado no `CLAUDE.md` para eu não esquecer que essa rede de segurança não existe.

**Verificação que o Rafael vai usar contra mim:** *"rodou? cola o número."* Meu modo de falha mais
comum é descrever a saída em vez de mostrá-la.

---

# Material para a apresentação

*Seção viva — vou alimentando conforme o projeto anda.*

## Surpresas (o que eu não esperava encontrar)

1. O arquivo de cadastro que todo tutorial usa está obsoleto: 10% de cobertura, zero taxas.
2. A data de início do fundo no registro é mentira — diz 2025 para fundos de 1994.
3. A quebra de layout do informe diário é em jan/2024, não em nov/2024 como eu supunha.
4. A ANBIMA não é fechada: os índices baixam sem credencial. Eu tinha desistido cedo demais.
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
