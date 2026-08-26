# Guia de Apresentação

Tudo o que é preciso saber para apresentar este projeto.

Os documentos irmãos: `01-solution-design.md` é o desenho, `decisoes.md` é o histórico
completo com 38 entradas, `02-checklist.md` é o que foi e o que não foi feito.

---

## 1. O projeto em um parágrafo

Existem 36.594 classes de fundos registradas na CVM. Este projeto identifica os cinco melhores
fundos de renda fixa para o investidor de varejo brasileiro, com data de referência 31/12/2025,
usando só dados públicos. Ele reduz o universo a **514 fundos que um cliente de fato consegue
comprar e cujo custo se consegue verificar**, calcula dez números por fundo a partir da cota diária, compara cada fundo **apenas
com fundos parecidos**, aplica pesos diferentes conforme quando o cliente precisa do dinheiro,
e, antes de publicar, refaz o ranking mil vezes para testar se ele se sustenta. Roda com um
comando, em cerca de 40 segundos, e foi validado fora da amostra.

---

## 2. Os números que você precisa saber de cor

| Número | O que é |
|---|---|
| **36.594 → 514** | O funil inteiro, de todas as classes registradas ao universo investável |
| **496** | Quantos desses são acessíveis ao varejo |
| **14,3242% em 252 dias úteis** | CDI acumulado em 2025. A janela de 12 meses tem 252 dias, e é isso que faz o retorno publicado bater com o que o fundo divulga |
| **40%** | Apenas 40% dos fundos bateram o CDI. A mediana ficou **0,19% abaixo** |
| **0,50%** | Taxa de administração mediana do universo, ao ano |
| **6,3 milhões** | Linhas de informe diário lidas e validadas, em ~4 segundos |
| **0,55%** | Fração das linhas que foi para quarentena |
| **305** | Testes automatizados, dos quais 11 abrem o `ranking.json` entregue e testam o produto |
| **0,040% contra 1,814%** | O que o Itaú Janeiro declarava e o que ele cobra. Era o nº 2 das duas listas até a taxa passar a ser medida |
| **235 classes em 0,040%** | Quantas foram parar exatamente nesse valor declarado depois da RCVM 175, vindas de até 2,60% |
| **580 → 514** | O que a regra conservadora tirou do universo: alimentadoras cujo custo não se consegue verificar |
| **D+0 quase sempre** | No perfil de liquidez, quase todo fundo que sobra liquida no mesmo dia, de modo que prazo é filtro e não critério |
| **12 invólucros, 1 carteira** | Classes que a Caixa oferece sobre uma única carteira |
| **p92 / p96 / p95** | Onde o Top 5 de liquidez ficou contra mil carteiras aleatórias, nas três datas |
| **6 de 6 · 0 de 6** | Recortes em que o Top 5 bateu a mediana, e em que bateu o CDI |
| **+8 a +22 pb** | A vantagem real sobre a mediana. Positiva nos seis, e pequena |

---

## 3. O resultado

Janela de **12 meses: 01/01/2025 a 31/12/2025**, 252 dias úteis. Benchmark CDI para todos os
grupos, declarado grupo a grupo no JSON.

### Varejo, reserva de emergência · 195 elegíveis

| # | Fundo | Taxa | Resgate | Rendeu | vs CDI | Nota grupo / universo |
|---:|---|---:|---:|---:|---:|---:|
| 1 | BTG Pactual CDB I RF | 0,150% | D+0 | 14,26% | −0,06% | 75,1 / 71,0 |
| 2 | BB Previdenciário RF Referenciado DI | 0,202% | D+0 | 14,42% | +0,09% | 74,9 / 73,6 |
| 3 | BNP Paribas Match RF | 0,350% | D+0 | 14,39% | +0,06% | 72,3 / 70,2 |
| 4 | Tivio Institucional RF Crédito Privado | 0,200% | D+0 | 14,71% | +0,39% | 70,4 / 65,9 |
| 5 | Itaú Empresa Trust RF Referenciado DI | 0,248% | D+0 | 14,35% | +0,02% | 71,5 / 71,9 |

**Peso redistribuído:** `redemption_days` valia 10 e não separa nada aqui, porque quase todo
fundo que sobra liquida em D+0. Os pesos de fato aplicados são taxa 27 · oscilação 22 ·
ganho sobre CDI 17 · pior queda 17 · tamanho 17.

