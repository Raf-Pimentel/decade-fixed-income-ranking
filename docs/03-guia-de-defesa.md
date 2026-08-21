# Guia de defesa

Tudo o que é preciso saber para apresentar este projeto e responder a quem o questionar.
Escrito para ser lido de uma vez, na véspera.

Os documentos irmãos: `01-solution-design.md` é o desenho, `decisoes.md` é o histórico
completo com 38 entradas, `02-checklist.md` é o que foi e o que não foi feito.

---

## 1. O projeto em um parágrafo

Existem 36.594 classes de fundos registradas na CVM. Este projeto identifica os cinco melhores
fundos de renda fixa para o investidor de varejo brasileiro, com data de referência 31/12/2025,
usando só dados públicos. Ele reduz o universo a **580 fundos que um cliente de fato consegue
comprar**, calcula dez números por fundo a partir da cota diária, compara cada fundo **apenas
com fundos parecidos**, aplica pesos diferentes conforme quando o cliente precisa do dinheiro,
e — antes de publicar — refaz o ranking mil vezes para testar se ele se sustenta. Roda com um
comando, em cerca de 40 segundos, e foi validado fora da amostra.

---

## 2. Os números que você precisa saber de cor

| Número | O que é |
|---|---|
| **36.594 → 580** | O funil inteiro, de todas as classes registradas ao universo investável |
| **559** | Quantos desses são acessíveis ao varejo |
| **14,3242%** | CDI acumulado em 2025, em exatamente 252 dias úteis |
| **40%** | Apenas 40% dos 580 fundos bateram o CDI. A mediana ficou **0,19% abaixo** |
| **0,50%** | Taxa de administração mediana do universo, ao ano |
| **6,3 milhões** | Linhas de informe diário lidas e validadas, em ~4 segundos |
| **0,55%** | Fração das linhas que foi para quarentena |
| **231** | Testes automatizados. Cobertura de 93% nos módulos de cálculo |
| **p92 / p100 / p98** | Onde o Top 5 de liquidez ficou contra mil carteiras aleatórias, nas três datas |
| **+10 a +31 pb** | A vantagem real sobre a mediana. Pequena — e é por isso que é crível |

---

## 3. O resultado

### Varejo — reserva de emergência · 218 elegíveis

| # | Fundo | Taxa | Resgate | Rendeu | vs CDI |
|---:|---|---:|---:|---:|---:|
| 1 | Itaú Crédito Bancário RF Crédito Privado | 0,040% | D+0 | 15,42% | +0,03% |
| 2 | BTG Pactual CDB I RF | 0,150% | D+0 | 15,32% | −0,07% |
| 3 | Itaú RF Referenciado DI Grau de Investimento | 0,040% | D+0 | 15,23% | −0,16% |
| 4 | Itaú Global Dinâmico RF Longo Prazo | 0,040% | D+0 | 15,87% | +0,48% |
| 5 | BTG Pactual Tesouro Selic | 0,200% | D+0 | 15,13% | −0,26% |

### Varejo — dois anos ou mais · 390 elegíveis

| # | Fundo | Taxa | Resgate | Rendeu | vs CDI |
|---:|---|---:|---:|---:|---:|
| 1 | Itaú Janeiro RF Longo Prazo | 0,040% | D+0 | 17,54% | +2,15% |
| 2 | Itaú Global Dinâmico RF Longo Prazo | 0,040% | D+0 | 15,87% | +0,48% |
| 3 | Itaú Private Janeiro RF Longo Prazo | 0,040% | D+0 | 17,56% | +2,17% |
| 4 | Daycoval Títulos Públicos I | 0,050% | D+0 | 15,37% | −0,02% |
| 5 | Inter Hedge FIF Incentivado de Infraestrutura | 0,050% | D+29 | 16,92% | +1,53% |

---

## 4. As dez perguntas que vão te fazer, com a resposta

### 1. "Por que a taxa pesa mais que a rentabilidade?"

Porque a taxa é o **único número que se sabe com certeza sobre 2026**. A rentabilidade de 2025 é,
em boa parte, CDI que todo fundo pegou igual, mais um prêmio de crédito que ainda não deu
problema. E o dado sustenta: **só 40% dos fundos bateram o CDI, e o fundo mediano ficou 0,19%
abaixo.** O custo come o prêmio. Dar peso maior ao que persiste é mais defensável que dar peso
maior ao que não persiste.

### 2. "Como você sabe que os pesos estão certos?"

**Não sei, e o projeto não afirma isso.** Encontrar pesos ótimos é um problema quantitativamente
difícil que este trabalho não resolve. O que ele garante é outra coisa: **se os pesos certos
existirem e forem informados, o pipeline produz o ranking correto a partir deles.** Os pesos
vivem em YAML, a simulação mede o quanto o resultado depende deles, e trocá-los não toca em uma
linha de código.

Essa é a limitação número um da entrega, e está declarada como tal.

### 3. "Oito, agora seis, dos dez fundos são do Itaú. Isso não é problema?"

