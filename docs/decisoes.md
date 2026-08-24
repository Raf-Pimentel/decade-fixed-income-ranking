# Diário de decisões

Registro corrido de cada decisão do projeto, escrita **no momento em que foi tomada**.
Serve para dois fins: impedir que se refaça discussão já encerrada, e deixar pronto o
material pronto para a apresentação final sem precisar reconstruir a trajetória de memória.

**Como uso:** toda decisão não óbvia vira uma entrada, na hora. Se eu reverter uma decisão,
**não apago a original**. Abro uma nova entrada marcada como reversão e explico o que mudou.
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
| [D-027](#d-027) | 20/08 | 3 | Aspas soltas quebravam a leitura do extrato | 📊 |
| [D-028](#d-028) | 20/08 | 3 | Prazo de resgate em dias úteis vira dias corridos | 🎥 |
| [D-029](#d-029) | 20/08 | 3 | Baseline restabelecido: definição diferente, não dado diferente | 🎥📊 |
| [D-030](#d-030) | 20/08 | 4 | **IMA-B não entra: CDI para todos, com a limitação declarada** | 🔄📊 |
| [D-031](#d-031) | 20/08 | 4 | A Decade delegou universo e janela: foco em varejo acionável | 🎥 |
| [D-032](#d-032) | 20/08 | 5 | **Dois perfis de varejo por horizonte; o qualificado sai** | 🔄🎥📊 |
| [D-033](#d-033) | 20/08 | 5 | Só ligar a simulação de verdade mostrou que ela não estava ligada | 🎥 |
| [D-034](#d-034) | 20/08 | 5 | **O primeiro Top 5 continha fundos institucionais. Dois defeitos meus** | 🎥📊 |
| [D-035](#d-035) | 20/08 | 5 | **Revisão do primeiro resultado: seis conclusões, nenhuma implementada agora** | 🎥 |
| [D-036](#d-036) | 20/08 | 5.5 | **O teste no passado validou o método, e corrigi dois erros contra mim** | 🎥📊 |
| [D-037](#d-037) | 20/08 | 6 | Extrato multi-ano ampliou o universo; o guardrail pegou e o resultado não mudou | 📊 |
| [D-038](#d-038) | 21/08 | 6 | **Publicar a taxa só-desempenho revelou que a lista é, sobretudo, de custo** | 🎥📊 |
| [D-039](#d-039) | 21/08 | 6 | A janela mede exatamente os meses que declara | 🎥📊 |
| [D-040](#d-040) | 21/08 | 6 | **Cinco fundos, não cinco notas: uma carteira ocupa uma vaga** | 🎥📊 |
| [D-041](#d-041) | 21/08 | 6 | Peso só vale para critério que separa | 📊 |
| [D-042](#d-042) | 21/08 | 6 | Duas notas por fundo: dentro do grupo e contra o universo | 🎥 |
| [D-043](#d-043) | 21/08 | 6 | A reamostragem sorteia por fundo, e o benchmark vai junto | 🎥📊 |
| [D-044](#d-044) | 21/08 | 6 | **O teste no passado mede o universo inteiro, e diz contra o que** | 🎥📊 |
| [D-045](#d-045) | 21/08 | 6 | Os entregáveis moram no repositório | 📊 |
| [D-046](#d-046) | 21/08 | 6 | Testes que leem o arquivo entregue | 🎥 |
| [D-047](#d-047) | 24/08 | 6 | **A taxa declarada não é o preço do cliente. Passa a ser medida** | 🔄🎥📊 |

---

## D-001: A unidade de análise é a classe, não o fundo 🎥📊
**Quando:** 19/08, Fase 1 · **Situação:** definir o grão do pipeline

Abri o arquivo real antes de escrever qualquer código. O informe diário de dez/2025 tem as
colunas `TP_FUNDO_CLASSE`, `CNPJ_FUNDO_CLASSE` e `ID_SUBCLASSE`. A Resolução CVM 175
reorganizou os fundos em classes, e desde **janeiro de 2024** o dado é publicado por classe.

**Decisão:** todo o pipeline trabalha no grão de classe, com `cnpj_classe` como chave.

**Por quê:** é o que a fonte publica hoje. Qualquer reconciliação para o grão antigo seria
invenção minha.

**O que aceito perder:** séries anteriores a 2021 ficam menos acessíveis.

**Por que importa para a apresentação:** quem escreve o código assumindo o formato antigo
faz o cruzamento errado **e não recebe erro nenhum**. O programa roda e entrega números
errados em silêncio. É o tipo de erro que só se evita indo olhar o arquivo.

---

## D-002: Taxas vêm do Extrato e da Lâmina 🎥📊
**Quando:** 19/08, Fase 1 · **Situação:** de onde tirar taxa de administração

Testei o `cad_fi.csv`, que é o arquivo que aparece em qualquer tutorial de dados da CVM.
Medi: cobre **10,3%** das classes de renda fixa de hoje e tem **0%** de `TAXA_ADM` preenchida.
Está obsoleto desde a RCVM 175.

**Decisão:** taxa e prazo de resgate vêm de `extrato_fi_YYYY.csv` (117 colunas) e da lâmina.

**Alternativa descartada:** insistir no `cad_fi.csv` com imputação, o que seria imputar 100% do dado.

---

## D-003: A idade do fundo não sai do `Data_Inicio` 🎥📊
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

## D-004: Janela de 12 meses 📊
**Quando:** 19/08, Fase 1 · **Situação:** quanto histórico usar

Medi a cobertura real das 1.801 classes conforme estico a janela: 6m = 97% · **12m = 93%** ·
24m = 82% · 36m = 74% · 60m = 61%. Cada ano a mais custa cerca de 10% do universo.

**Decisão:** 12 meses para pontuar; 3, 6 e 24 meses reportados junto. Parâmetro em YAML.

**Por quê:** além da cobertura, 2021–2023 teve a Selic indo de 2% a 13,75%, um regime diferente
do de 2025. Janela longa também enche a amostra de fundos velhos e grandes que sobreviveram.

**Correção factual no meio do caminho:** eu havia afirmado que a quebra de layout era em
nov/2024. Fui verificar mês a mês: é **jan/2024**. Existem três layouts (2000–2020, 2021–2023,
2024 em diante), e converter o do meio para o atual é só renomear coluna, bem mais barato do
que eu tinha dito. O limite da janela é estatístico, não técnico.

---

## D-005: Arquitetura elaborada *(revertida em D-009)*
**Quando:** 19/08, Fase 1

Propus camadas bronze/silver/gold, DuckDB junto com Polars, disjuntor, logging estruturado,
e um caminho de produção com orquestrador.

**Raciocínio na época:** demonstrar domínio de arquitetura de dados e um caminho de escala crível.

---

## D-006: Três perfis de cliente *(revertida em D-010)*
**Quando:** 19/08, Fase 1

Varejo Liquidez, Varejo Rendimento e Qualificado.

---

## D-007: ANBIMA descartada *(revertida em D-014)*
**Quando:** 19/08, Fase 1

Constatei que `data.anbima.com.br` exige credencial. Como a `Classificacao_Anbima` já vem
dentro do registro da CVM, concluí que dava para entregar sem a ANBIMA.

---

## D-008: Comparar cada fundo só dentro do seu grupo 🎥
**Quando:** 20/08, Fase 1 · **Situação:** como normalizar métricas entre fundos diferentes

**Decisão:** cada métrica vira a posição relativa do fundo **dentro do seu grupo ANBIMA**, não
uma nota absoluta comparada com todo mundo.

**Por quê:** em 2025 os fundos que mais renderam foram os que tomaram mais risco de crédito.
Um ranking por rentabilidade, ou até por Sharpe global, entregaria automaticamente os cinco
fundos mais arriscados, e o problema deles simplesmente ainda não tinha aparecido. Comparar
um fundo de título público com um de dívida privada pela rentabilidade nominal não é comparar,
é premiar risco.

**O que aceito perder:** grupos pequenos dão percentil ruidoso. Mitigo fundindo grupos com
menos de 20 fundos ao grupo pai.

---

## D-009: Cortar a infraestrutura 🔄
**Quando:** 20/08, Fase 1 · **Reverte:** D-005

A revisão apontou overengineering. Reavaliei e concordei.

**Decisão:** fora DuckDB, camadas de data lake, orquestrador, logging estruturado. Ficam
Polars, Parquet e uma pasta de saída.

**Por quê:** são ~1.000 fundos e ~200 MB. O projeto roda em minutos num notebook. Eu tinha
investido em infraestrutura de escala num problema que não tem problema de escala, e
economizado em estatística num problema que é inteiramente estatístico. Construí o encanamento
e não testei a água.

**O que fica:** validação de dados, point-in-time, manifesto com hash e testes. Esses carregam
peso de verdade, porque o dado da CVM é sujo e a CVM sobrescreve arquivo sem versionar.

---

## D-010: Dois perfis, não três 🔄
**Quando:** 20/08, Fase 1 · **Reverte:** D-006

**Decisão:** Varejo e Qualificado.

**Por quê:** é a divisão que a própria CVM faz no campo `Publico_Alvo`, e é ela que determina
o que o cliente pode legalmente comprar. O terceiro perfil era invenção minha e triplicava o
trabalho de redação por ganho marginal.

---

## D-011: Simulação de robustez no ranking 🎥
**Quando:** 20/08, Fase 1 · **Situação:** o ranking é confiável o suficiente para ser publicado como lista ordenada?

A revisão perguntou por que a simulação não tinha sido considerada. Foi ponto cego real: eu havia
escrito que a maior fraqueza do método era estimar qualidade com 12 meses de dados, e não
propus nenhuma ferramenta para **medir** essa incerteza.

Com 12 meses de dados diários, o erro sobre a medida de "retorno por unidade de risco" é da
ordem de **±1,5**, maior que as diferenças que eu ia ranquear. A diferença entre o 1º e o
15º colocado, muitas vezes, não existe.

**Decisão:** antes de publicar, mil simulações reembaralhando os retornos em blocos e sorteando
variações nos pesos. O Top 5 final são os cinco que mais aparecem no topo, e cada um sai com
o número: *"apareceu no Top 5 em 91% das simulações"*.

**Alternativa descartada:** simular trajetórias futuras a partir dos parâmetros estimados nos
mesmos 12 meses. Isso não adiciona informação, só reveste o número de falsa precisão.

**Limitação que declaro junto:** reembaralhar o que aconteceu nunca cria um evento que não
aconteceu. Se nenhum fundo teve problema de crédito em 2025, nenhuma simulação vai produzir um.
A simulação mede azar de amostra, não risco de cauda.

---

## D-012: Taxa pesa mais que rentabilidade no varejo 🎥
**Quando:** 20/08, Fase 1 · **Situação:** definir os pesos

**Decisão:** no perfil varejo, taxa de administração pesa 25 e prazo de resgate 20, contra 15
de ganho sobre o benchmark.

**Por quê:** a taxa é o único número que se sabe com certeza sobre **2026**. A rentabilidade de
2025 é, em boa parte, benchmark que todo fundo pegou igual, mais um prêmio de crédito que ainda
não deu problema. A taxa vai ser cobrada no ano que vem exatamente como foi neste. Dar peso
maior ao que persiste é mais defensável do que dar peso maior ao que não persiste.

**Contraintuitivo?** Sim, e é justamente por isso que está documentado.

---

## D-013: Só entra fundo com taxa e prazo publicados 📊
**Quando:** 20/08, Fase 1 · **Situação:** o que fazer com 44% do universo sem dado de taxa

**Decisão:** fundo sem taxa e prazo de resgate conhecidos não entra no ranking. Universo cai
de 1.801 para **1.003**.

**Por quê:** não é conveniência de dados. É o mínimo de uma recomendação responsável. Não dá
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

## D-014: ANBIMA volta, pelos índices públicos 🔄🎥
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

## D-015: O funil medido vira teste de regressão 🎥
**Quando:** 20/08, Fase 1 · **Situação:** como garantir qualidade sem ferramenta pesada

Na Fase 1 medi o funil de elegibilidade nos arquivos reais: 36.598 classes → 7.759 renda fixa
→ … → 1.801 → 1.003.

**Decisão:** esses números viram o **baseline esperado**. Toda execução imprime o funil e compara.
Desvio acima da tolerância para o pipeline.

**Por quê:** é o teste de fumaça mais barato que existe aqui, e pega o erro mais perigoso. Um
cruzamento quebrado que corta metade do universo é praticamente invisível numa revisão de
código, mas grita num relatório que diz "esperado 1.003, obtido 412".

---

## D-016: Disjuntor restaurado na extração 🔄
**Quando:** 20/08, Fase 1 · **Reverte:** parte de D-009

Ao revisar o pedido original, encontrei "tolerância a falhas (circuit breakers/retries)"
como requisito explícito. Eu tinha cortado o disjuntor junto com a infraestrutura.

**Decisão:** volta, na versão mínima. Após 5 falhas seguidas no mesmo servidor, para de insistir
e falha com mensagem clara. São ~15 linhas.

**Lição registrada:** "sem overengineering" não autoriza remover requisito do cliente. Autoriza
implementá-lo da forma mais simples que funcione.

---

## D-017: Testar o método no passado, com o critério declarado antes 🎥
**Quando:** 20/08, Fase 1 · **Situação:** o plano diz que o método é razoável, mas não mostra que funciona

Tudo o que eu tinha até aqui era argumento. Nada era evidência. É a primeira pergunta que
alguém experiente faz: *"tá, mas funciona?"*

**Decisão:** entra uma **Fase 5.5** entre o ranking e a documentação. Monto o ranking com dados
até três datas de corte de 2025, que são 31/03, 30/06 e 30/09, e meço como cada Top 5 se comportou
no período seguinte, que o ranking não viu.

**Contra o que comparo:** a mediana do grupo, o benchmark do grupo, e **1.000 carteiras de cinco
fundos sorteados ao acaso**. A terceira é a que importa: responde se meu método bate o acaso.
É o controle que quase ninguém faz.

**Por que cabe no prazo:** se o point-in-time estiver correto, cada rodada é um comando,
`uv run ranking --reference-date 2025-06-30`. Nenhum código novo. O custo está em medir e escrever,
não em programar. Isso é o retorno concreto da disciplina de point-in-time, que até agora era
só uma boa prática no papel. **E o teste audita a si mesmo:** se for difícil de rodar, é porque
o point-in-time está furado.

**Critério de sucesso, congelado antes de rodar:**
> acima do percentil 60 da distribuição de carteiras aleatórias em pelo menos 2 das 3 datas.

**Regra dura que vale mais que o resultado:** proibido mexer em pesos, cortes ou métricas depois
de ver o teste. Ajustar até passar não valida nada. Decora o segundo semestre de 2025. É a
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

## D-018: Automação real, aprovação por etapa, e o repositório precisa ser defensável 🎥
**Quando:** 20/08, Fase 1 · **Situação:** como conduzir o desenvolvimento nos 8 dias

**Decisão 1: mostrar em vez de descrever.** O enunciado pede que o caminho para execução diária
sem humano no loop seja "claro e viável". Quase todo candidato vai descrever isso num parágrafo.
Vamos **rodar**: uma automação do GitHub executa o pipeline do zero semanalmente e publica o
`ranking.json`. A diferença entre "seria viável" e "está rodando, olha o histórico" é grande, e
é exatamente o critério de escalabilidade e robustez da avaliação. Custo: ~1h, e vira a CI.

**Decisão 2: aprovação por etapa, não por fase.** Dentro de cada fase, apresento cada bloco e
espero o ok antes de seguir.

**Por quê, e essa é a razão de verdade:** o maior risco do projeto não é entregar pouco. É chegar
em 27/08 com um repositório grande que não se consegue defender no vídeo. A Decade vai
perguntar por que tal escolha foi feita; se a resposta for "o assistente sugeriu", o projeto morre
ali, independente da qualidade do código. **Regra adotada: módulo que não se consegue explicar
em duas frases é módulo para simplificar ou apagar.**

**Decisão 3: página visual do ranking** para a apresentação, feita na Fase 6.

**Recusado:** gancho automático rodando testes a cada arquivo salvo. Era o guardrail que não
dependia da minha disciplina; sem ele, rodar a suíte volta a ser responsabilidade manual minha.
Registrado no `CLAUDE.md` para eu não esquecer que essa rede de segurança não existe.

**Verificação de controle:** *"rodou? cola o número."* O modo de falha mais
comum é descrever a saída em vez de mostrá-la.

---

## D-019: Python 3.12 isolado pelo uv; Docker validado pela CI
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
funciona numa máquina que nunca viu o projeto, que é exatamente o que o enunciado pede.

---

## D-020: Código em inglês, documentos de trabalho em português
**Quando:** 20/08, Fase 2 · **Situação:** em que idioma escrever o repositório

**Decisão:** código, comentários, `README.md` e `ranking.md` em inglês. O desenho
(`01-solution-design.md`) e este diário em português.

**Por quê:** o case veio em inglês e um dos critérios de avaliação é "outro time consegue
consumir sem você". Já o desenho e o diário são material da apresentação final, que será
defendê-los em português.

**Custo aceito:** o repositório é bilíngue, o que é levemente estranho. A alternativa,
tudo em português, tornaria o código menos consumível por quem avalia.

---

## D-021: Os valores esperados dos testes são calculados fora do código 🎥
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

## D-022: A CI fica vermelha de propósito até a Fase 5 🎥
**Quando:** 20/08, Fase 2 · **Situação:** teste antes do código significa suíte falhando

**Decisão:** a CI roda desde o primeiro push e **falha**, porque os 92 testes referenciam
módulos que ainda não existem. O `README.md` explica isso na primeira tela.

**Por quê:** a alternativa seria marcar tudo como "esperado falhar" ou não ligar a CI ainda,
as duas escondem o estado real. Uma suíte vermelha por ausência de implementação é o estado
correto de um projeto escrito com teste primeiro.

**O que aceito perder:** quem olhar o repositório antes da Fase 5 vê um X vermelho. Mitigado
por dizer, em vez de esconder.

---

## D-023: Sem pre-commit
**Quando:** 20/08, Fase 2 · **Situação:** o checklist previa `.pre-commit-config.yaml`

**Decisão:** não criar. A CI aplica exatamente os mesmos portões, ruff, format, mypy e
pytest, a cada push.

**Por quê:** um hook local que ninguém instalou não protege nada; só parece que protege.
Duplicar a configuração em dois lugares cria a chance de eles divergirem.

**Consequência assumida:** com a recusa também do gancho automático de testes
(D-018), **rodar a suíte antes de declarar algo pronto é responsabilidade manual minha**. A
CI pega no push o que eu deixar passar, mas o ciclo de retorno fica mais lento.

---

## D-024: O registro da CVM tem linhas repetidas, e o join inflava o universo 🎥📊
**Quando:** 20/08, Fase 3 · **Situação:** rodar os leitores contra os arquivos completos

Ao validar os leitores nos 36.598 registros reais, o funil reproduziu o baseline **com um
desvio consistente de +2% em todas as etapas**. Dois por cento não é ruído: é sinal.

Causa: `registro_fundo.csv` tem **89.749 linhas para 88.617 ids únicos**, ou seja, 1.046 fundos
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

**Efeito colateral:** o baseline de `registered_classes` passou de 36.598 para **36.594**,
o número correto de classes distintas. Não é ajuste para fazer passar; é correção de um erro
de medição meu na Fase 1, onde contei linhas em vez de chaves.

---

## D-025: O disjuntor conta requisições, não arquivos
**Quando:** 20/08, Fase 3 · **Situação:** um teste falhou e expôs ambiguidade no desenho

Escrevi "para depois de 5 falhas seguidas no mesmo servidor" sem definir o que é uma falha.
Um teste falhou por causa disso, e a falha estava no teste, mas ela revelou que a decisão nunca
tinha sido tomada de verdade.

**Decisão:** conta **requisições** falhas, não downloads falhos.

**Por quê:** o servidor experimenta requisições. Contando arquivos, uma política de 3 tentativas
dispararia 15 requisições contra um servidor morto antes do disjuntor perceber. O objetivo do
disjuntor é parar de martelar, então a unidade tem que ser aquilo que o servidor vê.

---

## D-026: O Banco Central recusa janelas longas 📊
**Quando:** 20/08, Fase 3 · **Situação:** o primeiro download real falhou com HTTP 406

A URL do CDI na configuração pedia a série inteira, sem intervalo. O Banco Central respondeu
**406 Not Acceptable**. Medido: 11 anos é recusado, 14 meses é servido, série inteira sempre falha.

**Decisão:** a URL do CDI passa a carregar `{start}` e `{end}`, preenchidos a partir da data de
referência e da janela. As datas vão em formato dia-primeiro, que é o que o Banco Central espera.
enviá-las mês-primeiro buscaria uma janela diferente **com sucesso**, que é pior que falhar.

**Limitação registrada:** um backfill de mais de ~10 anos precisa ser fatiado em várias chamadas.

**Como apareceu:** só rodando de verdade. Nenhum teste com transporte simulado pegaria isso, e é
por isso que rodar contra os servidores reais no fim de cada bloco não é opcional.

**Segundo defeito na mesma rodada:** o CDI foi salvo em disco com o nome `2025`, porque eu derivava
o nome do arquivo da URL e essa é uma API com query string. Cada fonte agora **declara** seu nome
de arquivo na configuração.

---

## D-027: Aspas soltas quebravam a leitura do extrato 📊
**Quando:** 20/08, Fase 3 · **Situação:** `extrato_fi_2025.csv` falhava com "CSV malformed"

Medido: o arquivo tem **194 aspas duplas soltas** em campos de texto livre, em descrições de
política de investimento, principalmente. Um leitor que trate aspas como delimitador abre uma
região citada, engole todas as quebras de linha até a próxima aspa e morre no meio de um
arquivo de 12 MB.

**Decisão:** desligar o tratamento de aspas na leitura de arquivos da CVM.

**Por que é seguro:** verifiquei antes de decidir, e todas as 13.590 linhas têm exatamente 117
campos separando por `;`, com ou sem aspas presentes. A CVM não usa aspas como delimitador,
usa como caractere comum.

---

## D-028: Prazo de resgate em dias úteis vira dias corridos 🎥
**Quando:** 20/08, Fase 3 · **Situação:** o extrato tem `TP_DIA_PAGTO_RESGATE`

O campo diz se o prazo está em **dias úteis ou corridos**, e a base mistura os dois. Um fundo
que anuncia "D+5 dias úteis" faz o cliente esperar uma semana.

**Decisão:** tudo é convertido para dias corridos na leitura. Se a fonte parar de publicar a
unidade, assume-se dias corridos. Isso não penaliza ninguém por uma coluna que simplesmente
não veio.

**Por que importa:** prazo de resgate é o **segundo maior peso** do perfil varejo (20 de 100).
Tratar as duas unidades como iguais favoreceria sistematicamente todo fundo que cota em dias
úteis. É um viés silencioso e direcional, o pior tipo.

---

## D-029: Baseline restabelecido: definição diferente, não dado diferente 🎥📊
**Quando:** 20/08, Fase 3 · **Situação:** o funil do pipeline divergiu do baseline em 3 etapas

Rodando o pipeline completo contra os arquivos reais, seis das nove etapas bateram
**exatamente**. Três não bateram, e o guardrail parou a execução, que é exatamente o que ele
existe para fazer.

Investiguei antes de mexer em qualquer número. As causas:

| Etapa | Causa |
|---|---|
| `above_min_assets`, `above_min_shareholders` | O script exploratório da Fase 1 usava **20 observações de um mês**; o pipeline aplica a regra de **200 observações em doze meses** que este projeto sempre declarou. Não são a mesma grandeza |
| `with_fee_and_redemption` | Faltava implementar a **lâmina**, obrigatória justamente para fundos de varejo |

**Decisão:** implementar a lâmina (fechou o desvio: 703 → 975, e varejo 588 → 854) e
**restabelecer** as duas etapas restantes com a definição correta, documentando linha a linha
no `universe.yaml` o valor antigo, o novo e o motivo.

**A distinção que me autoriza a mexer no alvo:** a definição nova é melhor pelos próprios
méritos, decidida independentemente do número que produz. Um fundo com 44 dias de série no ano
não deveria ser ranqueado, e a regra de 200 dias está no desenho desde a Fase 1. O que estava
errado era a medição exploratória, não o pipeline. Isso é diferente de afrouxar um critério
até o resultado passar, que é o que a regra 11 proíbe.

**Resultado:** funil reproduz com **0,00% de desvio em todas as dez etapas**.

---

## D-030: IMA-B não entra: CDI para todos, com a limitação declarada 🔄📊
**Quando:** 20/08, Fase 4 · **Reverte parcialmente:** D-014

Na Fase 1 eu descobri que os índices IMA da ANBIMA baixam sem credencial e usei isso para
reincorporar a ANBIMA (D-014), prometendo benchmark por grupo: CDI para pós-fixado, IMA-B para
indexado à inflação, IRF-M para prefixado. Fui implementar e medi duas coisas:

**Primeira: quantos fundos isso afeta.** No universo de varejo (854 fundos):

| Grupo | Fundos | Benchmark correto |
|---|---:|---|
| Pós-fixado, soberano, crédito | 784 (91,8%) | CDI |
| Renda Fixa Indexados | 70 (8,2%) | IMA-B |
| Prefixado puro | **0** | IRF-M |

**Segunda: o arquivo não serve.** O `ima_completo.xls` é Excel binário de verdade (assinatura
OLE `D0 CF 11 E0`), e lê-lo exigiria uma dependência nova. Achei um `ima_completo.txt`, delimitado
por `@`, que responde 200, mas é a **foto do dia de hoje** e não a série histórica. Para um
ranking datado de 31/12/2025 ele não serve: não dá para reconstruir a variação de 12 meses
terminando naquela data.

**Decisão:** CDI como benchmark de todos os fundos, com a limitação escrita na entrega. IMA-B
volta para o backlog.

**O que isso custa, com precisão, e a parte que eu quase deixei passar:** como a comparação é
feita **dentro do grupo de pares**, um deslocamento constante no benchmark não muda a ordem por
`excesso`, porque todos os 70 fundos indexados se deslocam igual. Cheguei a concluir que era inócuo.
**Está errado:** `retorno_por_risco` é `(retorno − benchmark) / volatilidade`, e dividir um
numerador deslocado por volatilidades diferentes **muda a ordem**. Então o efeito não é nulo,
é limitado a 8,2% do universo e a uma das duas métricas de desempenho.

**Por que aceito:** 8,2% do universo, uma métrica de duas, contra uma dependência nova e um
parser de Excel binário a quatro dias da entrega. E o número reportado para esses 70 fundos sai
etiquetado com o benchmark usado, para ninguém ler "-8% contra o benchmark" achando que é IMA-B.

---

## D-031: A Decade delegou universo e janela: o critério é varejo acionável 🎥
**Quando:** 20/08, Fase 4 · **Situação:** chegou a resposta às perguntas enviadas

A resposta foi: *"ambos os pontos ficam a seu critério. Provavelmente faz sentido focar no que
for mais relevante para produzir recomendações acionáveis para investidores de varejo
brasileiros."*

Isso não é uma resposta vaga. É um critério, e ele confirma as escolhas de universo já feitas
(fora multimercado, FIDC, exclusivos e fechados; dentro só quem publica taxa e prazo) porque
todas seguem do mesmo princípio: não se recomenda a um investidor de varejo o que ele não pode
comprar ou o que não se consegue precificar.

Onde ele **muda** alguma coisa é na segmentação. Medi o universo de varejo:

| Corte de liquidez | Fundos |
|---|---:|
| D+0 ou D+1, reserva de emergência | **492 (58%)** |
| D+2 a D+30 | 232 |
| acima de D+30 | 130 |

Um ranking único de varejo entregaria os mesmos cinco fundos para quem precisa do dinheiro
amanhã e para quem investe por três anos. Com 58% do universo em D+0, o corte por horizonte
é a divisão que o investidor de varejo de fato faz.

**Janela:** mantida em 12 meses, agora por escolha registrada e não por falta de resposta.

---

## D-032: Dois perfis de varejo por horizonte; o qualificado sai 🔄🎥📊
**Quando:** 20/08, Fase 5 · **Reverte:** D-010 · **Segue de:** D-031

Esta é a segunda vez que a segmentação muda. Vale seguir a trajetória inteira, porque ela é o
argumento, e não o resultado.

| Momento | Perfis | Por quê |
|---|---|---|
| D-006 (Fase 1) | Varejo Liquidez · Varejo Rendimento · Qualificado | Intuição minha, sem dado |
| D-010 (Fase 1) | Varejo · Qualificado | Corte por overengineering: o terceiro perfil era invenção, e a linha varejo/qualificado ao menos é regulatória |
| **D-032 (Fase 5)** | **Varejo Liquidez · Varejo Prazo** | Resposta do cliente + medição |

**Decisão:** dois perfis, ambos de varejo, separados por **quando o cliente precisa do dinheiro**.
O perfil qualificado não é entregue.

### Os quatro argumentos, em ordem de força

**1. A medição.** No universo de varejo de 854 fundos, o prazo de resgate se distribui assim:

| Prazo | Fundos |
|---|---:|
| D+0 ou D+1 | **492 (58%)** |
| D+2 a D+30 | 232 |
| acima de D+30 | 130 |

Com 58% concentrado em D+0, um ranking único de varejo entregaria **os mesmos cinco fundos**
para quem precisa do dinheiro amanhã e para quem investe por três anos. Isso é o oposto de
acionável. O corte por horizonte não é uma persona inventada. É a única divisão que o dado
sustenta, e é a pergunta que o investidor de varejo de fato se faz.

**2. O cliente pediu.** A Decade respondeu que universo e janela ficam a critério, sugerindo
focar no que for *"mais relevante para produzir recomendações acionáveis para investidores de
varejo brasileiros"*. Um perfil dedicado ao investidor qualificado serve aproximadamente
ninguém na base deles.

**3. A amostra do qualificado não sustenta uma recomendação.** Dos 278 fundos restritos a
qualificado, apenas **79 publicam taxa e prazo, ou 28%**, contra 64% no varejo. E a lacuna não é
aleatória: a obrigação de publicar lâmina alcança fundos de varejo, não os restritos. Ranquear
sobre essa amostra produziria uma lista **enviesada pela regulação, e não pela qualidade**, e eu
teria que desqualificá-la em três parágrafos logo abaixo do título.

> Uma exclusão explicada com número é mais defensável que uma lista fraca publicada com
> ressalvas.

**4. O orçamento vai para onde muda a nota.** O custo de um terceiro perfil não é escrever mais
uma lista: é a Fase 5.5. Três perfis × três datas de corte = **nove backtests** em vez de seis,
com quatro dias restantes. E o backtest é a única coisa no projeto que transforma *"meu método é
defensável"* em *"meu método funcionou"*. Entre uma terceira lista e uma validação mais sólida,
a validação vale mais.

### Um detalhe de desenho que parece erro e não é

Os dois universos **se sobrepõem de propósito**:

| Perfil | Elegibilidade | Fundos |
|---|---|---:|
| Varejo Liquidez | resgate ≤ D+1 | 492 |
| Varejo Prazo | resgate ≤ D+30 | **724** |

Um investidor com horizonte de três anos pode perfeitamente comprar um fundo D+0, porque liquidez
sobrando não é defeito. Quem é restrito é o perfil de liquidez, não o de prazo. Então o mesmo
fundo pode aparecer nas duas listas, e isso é a resposta certa, não uma duplicação.

### O que muda entre os perfis não é só o peso

| Métrica | Liquidez | Prazo |
|---|---:|---:|
| Taxa de administração | **30** | **25** |
| Oscilação | 20 | |
| Pior queda | 15 | 15 |
| Tamanho e estabilidade | 15 | 15 |
| Ganho sobre o CDI | 10 | 20 |
| Retorno por unidade de risco | | 20 |
| Prazo de resgate | 10 | 5 |

Para a reserva de emergência, **preservar o capital e não pagar caro** dominam; retorno é
critério secundário. Para o horizonte longo, retorno ajustado ao risco entra de verdade. A taxa
segue como o **maior peso individual nos dois**, coerente com D-012 e agora sustentada pelo
dado de que só 37% dos fundos bateram o CDI em 2025.

### O que aceito perder

O ranking do investidor qualificado não é entregue. Se a Decade quiser depois, é uma linha de
configuração, porque a elegibilidade já é parametrizada e o universo de 69 fundos existe no pipeline.

---

## D-033: Só ligar a simulação de verdade mostrou que ela não estava ligada 🎥
**Quando:** 20/08, Fase 5

O primeiro ranking real saiu com **taxa de aparição de 100% em quase todos os fundos**. Um
número desses não é um resultado forte, é um sintoma: significa que nada estava variando.

E não estava. A reamostragem em blocos existia no código, com teste, e **nunca era chamada**.
o `metric_draws` não era passado pelo pipeline. A simulação estava variando apenas os pesos,
que é metade do que a D-011 promete.

Publicar 100% teria sido exatamente a falsa precisão que este projeto existe para evitar,
com o agravante de vir do módulo criado para combatê-la.

**Decisão:** ligar a reamostragem sobre as séries diárias reais, com uma escolha de desenho
que aproveitei para corrigir uma limitação já declarada: **todos os fundos são reamostrados
com os mesmos índices de bloco dentro de cada simulação**. Fundos não vivem histórias
independentes, porque vivem as mesmas semanas. Reamostrá-los separadamente assumiria que eles caem
em momentos diferentes, que é justamente o contrário do que acontece numa crise.

**Resultado:** as taxas de aparição passaram de "100% para todos" para **100%, 97%, 93%, 45%,
42%**, números que finalmente informam alguma coisa. E a ordem publicada deixou de ser a
ordem da nota: o 2º colocado do perfil de prazo tem nota maior que o 1º, e mesmo assim vem
depois, porque sobrevive menos.

**Custo medido:** 1,3 s para 975 fundos × 200 simulações. A execução completa vai de 24 s
para 36 s.

---

## D-034: O primeiro Top 5 continha fundos institucionais 🎥📊
**Quando:** 20/08, Fase 5 · **Situação:** olhar o resultado real antes de entregá-lo

O primeiro ranking com a simulação funcionando trouxe fundos com **17, 31 e 70 cotistas** e
dezenas de bilhões de patrimônio. Um fundo com 31 cotistas e R$ 63 bilhões não é produto de
varejo: é veículo institucional ou master rotulado "Público Geral".

Investigando, achei **dois defeitos de especificação meus**. Nenhum deles no código, ambos
nos critérios.

**Defeito 1: o corte de cotistas era decorativo.** Estava em 10, escolhido na Fase 1 para
"excluir exclusivos de fato". Medi a distribuição do varejo: o percentil 10 tem **31 cotistas**
e a mediana **924**. Um corte em 10 não exclui nada.

**Defeito 2: taxa zero declarada estava ganhando o percentil máximo.** 19,7% dos fundos
declaram taxa exatamente zero, e a distribuição não é aleatória:

| Cotistas | Fundos | Com taxa zero |
|---|---:|---:|
| < 100 | 200 | **22%** |
| 100 a 1.000 | 245 | 6% |
| > 1.000 | 409 | 6% |

A anomalia mora nos mesmos veículos institucionais. O zero não significa fundo gratuito.
significa que a taxa é cobrada no fundo investidor ou pelo distribuidor. Como custo é o
**maior peso dos dois perfis**, um zero aceito ao pé da letra entregava a melhor nota possível
a quem divulgou menos.

**Decisões:**

1. Corte de cotistas de 10 para **500**. Fica acima da faixa onde os dois artefatos vivem e
   mantém 59% do universo de varejo. É julgamento, está em configuração, e a medição que o
   sustenta está no YAML ao lado do número.
2. Taxa declarada como exatamente zero passa a ser tratada como **desconhecida**, e pontua
   neutro, não máximo. O valor declarado continua sendo reportado, com um sinalizador,
   porque a entrega deve dizer o que o fundo de fato informou.

**Efeito no funil:** 1.714 → **787** com o corte de cotistas; 975 → **520** no universo final;
varejo de 854 para **502**.

**Efeito no resultado:** os recomendados passaram a ter entre 743 e 141.715 cotistas, e taxas
reais de 0,02% a 0,15%. Nenhum fundo com taxa zero sobrou no Top 5.

**Sobre a regra 11, que proíbe ajustar critério depois de ver resultado:** ela vale a partir do
**teste no passado**, que ainda não rodou. O que aconteceu aqui é diferente e é a razão de
existir a etapa de revisão: o critério estava especificado errado, e o erro só ficou visível
quando o resultado saiu. Afrouxar um corte para um fundo entrar seria fraude; apertar um corte
porque ele estava deixando entrar quem o próprio critério dizia excluir é conserto. A distinção
está na direção da mudança e na justificativa, e as duas ficaram registradas antes do backtest.

---

## D-035: Revisão do primeiro resultado: seis conclusões 🎥
**Quando:** 20/08, Fase 5, com o primeiro ranking pronto

O primeiro Top 5 foi revisado com olhar externo, sem contexto do projeto. Seis conclusões.
**Nenhuma implementada nesta fase**, por decisão: o objetivo aqui é registrar o que se aprendeu
e reconhecer limitação, não sair consertando tudo a quatro dias da entrega.

### 1. Os pesos são a limitação mais séria, e são arbitrários

Não há como demonstrar que 30/20/15/15/10/10 é melhor que qualquer outro conjunto. A escolha
tem argumento (a taxa é o único número conhecido sobre 2026, e só 40% dos fundos bateram o CDI
em 2025), mas argumento não é prova.

**O que fica registrado como a postura defensável:** encontrar pesos ótimos é um problema
quantitativamente muito difícil, e este projeto não o resolve. O que ele garante é outra coisa
de que **se os pesos certos existirem e forem informados, o pipeline inteiro é robusto o
suficiente para produzir o ranking correto a partir deles.** Os pesos vivem em YAML, a
simulação de robustez mede quanto o resultado depende deles, e trocá-los não exige tocar em
uma linha de código.

Isso **promove a arbitrariedade dos pesos a limitação declarada de primeira ordem**, ao lado
da performance passada como proxy do futuro. As duas passam a ser nomeadas na entrega.

### 2. A concentração em Itaú é esperada, não é defeito

Oito dos dez recomendados são Itaú. A leitura: o Itaú pratica taxas artificialmente baixas nos
fundos de casa, e como custo é o maior peso, ele naturalmente se destaca. É consequência
coerente do critério, e não sintoma de erro. Continua valendo declarar na entrega, porque quem lê
precisa saber que a lista concentra em uma gestora e por quê.

### 3. O corte de 500 cotistas está razoável, e poderia ser maior

Mantido em 500 por ora. Registrado que subir é uma direção legítima, não um risco.

### 4. A taxa de aparição fica no motor, não na vitrine

Como validação estatística contra sobreajuste a um ano específico, ela é útil e fica. Como
produto para o investidor de varejo, **gera ruído**: uma lista com "apareceu em 42% das
simulações" ao lado do quinto colocado confunde mais do que informa.

**Decisão de produto:** a simulação continua rodando e continua determinando a ordem; a taxa
de aparição continua no `ranking.json` e na seção técnica. O `ranking.md` volta a apresentar
uma **lista simples**. A ser implementado na Fase 6.

### 5. As duas limitações mais graves

De toda a lista declarada, duas se destacam:

- **risco de crédito escondido**, porque o método não olha a carteira, e crédito privado no Brasil
  paga spread pequeno e constante até o dia em que não paga;
- **12 meses não dizem o que acontece em 2026.**

São as duas que devem aparecer com destaque no `ranking.md` e no vídeo, e não diluídas numa
lista de nove itens.

### 6. Reconhecer e seguir, em vez de consertar tudo

A decisão de processo: nada disso vira mudança de método agora. Vira limitação declarada e
backlog. A quatro dias da entrega, o que falta, o teste no passado e a documentação, vale
mais que uma tentativa apressada de otimizar pesos.

---

## D-036: O teste no passado validou o método 🎥📊
**Quando:** 20/08, Fase 5.5

O ranking foi reconstruído em 31/03, 30/06 e 30/09 de 2025, usando nada publicado depois de
cada data, e os cinco escolhidos foram medidos até 31/12/2025 contra a mediana dos elegíveis
e contra **mil carteiras de cinco fundos sorteados do mesmo universo**.

| Corte | Perfil | Top 5 | Mediana | Vantagem | Contra o acaso |
|---|---|---:|---:|---:|---:|
| 31/03 | liquidez | +10,93% | +10,66% | +27 pb | p92% ✅ |
| 31/03 | prazo | +10,90% | +10,69% | +20 pb | p84% ✅ |
| 30/06 | liquidez | +7,43% | +7,13% | +31 pb | p100% ✅ |
| 30/06 | prazo | +7,36% | +7,16% | +20 pb | p97% ✅ |
| 30/09 | liquidez | +3,49% | +3,39% | +10 pb | p98% ✅ |
| 30/09 | prazo | +3,32% | +3,39% | −8 pb | p51% ❌ |

**Veredito: validado.** Liquidez 3 de 3, prazo 2 de 3; o critério exigia 2 de 3.

### Dois erros meus, corrigidos antes de escrever o veredito, ambos contra mim

**1. Eu estava aplicando o critério mais frouxo do que ele foi escrito.** O texto congelado diz
"2 das 3 datas". Com dois perfis são seis resultados, e eu contei **5 de 6**, o que torna o
teste trivialmente mais fácil. Passou a ser aplicado **por perfil**: cada um clareia sozinho.
A leitura mais dura, e ainda passa.

É exatamente o que a regra 11 existe para pegar, com a diferença de que o erro estava na
*aplicação* do critério, não no critério.

**2. Percentil alto contra distribuição estreita não é ganho grande.** p98% soa forte; a
vantagem real é de **10 a 31 pontos-base**. Fundos pós-fixados rendem todos perto do CDI, então
a distribuição aleatória é apertada, e ficar no percentil 98 é ganhar de quase todos **por
pouco**. O relatório agora traz pontos-base ao lado do percentil.

### Por que o resultado é mais crível justamente por ser pequeno

Se tivesse aparecido +5% de vantagem em renda fixa, o certo seria desconfiar do próprio código.
Some-se que um caso **falhou** (p51%, praticamente moeda) e está na tabela, que o critério está
commitado desde a Fase 2 com data no histórico do git, e que fundos que pararam de publicar
foram mantidos pelo último valor, conforme política também congelada.

### O que não prova

Três recortes do mesmo ano, com um regime de juros só, **não são três observações
independentes**.

### E uma promessa da Fase 1 que se cumpriu

Escrevi na D-017 que o teste seria quase de graça *se* o point-in-time estivesse correto, e que
se fosse difícil de rodar seria sinal de que estava furado. Rodou como um comando.

---

## D-037: Extrato multi-ano ampliou o universo, e o resultado não mudou 📊
**Quando:** 20/08, Fase 6

A Fase 5.5 exigiu buscar o extrato de **todos os anos que a janela toca**, não só o do ano de
referência. Um fundo que protocolou em 2024 e não reprotocolou continua vigente em 2025, e
buscar um ano só fazia parecer que ele nunca tinha divulgado nada.

Isso melhorou também a rodada da data de referência: **520 → 580 fundos**, varejo de 502 para
559. O guardrail do funil disparou sozinho (+11,5% na última etapa), como deveria, e o baseline
foi restabelecido com o motivo escrito ao lado do número.

**O que vale registrar:** com 60 fundos a mais no universo, o teste no passado deu **exatamente
o mesmo resultado**, com p92/p100/p98 e p84/p97/p51 e as mesmas vantagens em pontos-base. Um método
cujo veredito virasse com 11% a mais de universo não seria um método. Este não virou.

**Efeito colateral bem-vindo:** a concentração caiu de 8 em 10 fundos numa única gestora para
6 em 10, com BTG, Daycoval e Inter aparecendo. O texto da entrega foi ajustado de "uma gestora"
para "poucas gestoras".

---

## D-038: Publicar a taxa "só desempenho" revelou o que a lista realmente é 🎥📊
**Quando:** 21/08, Fase 6

Numa revisão do repositório com olhar externo, apareceu que a `appearance_rate_variable_only`
era calculada e testada, e **nunca publicada**. Era uma promessa de docstring não cumprida no
produto. Decidi publicá-la.

Publicar mudou o entendimento do próprio resultado:

| Fundo | Aparição total | Só pelo desempenho |
|---|---:|---:|
| Itaú Crédito Bancário | 100% | **100%** |
| BTG Pactual CDB I | 98% | **4%** |
| Itaú Janeiro (1º do perfil de prazo) | 100% | **3%** |
| Daycoval Títulos Públicos | 74% | **0%** |

A coluna responde: *este fundo continuaria no top 5 se fosse pontuado só por retorno, ganho
sobre o CDI, oscilação e pior queda, ignorando taxa e prazo?* Para quase todos, **não**.

**Isso não é defeito. É a D-012 funcionando exatamente como projetada.** A taxa é o maior
peso, de propósito. Mas a magnitude é muito maior do que eu esperava, e leva a uma frase que
precisa estar na entrega:

> Esta é, em grande parte, uma lista de **custo e liquidez**. Os cinco fundos não seriam os
> mesmos se o critério fosse desempenho passado.

**Correção de redação que fiz junto:** eu tinha descrito a coluna como medida de "estabilidade
mecânica". Está errado. Ela não mede quanto da robustez é artefato. Mede se o fundo sobrevive
a um critério diferente. Descrever mal um número publicado é pior que não publicá-lo.

**Um fundo passou nas duas:** o Itaú Crédito Bancário, com 100% nas duas colunas. É o único da
lista que é escolhido tanto por custo quanto por desempenho.

---

## D-039: A janela mede exatamente os meses que ela declara 📊🎥

**Situação:** uma janela de doze meses terminando em 31/12/2025 pode começar em dois
lugares: no primeiro dia do mês doze meses atrás (01/12/2024), ou no dia seguinte à
mesma data doze meses atrás (01/01/2025). A diferença é um mês inteiro.

**Decisão:** a janela é fechada nas duas pontas e contada a partir da própria data de
referência. Doze meses terminando em 31/12/2025 começam em **01/01/2025** e contêm
**252 dias úteis**.

**Por quê:** a alternativa não quebra nada. Fundo e benchmark são compostos sobre a
mesma janela, então o excesso continua internamente coerente e nenhum teste fica
vermelho. O que ela produz é um retorno de treze meses publicado sob a palavra "doze",
que ninguém consegue reconciliar com o que o próprio fundo divulga, e um CDI de 15,39%
onde o ano-calendário fez 14,3242%. É o pior tipo de erro que este projeto pode ter:
invisível por dentro, checável por fora.

**O que garante isso:** `tests/unit/test_window.py` verifica a propriedade para 1, 3, 6,
12, 24 e 36 meses, incluindo os casos chatos, porque 31 de março menos um mês não tem 31 de
fevereiro para cair, e 29 de fevereiro só existe em ano bissexto. E
`test_published_output.py` refaz a conta a partir do `ranking.json` entregue: a distância
entre `window_start` e `reference_date` tem que bater com `lookback_months`.

**Consequência de contrato:** `window_start` é publicado no JSON. Um consumidor não tem
como conferir uma contagem de meses; tem como conferir duas datas.

---

## D-040: Cinco fundos, não cinco notas 🎥📊

**Situação:** uma gestora brasileira roda uma carteira só e a vende através de várias
classes de distribuição. Medi: a Caixa oferece **doze** sobre uma única carteira de renda
fixa: Executivo, Clássico, Personal, Investidor, Especial, Empreender. Cada uma é uma
classe separada no registro da CVM, cada uma é elegível, e cada uma tira quase a mesma
nota, porque são quase o mesmo fundo.

Uma nota ranqueia fundos um a um. Uma lista de cinco é consumida de uma vez, por alguém
que vai carregar os cinco. São perguntas diferentes, e um Top 5 com dois invólucros da
mesma carteira entrega quatro exposições sem avisar.

**Decisão:** o ranking escolhe os cinco primeiros que sejam **distinguíveis entre si**.
Dois fundos contam como um quando a mesma gestora roda os dois **e** a diferença entre
suas séries de retorno quase não oscila.

**A medida é a diferença e não a correlação, e isso importa.** Correlação não resolve este
problema neste mercado: todo fundo pós-fixado segue a mesma curva de um dia e correlaciona
acima de 0,99 com todos os outros. Medi no universo elegível: mesmo a 0,999, a correlação
marca 161 fundos como duplicata de alguma coisa. A pergunta certa não é *estes dois se
movem juntos* e sim *quanto estes dois discordam*. Dois invólucros de uma carteira diferem
só pela taxa, que é um arrasto constante e não gera variância nenhuma.

**O limiar, medido:** volatilidade anualizada da diferença abaixo de **0,10% ao ano**. Os
gêmeos conhecidos, Itaú Janeiro e Itaú Private Janeiro, CNPJs sequenciais e mesma carteira,
ficam em 0,062%. Os pares mais apertados do universo ficam em 0,0001%. Exigir a mesma
gestora é o que separa "uma casa vendendo uma carteira duas vezes" de "duas casas rodando
fundos Selic parecidos", que para o cliente é escolha de verdade.

**A ordem nunca é rearranjada.** A regra decide se um candidato acrescenta algo ao que já
foi aceito, nunca promove ninguém por cima de quem estava melhor colocado.

**Nada fica escondido:** o fundo deixado de fora é publicado ao lado da lista, com nome, o
fundo que ele repete e a distância entre os dois. Na entrega de 31/12/2025 é o BTG Pactual
Tesouro Selic, que repete o BTG Pactual CDB I a 0,036% ao ano de distância.

**A simulação aplica a mesma regra.** Contar sobrevivência sobre uma lista construída por
um critério diferente do que produz a resposta mediria a estabilidade de algo que ninguém
vê.

---

## D-041: Peso só vale para critério que separa 📊

**Situação:** o perfil de liquidez filtra para resgate em até um dia e depois dá peso 10
ao prazo de resgate. Medido no universo elegível: **214 dos 218 fundos liquidam em D+0**.
Todos empatam, o percentil sai 0,5 para todo mundo, e dez dos cem pontos não decidem nada.

**Decisão:** um critério cuja dispersão no universo elegível fique abaixo de um piso
declarado é tratado como inerte. Seu peso é redistribuído proporcionalmente entre os
critérios que ainda distinguem, e o `ranking.json` nomeia o critério e publica os pesos
**de fato aplicados** ao lado dos declarados.

**Por quê:** elegibilidade e pontuação respondem perguntas diferentes, e um critério pode
ser decisivo na primeira e vazio na segunda. Prazo de resgate já fez o trabalho dele como
filtro; como critério ele não tem mais o que dizer. Carregar o peso morto em silêncio
significa que os outros critérios valem 11% mais do que o arquivo de configuração afirma,
sem que ninguém consiga ver isso.

**Por que isso não é mexer nos pesos depois de ver o resultado.** A regra 11 proíbe ajustar
peso, corte ou métrica em função do que o teste devolveu. Isto é uma regra sobre a **forma
do dado**, aplicada igual a todo perfil e a toda data de referência, e escrita como
`min_dispersion` em YAML. Ninguém escolheu qual critério cai: o universo é que decide, a
cada execução. No perfil de prazo, com resgate espalhado de D+0 a D+30, nenhum critério é
inerte e os pesos aplicados são os declarados.

---

## D-042: Duas notas por fundo: dentro do grupo e contra o universo 🎥

**Situação:** a D-008 estabeleceu que cada métrica vira posição relativa dentro do grupo
ANBIMA, para não premiar quem tomou mais risco de crédito. Essa é a pergunta certa e ela é
**silenciosa sobre o grupo**: ser o primeiro de dezoito vale 1 num grupo forte e num grupo
fraco. O Top 5 final mistura grupos e soma esses percentis como se fossem comensuráveis.

**Decisão:** todo fundo publica duas notas. A nota contra os pares da categoria, que
decide o ranking, e a mesma nota recalculada contra **todo o universo elegível do perfil**.

**Por quê:** é a informação que falta para ler a lista, e ela é barata. Na entrega de
31/12/2025 o Daycoval Títulos Públicos tira 83,2 no grupo e **66,9** no universo: é o
melhor de uma categoria que não é boa. O Itaú Janeiro tira 89,9 e 86,8, e as duas notas
próximas dizem outra coisa: ele é bom contra os pares e continua bom contra tudo.

**O que eu não faço:** inventar um termo de qualidade de grupo para "corrigir" a soma.
Isso exigiria afirmar que uma categoria vale mais que outra, que é exatamente o julgamento
que a comparação intra-grupo existe para não ter que fazer. Publicar as duas notas entrega
o julgamento a quem lê.

---

## D-043: A reamostragem sorteia por fundo, e o benchmark vai junto 🎥📊

**Situação:** a simulação de robustez (D-011) responde quanto da vantagem de um fundo
sobre outro é sorte de amostra. Três detalhes de implementação decidem se a resposta
significa alguma coisa.

**Decisão 1: cada fundo sorteia os próprios blocos.** A grandeza estimada é
idiossincrática: quanto do resultado *deste* fundo é acaso. Dar a todos o mesmo calendário
reamostrado preserva o comovimento do mercado, o que soa conservador e é o contrário:
move a seção transversal inteira junta, deixa a ordem relativa quase intacta, e devolve
taxas de sobrevivência perto de 100% para um ranking que ninguém estressou. O preço é que
um ano simulado não contém crash comum; está declarado e é o erro mais barato dos dois.

**Decisão 2: o benchmark é reamostrado com o fundo.** Excesso é diferença entre duas
séries compostas, então os dois lados precisam ser compostos sobre os mesmos dias. Medir um
ano reamostrado do fundo contra o CDI do ano-calendário enviesa todo excesso. E como
retorno por unidade de risco divide essa diferença pela volatilidade, um viés que se
cancelaria num ranking por excesso **não se cancela ali**. Ele reordena, a favor dos fundos
mais voláteis. É o mesmo mecanismo da D-030, aplicado a outro lugar.

**Decisão 3: cada fundo mantém o próprio comprimento de histórico.** Truncar o painel
inteiro no fundo mais curto jogaria fora um quinto da evidência de todo mundo para acomodar
o mais novo. O painel é alinhado à esquerda e preenchido, e o preenchimento fica fora de
toda estatística em vez de ser contado como calmaria.

**Efeito medido:** as taxas de aparição saem do aglomerado de 97–100% e passam a ocupar a
faixa de 31% a 99%. O ranking não ficou menos confiável. Ele parou de afirmar uma
confiança que não tinha.

---

## D-044: O teste no passado mede o universo inteiro, e diz contra o que 🎥📊

**Situação:** a D-017 desenhou o teste fora da amostra com três comparações. Duas escolhas
de implementação decidem se ele é um teste ou um espelho.

**Decisão 1: os retornos futuros são lidos do painel validado completo**, não do
universo elegível na data final. Um fundo escolhido em março que encolheu abaixo do corte
de cotistas até dezembro **continua tendo tido um retorno**. Ler o resultado do conjunto
sobrevivente o descarta em silêncio da média, e a média passa a ser dividida pelos fundos
que deram certo. É o viés de sobrevivência que este projeto critica em três documentos,
aplicado ao teste que existe para detectá-lo.

A garantia está escrita como propriedade em `test_out_of_sample.py`: o divisor é sempre o
número de fundos que o método escolheu, nunca o número deles que era mensurável. Um fundo
sem cota nenhuma depois do corte entra com o último valor conhecido, conforme a política
congelada, e sai nomeado no relatório.

**Decisão 2: o CDI é composto sobre exatamente os dias medidos** e publicado na tabela.
Uma comparação anunciada e não calculada é pior do que uma comparação ausente.

**Decisão 3: entra um controle casado por custo.** A taxa sai da cota antes de qualquer
medição, então um ranking cujo maior peso é a taxa ganha parte de qualquer vantagem por
aritmética conhecida antes do teste. O relatório repete o sorteio usando só o quartil mais
barato do mesmo universo.

**Esse controle é reportado e não faz parte do critério**, que foi congelado antes de ele
existir. E ele **não é experimento limpo**: segurar o custo também muda a composição do
grupo, porque o quartil mais barato é dominado por fundo de título público, que rende bruto
menos que crédito. É um segundo ângulo, não uma decomposição entre custo e habilidade, e o
relatório diz isso com essas palavras.

**O resultado, como ele saiu:** veredito de aprovação, com liquidez 2 de 3, prazo 3 de 3,
contra o critério de 2 de 3 por perfil. E, na mesma tabela: o Top 5 ficou acima da mediana
dos elegíveis em **dois de seis** recortes, e **abaixo do CDI nos seis**. A vantagem sobre a
mediana vai de −15 a +21 pontos-base. O texto do relatório é gerado a partir desses números
em vez de afirmar uma leitura fixa, justamente para que ele não possa continuar otimista
quando os números deixarem de ser.

---

## D-045: Os entregáveis moram no repositório 📊

**Situação:** o enunciado pede `ranking.md` no repositório GitHub. Um arquivo que só passa
a existir depois que alguém roda o pipeline não está entregue, e um README que aponta para
ele vira link quebrado para quem clona.

**Decisão:** `saida/` é versionada. `dados/` não.

**Por quê:** a distinção é entre o que prova o resultado e o que o reconstrói. Os dados
brutos são pesados, reconstruíveis e sujeitos a retificação silenciosa pela CVM, o que os
prende à execução não é o arquivo, é o hash SHA-256 de cada fonte, que já viaja dentro do
`ranking.json`. O resultado é o produto.

A execução semanal comita direto em `saida/`, no mesmo lugar para onde o README, o desenho
e a lista de entregáveis do enunciado apontam. Uma segunda cópia sob outro nome significaria
duas respostas no repositório e nenhuma forma de saber qual é a atual.

---

## D-046: Testes que leem o arquivo entregue 🎥

**Situação:** a suíte cobre invariantes financeiras, contratos de fronteira e as doze
armadilhas da CVM. Tudo isso testa **componentes contra fixtures**, e isso deixa passar uma
classe inteira de defeito: a maquinaria funcionando perfeitamente e a resposta publicada
ainda assim errada.

Uma janela rotulada com o número errado de meses, um Top 5 com a mesma carteira duas vezes,
um critério com peso que empata para todo fundo do universo, um campo de contrato publicado
vazio. Nenhum quebra função nenhuma, e nenhum aparece numa suíte verde que só olha para
dentro.

**Decisão:** `tests/integration/test_published_output.py` abre o `ranking.json` e o
`ranking.md` entregues e afirma contra o produto. Que a janela tem a duração que o rótulo
promete. Que nenhuma lista repete uma carteira. Que os pesos aplicados somam 100 e que um
critério inerte está nomeado. Que todo grupo de pares diz contra qual benchmark foi medido.
Que todo fundo publica seu regime tributário e as duas notas.

**A regra que fica:** todo campo publicado precisa de um teste que falharia se ele saísse
vazio, com o rótulo errado, ou repetido. É a fronteira que outro time consome.


---

## D-047: A taxa declarada não é o preço do cliente, então ela passa a ser medida 🔄🎥📊

**Quando:** 24/08, Fase 6 · **Reverte:** a fonte da taxa em D-002 · **Segue de:** D-040

**O que me fez olhar.** Comparei o Top 5 entregue com listas publicadas na imprensa. Não
para copiar critério de ninguém, e sim para ver se o nosso resultado fazia o mínimo de
sentido. A InfoMoney, com dados da Economática, publica os 25 fundos de renda fixa com mais
cotistas do mercado. Dois dos nossos estavam lá, com cotistas e retorno batendo com os
nossos, e com a taxa divergindo dez vezes: 0,37% e 0,42% deles, contra 0,040% nossos.

**O que estava errado.** Nossa leitura do `extrato_fi_2025.csv` estava correta: o arquivo
diz 0,040000 mesmo. O que não é verdade é o que o campo significa. A mesma classe, o mesmo
CNPJ, declarava 0,400% em 2024 e 0,900% em 2023. Não é vírgula deslocada, porque há classes
que declaravam 2,60% e hoje declaram 0,040%. É a forma como uma casa passou a preencher o
extrato depois da reorganização em classes da RCVM 175. No arquivo inteiro, **580 das 2.655
classes presentes nos dois anos tiveram a taxa cair três vezes ou mais**, e 235 foram parar
em exatamente 0,040%.

**Duas hipóteses minhas caíram antes de eu achar a certa.** Primeiro achei que o custo
estivesse escondido no fundo master. Baixei a composição de carteira, achei os masters, e
eles declaram 0,000%. Depois achei que fosse erro de digitação de uma casa decimal. Não é:
de 0,900 para 0,040 não é uma casa.

**Decisão: a taxa deixa de ser lida e passa a ser medida.** Uma classe alimentadora aplica
quase todo o patrimônio num único fundo. As duas séries de cota são a mesma carteira, e a
única coisa que as separa é o que a classe cobra. Então

> taxa = 1 − (crescimento da classe ÷ crescimento do master) ^ (1 ÷ anos)

Não depende de campo declarado, de plano de contas, nem de fonte externa. Precisa de duas
séries de cota, que já temos, e de saber quem é o master, que vem da CDA. **A CDA é fonte
nova no projeto**, e é o único lugar em que a CVM nomeia o fundo por trás de uma classe.

A definição é geométrica e não a diferença simples de retornos. Taxa é cobrada todo dia, e
compõe. Anualizar a diferença simples daria números diferentes conforme o tamanho da janela,
o que penalizaria justamente os fundos com menos histórico. Há um teste que mede a mesma
taxa em 126 e em 252 dias e exige o mesmo resultado.

**O que a medição devolveu**, sobre os 252 dias úteis de 2025:

| Fundo | Declarada | Medida | Erro |
|---|---:|---:|---:|
| Itaú Janeiro RF Longo Prazo | 0,040% | 1,814% | 45x |
| Itaú Global Dinâmico | 0,040% | 0,641% | 16x |
| Itaú RF Diferenciado | 0,040% | 0,511% | 13x |
| Itaú Crédito Bancário | 0,040% | 0,396% | 10x |
| BB RF Longo Prazo Corporate | 0,200% | 0,202% | 1,0x |

O BB estar certo é a parte que impede a conclusão preguiçosa. O campo não é inútil, e a CVM
não está errada: é uma casa específica preenchendo de um jeito específico. A correção
precisava ser cirúrgica, não geral.

O número medido bate com a Economática por caminho independente: 0,396% e 0,511% contra
0,37% e 0,42%.

**Três regras conservadoras, e cada uma custa ao fundo em vez de premiá-lo.**

1. Onde os dois números existem, **vence o maior**. Uma classe não cobra menos do que a
   própria gestora declarou para ela, então medida abaixo da declarada é ruído ou a parcela
   que a alimentadora mantém fora do master, não desconto. Acreditar numa taxa baixa demais
   promove um fundo a um Top 5 que ele não ganhou.
2. Classe que investe através de outros fundos e **não pôde ser medida fica sem taxa**. O
   campo é não confiável exatamente para esse tipo de classe, então para elas ele não é
   evidência. O fundo sai pela regra que já existia, a de não recomendar o que não se
   consegue precificar. É o mesmo tratamento que a taxa declarada como zero já recebia.
3. Fundo que detém ativos diretamente mantém o que declarou. O problema é de uma família de
   classes, não do mercado.

**O corte de 95% ficou onde estava.** Uma classe precisa ter 95% do que aplica em fundos
concentrado num só para que a diferença entre as séries seja taxa e nada mais. Baixá-lo para
90% alcançaria mais 483 classes, e teria salvado o Itaú Global Dinâmico, que aplica 90% e
ficou sem medição. Mas eu escolhi 95% e escrevi a justificativa antes de rodar, e mexer nele
depois de ver qual Top 5 ele produz é a regra 11. O Global Dinâmico saiu pela regra 2, que é
mais severa e não depende de eu escolher um número olhando para o resultado.

**O guardrail do funil disparou, em −11,38%**, e foi assim que se soube o tamanho do efeito:
a última etapa caiu de 580 para 514 classes. O baseline foi reescrito com o motivo ao lado,
como em D-029. Sessenta e seis alimentadoras cujo master não se pôde identificar deixaram o
universo.

**O Top 5 mudou nos dois perfis, e o Itaú saiu inteiro do de liquidez.** O Itaú Janeiro era
o número 2 das duas listas e cobra 1,814%, contra uma mediana de universo de 0,50%. Ele não
era um dos mais baratos do Brasil: era dos caros, e o maior peso do ranking o tratava como o
mais barato possível.

**O que isso obriga a reler.** O projeto registrou, em quatro lugares, que a concentração no
Itaú refletia o mercado que o varejo tem. Parte dela era artefato de preenchimento. A frase
foi corrigida onde aparecia.

**Limite declarado.** A medição só alcança classes alimentadoras, porque um fundo que detém
títulos diretamente não tem contra o que ser comparado. E quando a alimentadora mantém caixa
ao lado do master, a diferença carrega também essa parcela, o que faz da medida um teto e
não um valor exato. O corte de 95% é o que limita esse erro.

Trilha completa, com origem e hash de cada arquivo, em `docs/04-investigacao-taxa.md`.

---

# Material para a apresentação

*Seção viva: vou alimentando conforme o projeto anda.*

## Surpresas (o que eu não esperava encontrar)

**Nos dados**

1. O arquivo de cadastro que todo tutorial usa está obsoleto: 10,3% de cobertura, zero taxas.
2. A data de início do fundo no registro é mentira: diz 2025 para fundos de 1994.
3. A quebra de layout do informe diário é em jan/2024, não em nov/2024 como eu supunha.
4. A ANBIMA não é fechada: os índices baixam sem credencial. Eu tinha desistido cedo demais.
   *(E depois: baixam, mas só a foto do dia, que não serve para uma data passada.)*
5. A falta de dado de taxa não é aleatória, segue a regulação. Varejo é obrigado a publicar
   lâmina; qualificado não. Por isso a cobertura cai de 64% para 28%.
6. O registro de fundos **repete 1.046 chaves**, com linhas idênticas.
7. O extrato tem **194 aspas duplas soltas** em texto livre, que quebravam a leitura inteira.
8. Extrato e lâmina nomeiam as mesmas colunas de formas diferentes.
9. Prazo de resgate vem em dias úteis **ou** corridos, misturados na mesma base.
10. O Banco Central recusa a série do CDI inteira com HTTP 406: 11 anos é recusado,
    14 meses é servido.
11. **Só 40% dos fundos bateram o CDI em 2025.** A mediana ficou 0,19% abaixo. O fundo mediano
    de renda fixa brasileiro perdeu do CDI, e o custo come o prêmio.

**No próprio processo**

12. Escrever o teste primeiro pegou um erro de desenho antes de virar código: dois testes
    especificavam leitura de arquivo dentro do módulo de cálculo.
13. **Dois testes meus estavam errados e o código certo.** Um fixava o estimador de desvio
    padrão por acidente, outro esperava 1,7069 onde a resposta é 1,704814.
14. O guardrail do funil **não pegou** um erro de 2% que cabia na tolerância (D-024), e
    **pegou** três desvios reais depois (D-029). Saber quando cada coisa acontece vale mais
    que dizer que ele funciona.
15. Uma substituição de texto num script meu falhou em silêncio porque o formatador tinha
    reformatado o bloco, o mesmo tipo de falha silenciosa que o projeto inteiro combate.

## Números que valem citar

| Número | |
|---|---|
| 36.594 → 580 | o funil inteiro, de todas as classes registradas ao universo investável |
| R$ 4,4 trilhões | patrimônio do universo antes do corte de divulgação |
| 10,3% e 0% | cobertura e preenchimento de taxa do `cad_fi.csv` |
| 66% vs 5,3% | fundos "com menos de 1 ano" pelo campo errado vs pelo certo |
| 7,4 anos | idade real mediana dos fundos |
| ±1,5 | incerteza sobre a medida de retorno ajustado ao risco com 12 meses |
| 93% → 61% | cobertura do universo conforme a janela vai de 12 para 60 meses |
| 89.749 linhas / 88.617 ids | o registro repete 1.046 fundos, e o join inflava o universo em 2% |
| 194 aspas soltas | quebravam a leitura de um arquivo de 12 MB |
| 31 MB em 2,7 s | as cinco fontes baixadas do zero, com repetição e disjuntor |
| 6,3 milhões de linhas em ~4 s | um ano de informe diário lido, validado e reduzido a painel |
| 0,55% em quarentena | por cota não positiva, com o motivo escrito linha a linha |
| **CDI 2025 = 14,3242% em 252 dias úteis** | a janela de 12 meses tem 252 dias e não 273, e é isso que faz o número bater com o que o fundo publica |
| **40%** | dos 580 fundos elegíveis bateram o CDI. A mediana ficou **0,19% abaixo** |
| 58% do varejo é D+0 | por isso um ranking único de varejo não serve |
| **214 de 218** | fundos do perfil de liquidez liquidam em D+0, então prazo de resgate é filtro e não critério, e o peso dele é redistribuído |
| **12 invólucros, 1 carteira** | classes de distribuição que a Caixa oferece sobre uma única carteira de renda fixa |
| **0,062% a.a.** | a distância entre Itaú Janeiro e Itaú Private Janeiro: mesma carteira, dois nomes, dois CNPJs sequenciais |
| 0,99 para todo mundo | por que correlação não identifica gêmeo em renda fixa pós-fixada: todos seguem a mesma curva |
| 288 testes verdes | incluindo os que abrem o `ranking.json` entregue e testam o produto, não a função |
| **p68 · p99 · p22 / p71 · p94 · p72** | o Top 5 contra mil carteiras aleatórias, em três datas de corte, nos dois perfis |
| **2 de 6 e 0 de 6** | recortes em que o Top 5 bateu a mediana dos elegíveis, e em que bateu o CDI |
| −15 a +21 pontos-base | a vantagem real sobre a mediana: pequena nos dois sentidos, e é por isso que três cortes não distinguem método de sorte |
| 83,2 no grupo, 66,9 no universo | o 1º do perfil de prazo é o melhor de uma categoria que não é boa, e as duas notas dizem isso |
| 99% vs 1% | o mesmo fundo some do top 5 quando pontuado só por desempenho: a lista é de custo |

## Esqueleto do vídeo (5 min)

| Tempo | Assunto | Apoio |
|---|---|---|
| 0:00–0:35 | O problema, e o funil de 36.594 para 514 | `relatorio_qualidade.md` |
| 0:35–1:35 | **Fui olhar o dado antes de codar.** As armadilhas que não geram erro nenhum | D-001, D-002, D-003 |
| 1:35–2:15 | Como decido o que é "melhor": grupo de pares, perfil, e por que a **taxa pesa mais que a rentabilidade**, com o dado de que só 40% bateram o CDI | D-008, D-012 |
| 2:15–2:55 | **Funciona?** O teste no passado e o percentil contra carteiras aleatórias | D-017, `validacao.md` |
| 2:55–3:35 | **A decisão que menos me convence** e o que a simulação não vê | D-011 |
| 3:35–4:05 | Onde meu próprio guardrail falhou, e onde acertou | D-024 vs D-029 |
| 4:05–4:30 | O que o projeto não vê: a carteira | seção 13 do desenho |
| 4:30–5:00 | Caminho para produção: um comando, uma função, um agendador | workflow semanal |

### Frases que já estão prontas para usar

- *"Criei um guardrail para pegar junção quebrada. Ele não pegou a minha, porque 2% cabia na
  tolerância de 3%. Verificação por percentual não substitui invariante exata."*
- *"Escrevi um teste que dizia 1.7069. O código disse 1.704814. O código estava certo."*
- *"Só 40% dos fundos de renda fixa bateram o CDI em 2025. É por isso que a taxa pesa mais que
  a rentabilidade passada no meu ranking, e isso não é teoria, é o dado."*
- *"Um fundo cuja cota não se move não é um fundo sem risco. É um fundo que parou de ser
  precificado. Por isso ele é excluído, não premiado."*
- *"Os cinco primeiros não são distinguíveis entre si. Eu digo isso na entrega em vez de
  fingir precisão que os dados não têm."*