**O 5º colocado declarou 0,040% e cobra 0,248%.** Ele entra na lista com a taxa medida, e o
`ranking.json` publica os dois números.

### Varejo, dois anos ou mais · 348 elegíveis

| # | Fundo | Taxa | Resgate | Rendeu | vs CDI | Nota grupo / universo |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Sicredi FIF RF Liquidez Empresarial DI | 0,150% | D+0 | 14,24% | −0,08% | 82,3 / **63,6** |
| 2 | SulAmérica Exclusive FIF RF Referenciado DI | 0,150% | D+0 | 14,24% | −0,08% | 82,6 / **63,0** |
| 3 | BB RF Longo Prazo Corporate | 0,202% | D+0 | 14,83% | +0,51% | 89,4 / 82,5 |
| 4 | Absolute Atenas Seleção RF Crédito Privado | 0,194% | D+0 | 14,66% | +0,34% | 79,7 / 77,1 |
| 5 | Sicredi FIF Institucional RF IRF-M LP | 0,180% | D+2 | 17,78% | +3,45% | 84,3 / 80,5 |

**Repare nos dois primeiros.** 82,3 e 82,6 contra os pares, 64,3 e 63,6 contra o universo
inteiro: são os melhores de uma categoria que não é boa. As duas notas existem para você
poder dizer isso antes que perguntem.

**Três taxas nas duas tabelas não são as declaradas.** O BB Corporate declarou 0,200% e cobra
0,202%, o Absolute Atenas declarou 0,080% e cobra 0,194%, e o Itaú Empresa Trust declarou
0,040% e cobra 0,248%. As três foram medidas contra o fundo que cada classe compra, e o
`ranking.json` publica os dois números lado a lado.

**Concentração:** o Itaú tem **26,2%** dos 195 fundos do perfil de liquidez e **19,2%** dos
348 do perfil de prazo, e ocupa uma das dez posições. Até 24/08 ocupava sete, com taxas
declaradas de 0,040% que a medição mostrou serem de 0,40% a 1,81%. O único que sobrou entra
com a taxa medida, não com a declarada. Ver D-047.

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
nos fundos de casa, e custo é o maior peso. Não é recomendação de concentrar. É o que o critério
devolve, e está declarado na entrega para quem lê não descobrir sozinho.

### 4. "Como você garante que o ranking não é só ruído?"

Não garanto por argumento. Eu meço. Com doze meses de dados diários, a incerteza sobre o retorno
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
| Liquidez | 3 de 3 datas (p92, p96, p95) | +9 a +22 pb |
| Prazo | 3 de 3 datas (p86, p95, p94) | +8 a +18 pb |

O critério, acima do percentil 60 em pelo menos 2 de 3 por perfil, estava **commitado antes**
da execução, com data no histórico do git.

**Estes números melhoraram em 24/08, e diga por quê antes que perguntem.** Até essa data eram
2 de 3 e 3 de 3, com vantagem de −15 a +21 pb. O que mudou foi a taxa: ela deixou de ser lida
no extrato e passou a ser medida contra o fundo que cada classe compra, o que corrigiu erros de
até 45 vezes. Um método que melhora logo depois de o autor mexer em alguma coisa é exatamente o
que um critério congelado existe para vigiar, então o essencial é a ordem dos fatos: o critério
de sucesso não se moveu desde que foi commitado, e a regra da taxa foi escrita e argumentada
antes desta execução. Ver D-047.

Os pesos foram revistos no mesmo dia, com a taxa caindo de 30 para 25 e de 25 para 23 (D-048).
**Essa revisão não moveu esta tabela em nada:** os seis percentis e as seis vantagens saíram
idênticos, até a segunda casa. A simulação de robustez já sorteia o peso da taxa dentro de uma
faixa de ±5, então um deslocamento de 5 pontos cai dentro do que ela já explorava. Se
perguntarem se os pesos foram ajustados para melhorar o resultado, a resposta é que mexer neles
não muda este resultado.

**Diga o resto da tabela antes que perguntem.** O Top 5 bateu a mediana dos elegíveis em **6 de
6** recortes, por margens de 8 a 22 pontos-base, e ficou **abaixo do CDI nos 6**. As medições saem do painel validado inteiro, não do
universo elegível no fim: um fundo escolhido em março que encolheu para fora do universo até
dezembro entra na média com o que ele fez. Ler o resultado só de quem sobreviveu é o viés de
sobrevivência que este teste existe para detectar.