É consequência coerente do critério. As gestoras dos grandes bancos praticam taxas muito baixas
nos fundos de casa, e custo é o maior peso. Não é recomendação de concentrar — é o que o critério
devolve, e está declarado na entrega para quem lê não descobrir sozinho.

### 4. "Como você garante que o ranking não é só ruído?"

Não garanto por argumento — meço. Com doze meses de dados diários, a incerteza sobre o retorno
ajustado ao risco é da ordem de **±1,5**, maior que as diferenças entre os primeiros colocados.
Então o ranking é reconstruído **mil vezes**, reamostrando as séries de retorno em blocos e
sorteando os pesos dentro de faixas declaradas. Publico quem sobrevive, não quem tirou a maior
nota numa conta só.

**Detalhe que vale mostrar:** a ordem publicada não é a ordem da nota. No perfil de prazo, o 2º
colocado tem nota maior que o 1º e vem depois, porque sobrevive menos.

### 5. "O método funciona, ou é só bem argumentado?"

Testado fora da amostra. Reconstruí o ranking em **31/03, 30/06 e 30/09 de 2025**, usando nada
publicado depois de cada data, e medi os cinco escolhidos até o fim do ano contra a mediana dos
elegíveis e contra **mil carteiras de cinco fundos sorteados do mesmo universo**.

| Perfil | Bateu o acaso em | Vantagem |
|---|---|---|
| Liquidez | 3 de 3 datas (p92, p100, p98) | +10 a +31 pb |
| Prazo | 2 de 3 datas (p84, p97, p51) | −8 a +20 pb |

O critério — acima do percentil 60 em pelo menos 2 de 3 — estava **commitado antes** da execução,
com data no histórico do git.

### 6. "p98 parece muito. É muito?"

Não. Fundos pós-fixados rendem todos perto do CDI, então a distribuição das carteiras aleatórias
é estreita. **Ficar no percentil 98 de uma distribuição apertada é ganhar de quase todos por
pouco.** A vantagem real é de 10 a 31 pontos-base. Num mercado onde a taxa mediana é 0,50% ao
ano, algumas dezenas de pontos-base é exatamente a ordem de grandeza do que há para ganhar.

Se eu tivesse encontrado +5% de vantagem em renda fixa, o certo seria desconfiar do próprio
código.

### 7. "Qual a maior fraqueza?"

Três, nesta ordem:

1. **Os pesos são arbitrários** (ver pergunta 2).
2. **O método não olha a carteira.** Mede resultado, não conteúdo. Dois fundos com números
   idênticos podem carregar riscos de crédito completamente diferentes — e crédito privado paga
   um prêmio pequeno e constante por meses e devolve tudo de uma vez quando o emissor quebra. A
   CVM publica esse dado (arquivo CDA) e é o primeiro item do backlog.
3. **Doze meses não dizem o que acontece em 2026.** A validação usou três recortes de um ano só,
   com um regime de juros só — **não são três observações independentes**.

### 8. "Você mexeu em algum critério depois de ver o resultado?"

Sim, duas vezes, e as duas estão registradas — **ambas apertando, nunca afrouxando**:

- O corte de cotistas subiu de 10 para 500, porque o primeiro ranking real trouxe fundos com
  17, 31 e 70 cotistas e dezenas de bilhões — veículos institucionais rotulados varejo. O
  percentil 10 do universo de varejo tem 31 cotistas; um corte em 10 não excluía nada (D-034).
- O critério do backtest passou a ser aplicado **por perfil** em vez de somado. Eu estava
  contando 5 de 6 pares data-perfil, o que é mais fácil que 2 de 3 por perfil. Corrigi para a
  leitura mais dura, e passou mesmo assim (D-036).

A regra que congelei antes proíbe mexer **depois do teste no passado**. Nenhuma das duas foi
depois dele.

### 9. "Por que só CVM, e não a base da ANBIMA?"

A base de fundos da ANBIMA exige credencial. Mas o dado da ANBIMA que mais importa — **a
classificação que define os grupos de comparação** — chega dentro do registro da CVM. Cheguei
a planejar usar os índices IMA como benchmark por grupo e desisti: o arquivo é Excel binário e
a alternativa em texto é a foto do dia, não a série. Medi antes de desistir — 91,8% do varejo é
corretamente servido pelo CDI, 8,2% precisaria de IMA-B, prefixado puro é zero (D-030).

### 10. "Isso roda em produção?"

Já roda. `weekly-ranking.yml` executa o pipeline inteiro contra dados ao vivo toda segunda às
09:00 UTC e publica o resultado, sem ninguém olhando. O `pipeline.run()` é função pura e
importável — a linha de comando é uma casca fina sobre ela.

---

## 5. As três histórias que valem contar

Escolha uma ou duas. Elas mostram método, não resultado.

### A armadilha que não gera erro nenhum