### 6. "p96 parece muito. É muito?"

Não. Fundos pós-fixados rendem todos perto do CDI, então a distribuição das carteiras
aleatórias é estreita. **Num universo apertado, ficar no percentil 96 é ganhar de quase todos
por muito pouco.** A vantagem real vai de +8 a +22 pontos-base. Num mercado onde a taxa mediana é
0,50% ao ano, é exatamente a ordem de grandeza do que há para ganhar, e é pequena o bastante
para que três cortes dentro de um ano não distingam método de sorte.

Se eu tivesse encontrado +5% de vantagem em renda fixa, o certo seria desconfiar do próprio
código.

### 6b. "Quanto disso é só a taxa ser menor?"

Boa pergunta, e o relatório traz o controle: a mesma comparação contra carteiras sorteadas
apenas do **quartil mais barato** do universo. Como a taxa sai da cota antes de qualquer
medição, parte da vantagem é aritmética conhecida antes do teste.

E digo o limite do controle antes que apontem: ele não é experimento limpo. Segurar o custo
também muda a composição, já que o quartil mais barato é dominado por fundo de título público, que
rende bruto menos que crédito. É um segundo ângulo, não uma decomposição entre custo e
habilidade. Por isso ele é **reportado e não faz parte do critério**, que foi congelado antes
de ele existir.

### 7. "Qual a maior fraqueza?"

Três, nesta ordem:

1. **Os pesos são arbitrários** (ver pergunta 2).
2. **O método não olha a carteira.** Mede resultado, não conteúdo. Dois fundos com números
   idênticos podem carregar riscos de crédito bem diferentes. Crédito privado paga
   um prêmio pequeno e constante por meses e devolve tudo de uma vez quando o emissor quebra. A
   CVM publica esse dado (arquivo CDA) e é o primeiro item do backlog.
3. **Doze meses não dizem o que acontece em 2026.** A validação usou três recortes de um ano só,
   com um regime de juros só, então **não são três observações independentes**.
4. **A lista mistura categorias e soma percentis calculados dentro delas.** Ser o primeiro de
   dezoito vale 1 num grupo forte e num grupo fraco. Não invento um termo de qualidade de grupo
   para consertar isso. Publico as duas notas e entrego o julgamento a quem lê (D-042).

### 8. "Você mexeu em algum critério depois de ver o resultado?"

Sim, duas vezes, e as duas estão registradas. **Ambas apertando, nunca afrouxando:**

- O corte de cotistas subiu de 10 para 500, porque o primeiro ranking real trouxe fundos com
  17, 31 e 70 cotistas e dezenas de bilhões, ou seja, veículos institucionais rotulados varejo. O
  percentil 10 do universo de varejo tem 31 cotistas; um corte em 10 não excluía nada (D-034).
- O critério do backtest passou a ser aplicado **por perfil** em vez de somado. Eu estava
  contando 5 de 6 pares data-perfil, o que é mais fácil que 2 de 3 por perfil. Corrigi para a
  leitura mais dura, e passou mesmo assim (D-036).

A regra que congelei antes proíbe mexer **depois do teste no passado**. Nenhuma das duas foi
depois dele.

**E uma regra que redistribui peso, que não é a mesma coisa.** Um critério cuja dispersão no
universo elegível fica abaixo de um piso declarado é tratado como inerte e o peso vai para os
que ainda separam. É regra sobre a **forma do dado**, escrita como `min_dispersion` em YAML,
aplicada igual a todo perfil e a toda data: ninguém escolhe qual critério cai, o universo é que
decide a cada execução. No perfil de liquidez cai o prazo de resgate, porque quase todo fundo
que sobra liquida em D+0. No perfil de prazo não cai nada (D-041).

### 9. "Por que só CVM, e não a base da ANBIMA?"

A base de fundos da ANBIMA exige credencial. Mas o dado da ANBIMA que mais importa, **a
classificação que define os grupos de comparação**, chega dentro do registro da CVM. Cheguei
a planejar usar os índices IMA como benchmark por grupo e desisti: o arquivo é Excel binário e
a alternativa em texto é a foto do dia, e não a série. Medi antes de desistir: 91,8% do varejo é
corretamente servido pelo CDI, 8,2% precisaria de IMA-B, prefixado puro é zero (D-030).

### 10. "Isso roda em produção?"

Já roda. `weekly-ranking.yml` executa o pipeline inteiro contra dados ao vivo toda segunda às
09:00 UTC e publica o resultado, sem ninguém olhando. O `pipeline.run()` é função pura e
importável, e a linha de comando é uma casca fina sobre ela.

---

## 5. As três histórias que valem contar

Escolha uma ou duas. Elas mostram método, não resultado.

### A armadilha que não gera erro nenhum

O campo `Data_Inicio` do registro da CVM **não é a data de início do fundo**. É a data de
adaptação à Resolução 175. O CNPJ `00068305000135` diz 2025-05-12; o fundo foi constituído em
**1994**. Pelo campo errado, 66% do universo pareceria ter menos de um ano. Pela data certa, a
idade mediana é 7,4 anos.

Um filtro inocente de "fundos com mais de um ano" jogaria fora dois terços do universo,
incluindo fundos de trinta anos. **E o programa rodaria sem erro nenhum.**

### O guardrail que falhou, e o mesmo guardrail que acertou

Criei uma verificação que compara o funil de elegibilidade contra números medidos de antemão.
Ela **não pegou** um erro de 2% causado por chaves repetidas no registro da CVM, 89.749 linhas
para 88.617 ids, porque 2% cabia na tolerância de 3%.

Verificação por percentual não substitui invariante exata. Adicionei a regra dura: junção que
muda a contagem de linhas levanta erro, independente de tolerância.

Duas fases depois, **o mesmo guardrail parou a execução três vezes** e estava certo nas três.

### A simulação que não estava ligada

O primeiro ranking real saiu com **100% de aparição em quase todos os fundos**. Isso não é
resultado forte, é sintoma: significa que nada estava variando. A reamostragem em blocos existia,
tinha teste, e **nunca era chamada**.

Publicar aquele 100% teria sido exatamente a falsa precisão que o módulo existe para evitar.

E há uma segunda camada na mesma história, que é a melhor parte dela. Uma reamostragem pode
dar a todos os fundos o mesmo calendário sorteado, o que preserva o comovimento do mercado e
**soa** conservador. É o contrário: move a seção transversal inteira junta, deixa a ordem
relativa quase intacta, e devolve sobrevivência perto de 100% de novo, agora com a simulação
ligada. Cada fundo sorteia os próprios blocos, e o benchmark é reamostrado junto com ele, para
que excesso seja diferença entre duas séries compostas sobre os mesmos dias. Depois disso as
taxas ocupam a faixa de **31% a 99%** (D-043).

O ranking não ficou menos confiável. Ele parou de afirmar uma confiança que não tinha.

### A carteira que aparece cinco vezes com cinco nomes

Uma gestora roda uma carteira e a vende por várias classes de distribuição. A Caixa tem
**doze** sobre uma só. CNPJs diferentes, nomes diferentes, notas quase iguais, e um Top 5 sem
tratamento entrega quatro exposições dizendo que entrega cinco.

O detalhe que vale contar: **correlação não resolve isso**. Todo fundo pós-fixado segue a mesma
curva de um dia e correlaciona acima de 0,99 com todos os outros; mesmo a 0,999 a correlação
marca 161 fundos como duplicata de alguma coisa. A pergunta certa não é *estes dois se movem
junto* e sim *quanto estes dois discordam*. Dois invólucros de uma carteira diferem só pela
taxa, que é arrasto constante e não gera variância. Mesma gestora e diferença abaixo de 0,10%
ao ano (D-040).

---

## 6. A coisa mais honesta da entrega

Publiquei uma segunda coluna que responde: *este fundo continuaria no top 5 se fosse pontuado
só por desempenho, ignorando taxa e prazo?*

| Fundo | Aparição total | Só desempenho |
|---|---:|---:|
| BNP Paribas Match (3º da liquidez) | 50% | **49%** |
| BB RF Longo Prazo Corporate (3º do prazo) | 77% | **19%** |
| Itaú Empresa Trust (5º da liquidez) | 42% | **6%** |
| BTG Pactual CDB I (1º da liquidez) | 61% | **5%** |
| Sicredi Liquidez Empresarial (1º do prazo) | 97% | **0%** |

Para quase todos, a resposta é **não**. Isso não é defeito. É o peso da taxa funcionando como
projetado. Mas leva a uma frase que precisa estar na entrega:

> Esta é, em grande parte, uma lista de **custo e liquidez**. Os cinco fundos não seriam os
> mesmos se o critério fosse desempenho passado.

Um fundo é a exceção, e vale apontá-la: o **BNP Paribas Match** aparece em 50% das simulações
e em **49%** quando a taxa e o prazo são ignorados. Ele é o único da lista que se sustenta
igualmente pelos dois caminhos. Todos os outros caem para 20% ou menos, e é honesto dizer isso
em vez de procurar o menos ruim.

---

## 7. Roteiro do vídeo, em 5 minutos

O enunciado pede três coisas no vídeo: o desenho, **a decisão de que menos tenho certeza**, e o
caminho para produção. As três estão marcadas abaixo com ★. Se o tempo apertar, corte o resto.

Cinco minutos em português são cerca de **740 palavras faladas**, a 150 por minuto. O roteiro
abaixo tem 732 e fecha em **4:53**. Escrever mais é o erro mais comum, e ele aparece como
pressa na gravação. Os tempos de cada bloco saem da contagem de palavras dele, não de
estimativa.

---

### 0:00 a 0:29 · O problema ★

**Mostrar:** `saida/relatorio_qualidade.md`

> "Existem 36.594 classes de fundos registradas na CVM. A pergunta é quais cinco um cliente de
> varejo deveria comprar. Meu funil derruba isso para 514 fundos que a pessoa de fato consegue
> comprar e cujo custo eu consigo verificar, e cada etapa dele é conferida contra um número que
> eu medi antes de escrever o pipeline. Se algum passo sair mais de 3% do esperado, o programa
> para em vez de publicar."

---

### 0:29 a 0:58 · Fui olhar o dado antes de escrever código

**Mostrar:** D-003 no diário de decisões

> "Antes de codar, passei um dia só olhando os arquivos. Uma armadilha vale contar: o campo
> `Data_Inicio` do registro da CVM não é a data de início do fundo, é a data em que ele se
> adaptou à Resolução 175. Acreditando nele, 66% do universo parece ter menos de um ano, quando
> a idade mediana real é sete. Esse erro não gera exceção nenhuma. Devolve um ranking errado com
> cara de certo."

---

### 0:58 a 1:48 · Como o ranking é calculado ★

**Mostrar:** a tabela do BTG Pactual CDB I (abaixo), ou `configs/profiles.yaml`

> "O ranking é uma soma ponderada de percentis. Não somo taxa com retorno, porque são unidades
> diferentes. Converto cada número na posição relativa do fundo dentro da categoria ANBIMA dele,
> e só então aplico os pesos.
>
> Aqui está o primeiro colocado. Ele está no percentil 97 de custo, e isso sozinho traz 26 dos
> 75 pontos da nota. A pior linha dele é pior queda, percentil 31.
>
> E o Top 5 não são os cinco de maior nota. Eu reconstruo o ranking mil vezes, reamostrando as
> séries de retorno e sorteando os pesos dentro de uma faixa. Publico os cinco que mais
> sobreviveram. Um fundo que só é primeiro na conta exata, e some quando você sacode os dados,
> não é uma boa recomendação."

| Critério | Percentil | Peso | Contribuição |
|---|---:|---:|---:|
| Taxa de administração | 0,971 | 27 | 26,2 |
| Oscilação | 0,824 | 22 | 18,1 |
| Tamanho e estabilidade | 0,941 | 17 | 16,0 |
| Ganho sobre o CDI | 0,559 | 17 | 9,5 |
| Pior queda | 0,309 | 17 | 5,3 |
| **Nota** | | **100** | **75,1** |

---

### 1:48 a 2:37 · A taxa não é lida, é medida

**Mostrar:** `docs/04-investigacao-taxa.md`, a tabela de três anos

> "Custo é o maior peso, então é o número que menos posso errar. Comparei minha lista com as que
> o mercado publica e a taxa de dois fundos meus divergia por dez vezes.
>
> A CVM não está errada, e minha leitura também não. Depois da Resolução 175, algumas casas
> passaram a declarar no extrato uma taxa de camada, não o preço do cliente. A mesma classe
> declarava 0,90% em 2024 e declara 0,040% hoje. No arquivo, 235 foram parar em exatamente
> 0,040%, algumas vindas de 2,60%.
>
> Então parei de ler a taxa e passei a medi-la na cota. O fundo que era o número dois das minhas
> listas declarava 0,040% e cobra 1,81%. Ele saiu."