O campo `Data_Inicio` do registro da CVM **não é a data de início do fundo** — é a data de
adaptação à Resolução 175. O CNPJ `00068305000135` diz 2025-05-12; o fundo foi constituído em
**1994**. Pelo campo errado, 66% do universo pareceria ter menos de um ano. Pela data certa, a
idade mediana é 7,4 anos.

Um filtro inocente de "fundos com mais de um ano" jogaria fora dois terços do universo,
incluindo fundos de trinta anos. **E o programa rodaria sem erro nenhum.**

### O guardrail que falhou, e o mesmo guardrail que acertou

Criei uma verificação que compara o funil de elegibilidade contra números medidos de antemão.
Ela **não pegou** um erro de 2% causado por chaves repetidas no registro da CVM — 89.749 linhas
para 88.617 ids — porque 2% cabia na tolerância de 3%.

Verificação por percentual não substitui invariante exata. Adicionei a regra dura: junção que
muda a contagem de linhas levanta erro, independente de tolerância.

Duas fases depois, **o mesmo guardrail parou a execução três vezes** e estava certo nas três.

### A simulação que não estava ligada

O primeiro ranking real saiu com **100% de aparição em quase todos os fundos**. Isso não é
resultado forte, é sintoma: significa que nada estava variando. A reamostragem em blocos existia,
tinha teste, e **nunca era chamada**.

Publicar aquele 100% teria sido exatamente a falsa precisão que o módulo existe para evitar.
Depois de ligada, as taxas passaram a ir de 100% a 34% — números que informam alguma coisa.

---

## 6. A coisa mais honesta da entrega

Publiquei uma segunda coluna que responde: *este fundo continuaria no top 5 se fosse pontuado
só por desempenho, ignorando taxa e prazo?*

| Fundo | Aparição total | Só desempenho |
|---|---:|---:|
| Itaú Crédito Bancário | 100% | **100%** |
| BTG Pactual CDB I | 98% | **4%** |
| Itaú Janeiro (1º do prazo) | 100% | **3%** |
| Daycoval Títulos Públicos | 74% | **0%** |

Para quase todos, a resposta é **não**. Isso não é defeito — é o peso da taxa funcionando como
projetado. Mas leva a uma frase que precisa estar na entrega:

> Esta é, em grande parte, uma lista de **custo e liquidez**. Os cinco fundos não seriam os
> mesmos se o critério fosse desempenho passado.

Um fundo passa nos dois critérios: o **Itaú Crédito Bancário**, 100% nas duas colunas.

---

## 7. Roteiro do vídeo — 5 minutos

| Tempo | Assunto | O que mostrar |
|---|---|---|
| 0:00–0:35 | O problema e o funil de 36.594 para 580 | `relatorio_qualidade.md` |
| 0:35–1:35 | Fui olhar o dado antes de codar — a armadilha do `Data_Inicio` | D-003 |
| 1:35–2:15 | Como decido o que é "melhor", e por que a taxa pesa mais | os 40% que bateram o CDI |
| 2:15–2:55 | **Funciona?** O teste contra mil carteiras aleatórias | `validacao.md` |
| 2:55–3:35 | **A decisão que menos me convence:** os pesos | a resposta da pergunta 2 |
| 3:35–4:05 | Onde meu próprio guardrail falhou | D-024 vs D-029 |
| 4:05–4:30 | O que o projeto não vê: a carteira | seção 13 do desenho |
| 4:30–5:00 | Caminho para produção — já está rodando | o workflow semanal |

### Frases prontas

- *"Só 37% dos fundos de renda fixa bateram o CDI em 2025. É por isso que a taxa pesa mais que
  a rentabilidade passada no meu ranking — e isso não é teoria, é o dado."*
- *"Criei um guardrail para pegar junção quebrada. Ele não pegou a minha, porque 2% cabia na
  tolerância de 3%."*
- *"Um fundo cuja cota não se move não é um fundo sem risco. É um fundo que parou de ser
  precificado. Por isso ele é excluído, não premiado."*
- *"Os cinco primeiros não são distinguíveis entre si. Eu digo isso na entrega em vez de fingir
  precisão que os dados não têm."*
- *"Se eu tivesse encontrado cinco por cento de vantagem em renda fixa, o certo seria desconfiar
  do meu próprio código."*

---

## 8. Se perguntarem o que falta

Com franqueza, e nesta ordem:

1. **Olhar a carteira dos fundos** (arquivo CDA da CVM). Fecha a lacuna principal.
2. **Validar em mais de um ano.** Três cortes de 2025 não são observações independentes.
3. **Separar habilidade de exposição.** Descontar do retorno a parte que veio de estar exposto a
   juros e crédito, e ranquear pelo que sobra.
4. **Corrigir a volatilidade subestimada** dos fundos de crédito, que não são remarcados
   diariamente.
5. **Escolher os cinco como carteira**, não individualmente — hoje o Top 5 pode conter cinco
   fundos parecidos.
6. **Testar o `run_all()` do backtest.** É a função que produz a afirmação principal e tem a
   menor cobertura do repositório (61%).