---

### 2:37 a 3:17 · Funciona?

**Mostrar:** `saida/validacao.md`

> "Testei fora da amostra. Reconstruí o ranking em três datas de 2025 usando nada publicado
> depois de cada uma, e medi o que os escolhidos fizeram até dezembro contra mil carteiras de
> cinco fundos sorteados do mesmo universo. O critério estava commitado antes de eu rodar.
>
> Passou nas seis medições. E digo o resto da tabela antes que me perguntem: a vantagem sobre a
> mediana é de 8 a 22 pontos-base, que é pouco, e o Top 5 ficou **abaixo do CDI nos seis
> recortes**. Percentil 95 numa distribuição estreita significa ganhar de quase todo mundo por
> muito pouco."

---

### 3:17 a 3:59 · A decisão de que menos tenho certeza ★

**Mostrar:** o bloco `weights` em `configs/profiles.yaml`

> "São os pesos. Não tenho demonstração de que sejam os melhores, e o dado até me contraria em
> parte: medi a dispersão, e o ganho sobre o CDI espalha mais que a taxa, 2,75 pontos contra
> 1,60. O que sustenta o peso da taxa não é ela distinguir mais, é a distinção dela persistir.
>
> O que eu garanto não é que os pesos estejam certos. É que estão num arquivo de configuração,
> que os aplicados saem publicados ao lado dos declarados, e que a simulação os sorteia mil
> vezes, de modo que fundo que só vence com um conjunto exato de pesos não chega à lista."

---

### 3:59 a 4:22 · O que o projeto não vê

**Mostrar:** a seção "What this does not do" do README

> "A maior limitação: não olho o que os fundos têm dentro. Meço resultado, não carteira. Dois
> fundos com o mesmo retorno e a mesma oscilação são gêmeos para mim, mesmo que um tenha título
> público e o outro dívida de uma empresa em dificuldade. A CVM publica esse dado, e lê-lo é o
> primeiro item do trabalho futuro."

---

### 4:22 a 4:56 · Caminho para produção ★

**Mostrar:** o commit `76102a4`, autor `github-actions[bot]`

> "O caminho para produção não é promessa, é um commit. Este foi escrito por um robô: o GitHub
> ligou uma máquina limpa, baixou a CVM ao vivo, rodou o pipeline e publicou, sem ninguém
> olhando. O agendamento está comentado enquanto vocês avaliam, para o entregável não ser
> sobrescrito.
>
> Para virar rotina faltariam quatro coisas pequenas: data móvel, guarda de frescor do dado,
> saída versionada fora do git, e commit que diga o que mudou. O pipeline não muda: já é uma
> função que recebe uma data."

---

### Como gravar

Grave em blocos, um por seção, e junte depois. Errar aos 4:30 e ter que refazer cinco minutos é
o que faz a quinta tentativa sair pior que a segunda.

As três seções marcadas com ★ são obrigatórias pelo enunciado. Se estourar o tempo, o corte é
por esta ordem: 0:29 (a armadilha), depois 3:59 (o que não vê), depois 2:37 (funciona).

### Frases prontas

- *"Só 40% dos fundos de renda fixa bateram o CDI em 2025. É por isso que a taxa pesa mais que
  a rentabilidade passada no meu ranking, e isso não é teoria, é o dado."*
- *"Parei de ler a taxa no formulário e passei a medi-la na cota. O erro chegava a 45 vezes."*
- *"Doze meses são 252 dias úteis. Se o meu número não bater com o que o fundo publica, o
  errado sou eu."*
- *"Correlação não identifica fundo repetido em renda fixa: todo pós-fixado correlaciona acima
  de 0,99 com todo pós-fixado. A pergunta certa é quanto os dois discordam."*
- *"O Top 5 ficou abaixo do CDI nos seis recortes. Está na tabela porque é a comparação que o
  cliente faz de cabeça, e esconder isso seria o mesmo que não ter testado."*
- *"Criei um guardrail para pegar junção quebrada. Ele não pegou a minha, porque 2% cabia na
  tolerância de 3%."*
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
5. **Escolher os cinco como carteira**, não individualmente. Hoje a regra garante que nenhum
   dos cinco é a mesma carteira que outro, o que é bem menos que otimizar a combinação deles.
6. **Validar em regime de juros diferente**, o que exige estender a janela para trás e lidar com
   os três layouts do informe diário.
