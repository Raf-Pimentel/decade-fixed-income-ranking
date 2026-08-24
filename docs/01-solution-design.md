# Fase 1: desenho da solução

**Projeto:** Ranking de fundos de renda fixa brasileiros
**Data de referência:** 31/12/2025
**Prazo:** 28/08/2026, 20h

---

## 1. O problema

Existem milhares de fundos de renda fixa registrados no Brasil. A pergunta é: **quais são os cinco melhores para um cliente?**

"Melhor" não tem uma resposta única. Depende de quanto o cliente pode investir, de quando ele vai precisar do dinheiro de volta, e de quanto risco ele aguenta. Então o trabalho tem duas partes: **medir** os fundos de forma correta, e **decidir** o que "melhor" significa, deixando essa decisão explícita e fácil de mudar.

---

## 2. A ideia, em um parágrafo

Eu pego todos os fundos de renda fixa que um cliente comum consegue de fato comprar. Para cada um, calculo dez métricas a partir do valor da cota de 2025: quanto rendeu, quanto oscilou, quanto caiu no pior momento, quanto cobra de taxa, em quantos dias devolve o dinheiro, qual o tamanho do fundo, etc. Comparo cada fundo **apenas com fundos parecidos com ele**, de modo que um fundo que só compra título público não disputa com um que compra dívida de empresa. Somo esses números com pesos que dependem do perfil do cliente. Aí, antes de publicar, **testo se o resultado se sustenta**: refaço a conta mil vezes mexendo levemente nos dados e nos pesos, e só recomendo os fundos que continuam aparecendo no topo. O resultado final não é "o fundo nº 1". É **"estes cinco são consistentemente bons, e a ordem entre eles não significa muita coisa"**.

---

## 3. Quais fundos entram na disputa

Parti de todas as classes registradas na CVM e fui cortando. Todos os números abaixo foram **medidos nos arquivos reais**, não estimados:

| Corte | Sobram | Por que corto |
|---|---:|---|
| Todas as classes registradas na CVM | 36.594 | ponto de partida |
| Só renda fixa | 7.759 | é o escopo do case |
| Em funcionamento normal | 7.337 | fundo cancelado ou liquidado não serve |
| Condomínio aberto | 6.580 | fundo fechado não aceita aplicação nova |
| Não exclusivo | 3.498 | fundo exclusivo é de um único dono |
| Tem série de cota | 3.270 | sem cota não dá para medir nada |
| Pelo menos 200 dias de série no ano | 2.924 | 44 dias não permitem medir risco |
| Patrimônio ≥ R$ 10 milhões | 2.690 | fundo minúsculo não é recomendável |
| **Pelo menos 500 cotistas** | **787** | **ver abaixo** |
| Tem taxa e prazo de resgate **verificáveis** | **514** | não se recomenda o que não se consegue precificar |

**Universo final: 514 fundos.** Destes, 496 são acessíveis ao varejo, 17 restritos a
qualificado e 1 a profissional.

Dois desses cortes merecem explicação.

**Taxa e prazo verificáveis.** Não recomendo um fundo se não consigo dizer ao cliente quanto
ele custa e em quantos dias o dinheiro volta. Não é conveniência de dados, é o mínimo de uma
recomendação responsável. A lacuna que isso revela não é aleatória: fundos de varejo são
obrigados por lei a publicar lâmina, os restritos a qualificado não. É desenho da regulação.

A palavra é **verificáveis** e não publicadas, porque publicar não basta. Para classes que
investem através de outros fundos, o valor publicado no extrato não é o preço que o cliente
paga, e o projeto mede a taxa em vez de lê-la. Uma classe desse tipo cuja taxa não se consegue
medir conta como não tendo divulgado nada, e é aqui que ela sai. Ver a seção 7.1 e a D-047.

**Quinhentos cotistas.** O corte começou em 10, e o primeiro ranking que fiz trouxe fundos com
17, 31 e 70 cotistas e dezenas de bilhões de patrimônio. veículos institucionais rotulados
"Público Geral". Medindo o universo de varejo: o percentil 10 tem **31 cotistas** e a mediana
**924**. Um corte em 10 não excluía nada. Ver D-034.

---

## 4. De onde vêm os dados

Tudo é público e baixável sem cadastro. Três fontes:

| Fonte | O que traz | Formato |
|---|---|---|
| **CVM, Informe Diário** | Valor da cota, patrimônio, nº de cotistas, aplicações e resgates de cada dia | 1 arquivo ZIP por mês |
| **CVM, Registro de Fundos e Classes** | Nome, gestor, classificação, público-alvo, se é aberto/exclusivo | 1 arquivo ZIP (foto do momento) |
| **CVM, Extrato e Lâmina** | Taxa de administração, taxa de performance, prazo de resgate, aplicação mínima | Extrato: 1 por ano · Lâmina: 1 por mês |
| **Banco Central, série 12** | Taxa CDI de cada dia | API JSON |
| **ANBIMA, classificação** | O grupo de comparação de cada fundo, que é dentro do que todo percentil é calculado | Chega dentro do registro da CVM |

Volume total para rodar o projeto: **cerca de 15 arquivos, ~200 MB**.

### O benchmark é o CDI, para todos os grupos, e a saída diz isso

O livro-texto manda escolher o benchmark por grupo: CDI para pós-fixado, IMA-B para indexado à
inflação, IRF-M para prefixado. Comparar um fundo de IMA-B contra o CDI num ano de juros altos
faz ele parecer péssimo quando está apenas fazendo o que promete.

**O dado não permite.** A ANBIMA publica o IMA como **foto do dia corrente**, não como série
histórica: o arquivo principal é Excel binário e a alternativa em texto traz o valor de hoje.
Uma janela que termina numa data passada não se reconstrói a partir disso.

Medi o custo antes de aceitá-lo: **91,8% do universo de varejo é corretamente servido pelo CDI,
8,2% precisaria de IMA-B, e prefixado puro é zero.** E a comparação intra-grupo absorve a maior
parte do resto: um benchmark deslocado move todos os 8,2% juntos, e a ordem por excesso dentro
do grupo não muda. **O que ela não absorve** é o retorno por unidade de risco, que divide esse
excesso deslocado por volatilidades diferentes; ali a ordem muda. Então o efeito não é nulo:
é limitado a 8,2% do universo e a uma das duas métricas de desempenho. Ver D-030.

Por isso `benchmark_by_group` sai preenchido grupo a grupo no `ranking.json`, nomeando CDI em
cada um. Um campo vazio seria pior que um campo ausente, porque leria como se a pergunta tivesse sido
feita e voltado sem resposta.

**O que a ANBIMA fornece, e é o que mais importa aqui, é a classificação** que define os grupos
de comparação. Ela chega dentro do registro da CVM, sem depender da API autenticada, e é dentro
dela que cada percentil é calculado.

---

## 5. As etapas do projeto

Seis etapas. Cada uma é uma pasta de código, recebe uma coisa e devolve outra. Nenhuma depende de como a anterior foi escrita por dentro, só do formato do que ela devolve.

### Etapa 1: baixar

| | |
|---|---|
| **Entrada** | Data de referência (`2025-12-31`) e quantos meses de histórico |
| **Saída** | Arquivos originais salvos em `dados/brutos/`, mais um `manifesto.json` com o nome, o tamanho e a impressão digital (hash) de cada arquivo |
| **O que faz** | Baixa os arquivos da CVM, do Banco Central e da ANBIMA. Se a conexão falhar, tenta de novo 3 vezes com espera crescente. Se o arquivo já existe e a impressão digital bate, não baixa de novo |
| **Tolerância a falha** | Três camadas: **repetição** (3 tentativas com espera crescente), **disjuntor** (após 5 falhas seguidas no mesmo servidor, para de insistir e falha com mensagem clara em vez de travar), e **verificação de conteúdo** (a CVM devolve página de erro com status 200, então confiro se o arquivo é mesmo um ZIP antes de aceitar) |
| **Por que o manifesto** | A CVM **sobrescreve os arquivos** quando corrige um dado, sem avisar e sem manter versão. O manifesto é a única forma de eu saber, daqui a três meses, com qual versão do dado o ranking foi feito |
| **Cache de leitura** | Cada arquivo mensal é lido uma vez e guardado como Parquet sob um nome que carrega o SHA-256 do arquivo de origem. Ler é a metade cara da execução: 280 MB de texto latin-1 separado por ponto e vírgula custam mais que o download depois que os arquivos estão em disco. **A chave é o hash, não o nome**: arquivo retificado tem hash diferente, erra o cache e é lido de novo. Cache por nome de arquivo serviria número velho para sempre, sem avisar |

### Etapa 2: conferir

| | |
|---|---|
| **Entrada** | Arquivos brutos |
| **Saída** | Tabelas limpas em `dados/limpos/` + um relatório do que foi descartado e por quê |
| **O que faz** | Uma lista de checagens, cada uma sendo uma função com seu próprio teste |

Checagens:

| Checagem | O que faço quando falha |
|---|---|
| CNPJ tem 14 dígitos e dígito verificador válido | descarto a linha |
| Valor da cota é positivo | descarto a linha |
| Data não é do futuro em relação à data de referência | descarto a linha |
| Não há duas linhas para o mesmo fundo no mesmo dia | fico com a última |
| Cota não repetiu o mesmo valor por mais de 10 dias úteis | marco o fundo como parado e tiro da disputa |
| Variação diária acima de 20% | **marco, mas não descarto**, porque pode ser amortização legítima |
| Fundo tem pelo menos 200 dias de cota no período | tiro da disputa |

**Regra de freio:** se mais de 5% das linhas de um arquivo forem descartadas, o programa **para com erro**. Prefiro não entregar ranking a entregar um ranking torto sem ninguém perceber.

**E nada é descartado em silêncio:** toda linha rejeitada vai para quarentena **com o motivo escrito**. Filtro que não se consegue inspecionar é indistinguível de bug.

### Etapa 3: juntar

| | |
|---|---|
| **Entrada** | Tabelas limpas |
| **Saída** | Uma tabela única: uma linha por fundo por dia, com os dados de cadastro e taxa colados ao lado |
| **O que faz** | Liga a série de cotas ao cadastro do fundo, à taxa e ao prazo de resgate, e ao CDI do dia |

Aqui mora a parte mais difícil do projeto, explicada na seção 10.

### Etapa 4: calcular

| | |
|---|---|
| **Entrada** | Tabela única |
| **Saída** | Uma linha por fundo, com os dez números da seção 6 |
| **O que faz** | Calcula rentabilidade, risco, custo e liquidez de cada fundo |

Cada fórmula é uma função pequena com teste próprio. Exemplos de teste: uma série de cota constante tem que dar rentabilidade zero; uma série que dobra tem que dar 100%; a rentabilidade acumulada calculada dia a dia tem que bater com a calculada ponta a ponta.

### Etapa 5: ranquear

| | |
|---|---|
| **Entrada** | Números por fundo + arquivo de pesos por perfil |
| **Saída** | Uma lista ordenada por perfil, com nota e com o **grau de confiança** de cada posição |
| **O que faz** | Converte cada número em posição relativa dentro do grupo de fundos parecidos, aplica os pesos, e depois testa se o resultado aguenta (seção 8) |

### Etapa 6: publicar

| | |
|---|---|
| **Entrada** | Listas ranqueadas |
| **Saída** | `ranking.json` (para outro sistema consumir) e `ranking.md` (para uma pessoa ler) |
| **O que faz** | Escreve os dois arquivos, com todos os números que justificam cada escolha |

### Como se roda

```bash
uv run ranking --reference-date 2025-12-31
```

Um comando. Mesmo comando, mesma data, mesmo resultado. Acrescentar `--validate` roda também o teste fora da amostra e escreve `validacao.md`. Leva minutos em vez de segundos, porque roda o pipeline quatro vezes.

A linha de comando é casca fina. O programa inteiro é uma função, e outro time a importa sem precisar de shell:

```python
from ranking.pipeline import run

resultado = run(reference_date=date(2025, 12, 31))
resultado.payload.profiles[0].top[0].name
```

---

## 5.1 Como garanto a qualidade dos dados

Três camadas. Nenhuma delas é uma ferramenta pesada. São três perguntas diferentes.

### Camada 1: o dado tem a forma certa? (contrato)

Cada tabela tem um **schema declarado em um arquivo**, não checagens espalhadas pelo código. O schema diz o tipo de cada coluna, se aceita vazio, a faixa de valores e o que é chave única.

```python
InformeDiario = Schema(
    cnpj_classe=Coluna(str, regex=r"^\d{14}$"),
    data=Coluna(date, menor_igual="data_ref"),
    valor_cota=Coluna(float, maior_que=0),
    patrimonio=Coluna(float, maior_igual=0),
    cotistas=Coluna(int, maior_igual=0),
    chave_unica=["cnpj_classe", "data"],
)
```

O dado passa por isso **na entrada de cada etapa**. Se não bater, não passa. A vantagem de ser declarativo: o schema é legível por quem não escreveu o código, e serve de documentação viva do que o pipeline espera.

### Camada 2: o dado faz sentido? (regras de negócio)

Coisas que o schema não pega, porque dependem de conhecer o mercado. Cada regra é uma função com nome e teste próprio:

| Regra | O que faz |
|---|---|
| `cota_nao_esta_parada` | mesma cota por 10 dias úteis ⇒ fundo saiu da disputa |
| `serie_tem_densidade_minima` | menos de 200 dias no período ⇒ fora |
| `variacao_diaria_plausivel` | acima de 20% ⇒ **marca, não descarta** (pode ser amortização) |
| `cnpj_tem_digito_valido` | valida o dígito verificador, não só o formato |
| `idade_vem_da_fonte_certa` | bloqueia uso de `Data_Inicio` como idade |

Linha rejeitada não some: vai para um arquivo de quarentena **com o motivo**. Assim eu consigo olhar o que foi descartado em vez de confiar que estava tudo bem.

### Camada 3: o resultado bate com o que eu já sei? (regressão de dados)

Esta é a camada que mais me protege, e é de graça.

Na Fase 1 eu medi o funil de elegibilidade nos arquivos reais: 36.598 classes → 7.759 renda fixa → ... → 1.801 → 1.003. **Esses números viram o baseline esperado.**

Toda execução imprime `saida/relatorio_qualidade.md` com o funil e a comparação:

```
Classes no registro     36.598   esperado 36.598   OK
Renda fixa               7.759   esperado  7.759   OK
...
Com taxa e prazo           412   esperado  1.003   FALHA (-59%)
```

Se um número desviar mais que a tolerância, **o pipeline para**. É o teste de fumaça mais barato e mais eficaz que existe aqui: pega join quebrado, filtro invertido, arquivo truncado, mudança de layout na fonte. Um erro de join que reduz o universo pela metade seria invisível numa inspeção de código, mas grita nesse relatório.

**Freio geral:** se mais de 5% das linhas de um arquivo caírem em quarentena, o programa falha. Prefiro não entregar ranking a entregar um ranking torto sem ninguém perceber.

---

## 5.2 Como desenvolvo: teste antes do código

O ciclo é sempre o mesmo, e não pulo etapa:

**vermelho** (escrevo o teste, vejo falhar) → **verde** (escrevo o mínimo para passar) → **refatoro** (limpo com a suíte verde) → **borda** (adiciono o caso chato).

Se um teste passa de primeira, ele está errado, porque não testa o que eu acho que testa.

### Os cinco tipos de teste, e por que cada um existe

| Tipo | Exemplo concreto | Que erro pega |
|---|---|---|
| **Invariante financeira** | cota constante ⇒ retorno 0 · cota que dobra ⇒ 100% · composição dia a dia = ponta a ponta · pior queda nunca é positiva | Fórmula errada. É o erro mais caro e o mais silencioso |
| **Contrato** | schema rejeita CNPJ com 13 dígitos, cota negativa, data futura | Dado ruim entrando |
| **Armadilha** | `Data_Inicio` do CNPJ `00068305000135` é 2025, mas a idade tem que sair 31 anos | Regressão das 13 armadilhas conhecidas |
| **Ponta a ponta** | pipeline roda em fixture de 20 fundos × 60 dias e gera JSON válido | Peças que funcionam sozinhas e quebram juntas |
| **Produto** | abre o `ranking.json` entregue: a janela tem a duração que o rótulo promete · nenhuma lista repete uma carteira · os pesos aplicados somam 100 · nenhum campo do contrato sai vazio | **A maquinaria certa produzindo resposta errada** |

Mais um: **arquivo dourado**. Congelo o `ranking.json` de uma fixture. Se ele mudar sem eu ter mexido de propósito, algo aconteceu.

**Por que o quinto tipo existe.** Os quatro primeiros olham para dentro e pegam função errada. Nenhum deles pega uma janela de treze meses rotulada como doze, uma lista com a mesma carteira em duas posições, um peso que empata para todo fundo do universo, ou um campo de contrato publicado vazio. Nada disso quebra função nenhuma, e tudo isso atravessa uma suíte verde. A regra que fica: **todo campo publicado precisa de um teste que falharia se ele saísse vazio, com o rótulo errado, ou repetido.**

### Fixtures

Recortes **reais e pequenos** da CVM, com 20 fundos e 60 dias, congelados no repositório. Nenhum teste baixa da internet: teste que depende de rede não é teste, é aposta.

### O que eu não testo

Não busco 100% de cobertura. Meta de 90% **só nos módulos de cálculo**, que é onde erro custa caro. Código de leitura de arquivo e de formatação de saída fica coberto pelo teste ponta a ponta, e está bom.

---

## 6. Os dez números

Todos saem do **valor da cota**, que é o dado mais confiável da CVM e que **já vem descontado das taxas de administração e de performance**. Ou seja: é o retorno que o cotista de fato embolsou.

| Número | O que significa | Como se calcula |
|---|---|---|
| **Rentabilidade** | Quanto rendeu no período | cota final ÷ cota inicial − 1 |
| **Ganho sobre o CDI** | Quanto rendeu além da taxa básica | rentabilidade − CDI acumulado |
| **Oscilação** | O quanto o valor balança no dia a dia | desvio-padrão dos retornos diários, anualizado |
| **Retorno por unidade de risco** | Ganho sobre o CDI dividido pela oscilação | quanto mais alto, melhor o negócio |
| **Pior queda** | A maior perda do topo até o fundo no período | dói mais no cliente do que a oscilação média |
| **Dias no vermelho** | % dos dias em que o fundo perdeu | fundo de crédito costuma ter poucos, até o dia em que tem muitos |
| **Taxa de administração** | Custo anual | do Extrato ou da Lâmina |
| **Prazo de resgate** | Dias entre pedir e receber | soma de conversão e pagamento |
| **Tamanho** | Patrimônio e número de cotistas | fundo grande e com muitos cotistas é mais estável |
| **Estabilidade do dinheiro** | Se o fundo está apanhando resgate | (aplicações − resgates) ÷ patrimônio |

### Por que 12 meses e não 3 anos

Medi a disponibilidade real de histórico dos 1.801 fundos:

| Janela | Fundos com série completa | % |
|---|---:|---:|
| 6 meses | 1.749 | 97% |
| **12 meses** | **1.675** | **93%** |
| 24 meses | 1.481 | 82% |
| 36 meses | 1.326 | 74% |
| 60 meses | 1.094 | 61% |

Cada ano a mais de histórico custa cerca de 10% do universo. Além disso, 2021–2023 teve a Selic indo de 2% a 13,75%, um mundo diferente do de 2025. Esticar a janela mistura dois regimes e ainda enche a amostra de fundos velhos e grandes que sobreviveram, o que enviesa o resultado.

**Uso 12 meses para pontuar** e reporto 3, 6 e 24 meses junto, para quem quiser discordar do meu critério com os números na mão. A janela é um parâmetro de configuração.

**E doze meses são doze meses.** A janela é fechada nas duas pontas e contada a partir da própria data de referência: 31/12/2025 menos doze meses começa em **01/01/2025** e contém **252 dias úteis**, contra os 14,3242% que o CDI fez no ano-calendário. Começar no primeiro dia do mês doze meses atrás daria 01/12/2024, treze meses, 273 dias e um CDI de 15,39%, sem quebrar nada, porque fundo e benchmark continuariam compostos sobre a mesma janela e o excesso continuaria coerente. O que sairia errado é só o que o leitor consegue conferir: um retorno que não bate com o que o próprio fundo publica. Por isso o `ranking.json` publica `window_start` como data, e não só a contagem de meses: contagem de mês ninguém confere, duas datas qualquer um confere.

---

## 7. Dois perfis de cliente

Não inventei personas. O corte é **quando o cliente precisa do dinheiro de volta**, e sai do próprio dado: 58% do universo de varejo devolve o dinheiro no mesmo dia, então uma lista única entregaria os mesmos cinco fundos para quem está guardando dinheiro para uma viagem e para quem está guardando para três anos.

O enunciado sugere varejo contra investidor qualificado como exemplo de segmentação, e eu comecei por aí. **O dado não sustentou.** Dos fundos restritos a qualificado, apenas 79 publicam taxa e prazo de resgate, ou 28%, contra 64% no varejo. A lacuna não é aleatória: a obrigação de publicar lâmina alcança fundos de varejo e não os restritos. Ranquear sobre essa amostra produziria uma lista enviesada pela regulação e não pela qualidade, e o universo qualificado elegível cai para 19 fundos, o que é pouco para um Top 5 significar alguma coisa. Ver D-031 e D-032.

Os dois perfis publicados são, então, dois recortes do varejo:

| | **Reserva de emergência** | **Dois anos ou mais** |
|---|---|---|
| Público-alvo | Público Geral | Público Geral |
| Aplicação mínima aceita | até R$ 5 mil | até R$ 50 mil |
| Prazo de resgate aceito | até D+1 | até D+30 |
| Fundos elegíveis em 31/12/2025 | 195 | 348 |
| O que importa mais | não pagar caro e conseguir sacar | não pagar caro e ganhar do CDI de forma consistente |

Os universos se sobrepõem de propósito. Quem tem horizonte longo pode perfeitamente comprar um fundo D+0, porque liquidez sobrando não é defeito, e por isso o perfil de prazo é o mais largo dos dois. O mesmo fundo aparecendo nas duas listas é a resposta certa, e não uma duplicação.

### Pesos

| Número | Reserva de emergência | Dois anos ou mais |
|---|---:|---:|
| Taxa de administração | **25** | **23** |
| Oscilação | 20 | |
| Ganho sobre o CDI | 15 | 22 |
| Retorno por unidade de risco | | 20 |
| Pior queda | 15 | 15 |
| Tamanho e estabilidade | 15 | 15 |
| Prazo de resgate | 10 | 5 |
| **Total** | **100** | **100** |

A taxa é o maior peso individual nos dois perfis, e por pouco no de prazo. Custo é o único
número que se sabe com certeza sobre o ano que vem, mas ele não é o que mais separa os fundos:
medido no universo elegível, o excesso sobre o CDI vai de −2,46% a +0,29% entre o percentil 10
e o 90, uma amplitude de 2,75 pontos, contra 1,60 ponto da taxa. O que sustenta o peso da taxa
não é a dispersão, é a persistência dela.

Estes são os pesos **declarados**. Os de fato aplicados saem no `ranking.json` ao lado deles, porque um critério em que todo o universo elegível empata tem o peso redistribuído. A seção "Peso só vale para critério que separa", mais abaixo, explica quando isso acontece e por quê.

**Por que a taxa é o maior peso do varejo, e não a rentabilidade.** Essa é a decisão menos óbvia do projeto, então vale a justificativa: em renda fixa, a taxa é o único número que se sabe com certeza sobre o **futuro**. A rentabilidade passada de 12 meses é, em boa parte, CDI, que todo fundo pegou igual, mais um prêmio de risco de crédito que ainda não deu problema. A taxa, ao contrário, vai ser cobrada em 2026 exatamente como foi em 2025. Dar peso maior ao que persiste é mais defensável do que dar peso maior ao que não persiste.

### 7.1 A taxa é medida, não lida

Custo decide mais deste ranking do que qualquer outro número, o que faz dele o número que o
projeto menos pode errar. O extrato da CVM traz uma taxa de administração declarada, e para
uma família inteira de classes esse valor não é o preço que o cliente paga.

Sob a RCVM 175 uma gestora roda uma carteira e a vende por classes alimentadoras, cada uma
entregando o próprio extrato. Algumas casas passaram a declarar ali um valor nominal de
camada. No arquivo, **580 das 2.655 classes presentes em 2024 e 2025 tiveram a taxa declarada
cair três vezes ou mais**, e 235 foram parar em exatamente 0,040%, algumas vindas de 2,60%.
Ninguém corta uma taxa de 2,60% para 0,04%.

Então a taxa é medida. Uma alimentadora aplica quase todo o patrimônio num único fundo, o que
faz das duas séries de cota a mesma carteira precificada duas vezes, e a única coisa que as
separa é o que a classe retém:

    taxa = 1 − (crescimento da classe ÷ crescimento do master) ^ (1 ÷ anos)

O elo entre classe e master vem da composição de carteira da CVM, que é fonte nova no projeto.
Nada mais é necessário, e nada depende de um formulário preenchido corretamente. A definição é
geométrica e não a diferença simples de retornos, porque taxa é cobrada todo dia e compõe:
anualizar a diferença simples daria números diferentes conforme o tamanho da janela.

Contra fonte externa, os dois fundos em que isso mais pesou medem 0,396% e 0,511% aqui, contra
0,37% e 0,42% reportados pela Economática.

Três regras decidem o número, e cada uma custa ao fundo em vez de premiá-lo. Onde os dois
valores existem, vence o **maior**: uma classe não cobra menos do que a gestora declarou para
ela, então medida abaixo da declarada é ruído e não desconto. Classe que investe através de
outros fundos e **não pôde** ser medida fica sem taxa, e sai pela regra que já recusa ranquear
o que não se consegue precificar. Todo o resto mantém o que declarou, porque o problema é de
uma família de classes e não do mercado.

Os dois números são publicados lado a lado, para que o leitor veja a diferença.

### Comparação só entre iguais

Antes de aplicar os pesos, converto cada número na **posição relativa do fundo dentro do seu grupo** (fundos de título público competem com fundos de título público, fundos de crédito com fundos de crédito). Uso a classificação ANBIMA, que já vem dentro do arquivo de registro da CVM.

Sem isso, o ranking viraria automaticamente "os cinco fundos que tomaram mais risco de crédito", porque em 2025 eles renderam mais e o problema deles ainda não apareceu.

### Duas notas, porque percentil é sempre relativo a alguma coisa

Comparar dentro do grupo responde *este fundo é bom para o que ele é?*, que é a pergunta respondível a partir de uma série de cotas. Ela é **silenciosa sobre o grupo**: ser o primeiro de dezoito vale 1 numa categoria forte e numa fraca, e o Top 5 final mistura categorias.

Então todo fundo publica duas notas: a nota contra os pares, que decide o ranking, e a mesma nota recalculada contra **todo o universo elegível do perfil**. Quando as duas se afastam, o fundo é o melhor de uma categoria que não é boa. Na entrega de 31/12/2025 o primeiro colocado do perfil de prazo tira 83,2 no grupo e 66,9 no universo, e quem lê tem direito de saber disso antes de comprar.

Eu **não** invento um termo de qualidade de grupo para "corrigir" a soma. Isso exigiria afirmar que uma categoria vale mais que outra, exatamente o julgamento que a comparação intra-grupo existe para não precisar fazer. Publicar as duas notas devolve o julgamento a quem lê.

### Peso só vale para critério que separa

Elegibilidade e pontuação respondem perguntas diferentes, e um critério pode ser decisivo na primeira e vazio na segunda. O perfil de liquidez filtra para resgate em até um dia e depois dá peso ao prazo de resgate, mas **quase todo fundo que sobra liquida em D+0**. Todos empatam, o percentil sai 0,5 para todo mundo, e o peso não decide nada enquanto os outros critérios valem 11% mais do que a configuração afirma.

Um critério cuja dispersão no universo elegível fica abaixo de um piso declarado é tratado como inerte: o peso vai proporcionalmente para os que ainda distinguem, e a saída nomeia o critério e publica os pesos **de fato aplicados** ao lado dos declarados. É regra sobre a forma do dado, aplicada igual a todo perfil e a toda data. O universo decide qual critério cai, a cada execução, e não eu.

### Cinco fundos, não cinco notas

Uma nota ranqueia fundos um a um. Uma lista de cinco é consumida de uma vez, por alguém que vai carregar os cinco.

Uma gestora brasileira roda uma carteira e a vende por várias classes de distribuição, e a Caixa tem **doze** sobre uma só carteira de renda fixa. Cada uma é classe separada no registro, cada uma é elegível, cada uma tira quase a mesma nota. Um Top 5 com duas delas entrega quatro exposições sem avisar.

Dois fundos contam como um quando **a mesma gestora roda os dois** e a diferença entre suas séries de retorno quase não oscila, com volatilidade anualizada da diferença abaixo de 0,10% ao ano. Correlação não serve aqui e não é usada: todo fundo pós-fixado segue a mesma curva de um dia e correlaciona acima de 0,99 com todos os outros, então qualquer limiar alto o bastante para pegar um gêmeo também marca metade do universo. A pergunta certa não é *estes dois se movem junto*, é *quanto estes dois discordam*: dois invólucros de uma carteira diferem só pela taxa, que é arrasto constante e não gera variância.

O fundo deixado de fora sai publicado ao lado da lista, com nome, o fundo que ele repete e a distância entre os dois.

---

## 8. Como lido com o fato de que o ranking é ruidoso

Esta é a parte que separa uma lista bonita de uma recomendação honesta.

Com 12 meses de dados diários, a incerteza sobre o "retorno por unidade de risco" de um fundo é **grande, da ordem de ±1,5**. Isso significa que a diferença entre o 1º e o 15º colocado, muitas vezes, **não existe de verdade**: é ruído. Publicar "este é o melhor fundo do Brasil" com esse nível de incerteza seria desonesto.

Então faço duas coisas antes de publicar:

**Teste 1: os dados poderiam ter sido diferentes.** Reembaralho a série de retornos de cada fundo em blocos (preservando o comportamento de dias seguidos) e refaço todos os cálculos. Mil vezes.

**Teste 2: meus pesos poderiam ser outros.** Sorteio variações nos pesos, dentro de faixas razoáveis (a taxa do varejo pode valer entre 20 e 30, não entre 0 e 100). Mil vezes.

Depois, para cada fundo, conto: **em quantas das mil simulações ele apareceu entre os cinco primeiros?**

O Top 5 final são os cinco com maior taxa de aparecimento, e não os cinco com maior nota pontual. E cada um sai na entrega com o número junto:

> **1. Fundo X** apareceu no Top 5 em **91%** das simulações
> **2. Fundo Y** apareceu no Top 5 em **88%** das simulações

Um fundo que só é primeiro na conta exata, e some quando eu mexo um pouco nos pesos, **não é uma boa recomendação**, e esse teste revela isso.

Isso também responde à crítica mais óbvia que se pode fazer ao projeto: *"os pesos são arbitrários"*. São. Mas eu mostro o quanto o resultado depende deles.

### Três detalhes da reamostragem que decidem se ela significa alguma coisa

**Cada fundo sorteia os próprios blocos.** A grandeza estimada é idiossincrática: quanto da vantagem *deste* fundo sobre aquele é sorte de amostra. Dar a todos o mesmo calendário reamostrado preserva o comovimento do mercado, o que soa conservador e é o contrário: move a seção transversal inteira junta, deixa a ordem relativa quase intacta e devolve sobrevivência perto de 100% para um ranking que ninguém estressou. O preço é que um ano simulado não contém crash comum. Está declarado, e é o mais barato dos dois erros.

**O benchmark é reamostrado junto com o fundo.** Excesso é diferença entre duas séries compostas, e as duas precisam ser compostas sobre os mesmos dias. Medir um ano reamostrado do fundo contra o CDI do ano-calendário enviesa todo excesso. E como retorno por unidade de risco divide essa diferença pela volatilidade, um viés que se cancelaria num ranking por excesso não se cancela ali: ele reordena, a favor dos fundos mais voláteis.

**Cada fundo mantém o próprio comprimento de histórico.** Truncar o painel no fundo mais curto jogaria fora um quinto da evidência de todo mundo para acomodar o mais novo.

Com os três no lugar, as taxas de aparição ocupam a faixa de 31% a 99%, em vez do aglomerado de 97% a 100% que uma reamostragem de calendário comum produz. O ranking não ficou menos confiável. Ele parou de afirmar uma confiança que não tinha.

---

## 8.1 O teste no passado: o método funciona?

Tudo até aqui diz que o método é **razoável**. Nada até aqui diz que ele **funciona**. Essa é a diferença entre um argumento e uma evidência, e é a pergunta que qualquer pessoa experiente faz primeiro.

Então faço o teste óbvio: **monto o ranking com dados de meio do ano e vejo o que aconteceu depois.**

### Como funciona

Rodo o pipeline inteiro fingindo que hoje é 30 de junho de 2025. Mesmo código, mesma configuração, nenhuma linha nova:

```bash
uv run ranking --reference-date 2025-12-31 --validate
```

Por dentro, isso é o pipeline inteiro rodado quatro vezes: uma por data de corte, mais a final que fornece a régua. Mesmo código, mesma configuração, nenhuma linha nova.

Congelo o Top 5 que sair. Depois meço quanto esses cinco fundos renderam de **julho a dezembro de 2025**, período que o ranking não viu.

Se o point-in-time da Etapa 1 estiver correto, isso é literalmente um comando. **É aqui que a disciplina de "nenhuma linha com data posterior entra no cálculo" para de ser virtude teórica e vira benefício concreto.** Se o teste for difícil de fazer, é sinal de que o point-in-time está furado, e o próprio teste vira uma auditoria da arquitetura.

### Contra o que comparo

| Referência | Pergunta que responde |
|---|---|
| Mediana dos elegíveis | Meu Top 5 bate o fundo típico do mesmo universo? |
| CDI, composto sobre exatamente os dias medidos | Bate o benchmark que o cliente tem na cabeça? |
| **1.000 carteiras de 5 fundos sorteados** ao acaso do universo elegível | **Meu método bate o acaso?** |
| 1.000 carteiras sorteadas do **quartil mais barato** do mesmo universo | Quanto disso é seleção e quanto é a taxa ser menor? |

A terceira é a que decide o critério congelado. É o controle que quase ninguém faz, e é o que separa análise de horóscopo. O número reportado é em que percentil da distribuição de carteiras aleatórias o Top 5 caiu.

**A quarta existe porque a taxa sai da cota antes de qualquer medição.** Como o custo é o maior peso dos dois perfis, parte de qualquer vantagem sobre a mediana é aritmética que se sabia antes de rodar o teste: fundo mais barato entrega mais do mesmo retorno bruto. Sortear só entre os baratos segura isso aproximadamente constante.

E ela não é experimento limpo, o que o relatório diz com essas palavras: segurar o custo também muda a composição do grupo, porque o quartil mais barato é dominado por fundo de título público, que rende bruto menos que crédito. É um segundo ângulo sobre o mesmo resultado, não uma decomposição entre custo e habilidade. Por isso ela é **reportada e não faz parte do critério**, que foi congelado antes de ela existir.

### De onde saem os retornos medidos

Do **painel validado inteiro**, não do universo elegível na data final.

A diferença não é detalhe. Um fundo escolhido em março que encolheu abaixo do corte de cotistas até dezembro continua tendo tido um retorno. Ler o resultado do conjunto sobrevivente o descarta em silêncio da média, e a média passa a ser dividida pelos fundos que deram certo. É o viés de sobrevivência que este projeto critica em três lugares, aplicado ao próprio teste que existe para detectá-lo.

A garantia é uma propriedade testada: **o divisor é sempre o número de fundos que o método escolheu**, nunca o número deles que era mensurável. Um fundo sem cota nenhuma depois do corte entra com o último valor conhecido, conforme a política congelada antes, e sai nomeado no relatório.

### Três datas de corte, não uma

Um único semestre é uma amostra de tamanho 1, e pode ter sido sorte. Como cada rodada é um comando, faço três: **31/03**, **30/06** e **30/09/2025**, cada uma medida contra o que veio depois.

### O critério de sucesso, declarado antes de rodar

> **O método é considerado validado se o Top 5 ficar acima do percentil 60 da distribuição de carteiras aleatórias em pelo menos 2 das 3 datas de corte.**

Declarar o critério **antes** de ver o resultado é o que me impede de racionalizar qualquer número que apareça. Sem isso, o teste não vale nada, porque sempre dá para contar uma história bonita depois do fato.

### Duas regras que valem mais que o resultado

**Regra 1: proibido ajustar os pesos depois de ver o teste.** Se eu mexer nos pesos até o teste passar, eu não validei nada: apenas decorei o segundo semestre de 2025. Isso é a forma mais comum de fraudar a si mesmo em finanças quantitativas, e costuma ser feita sem má intenção.

**Regra 2: se falhar, eu reporto que falhou.** E digo o que mudaria. Um resultado negativo relatado com honestidade vale mais do que um Top 5 sem validação nenhuma: mostra que o método é falseável, que é justamente o que se espera de um método.

### Um detalhe que precisa ser decidido antes

E se um dos cinco fundos parar de publicar cota entre julho e dezembro? Regra fixada **agora**, para não ser escolhida conveniente depois: o fundo é mantido na carteira com o último valor conhecido e **marcado como descontinuado no relatório**. Fingir que ele nunca esteve lá seria exatamente o viés de sobrevivência que eu critico na seção 12.

### O que este teste ainda não prova

Que o método funciona **em 2026**. Ele mostra que funcionou em três recortes de 2025, com um ano só e um regime de juros só. É evidência, não garantia, e vou escrever isso com essas palavras na entrega.

---

## 9. O que o projeto entrega

| Arquivo | Para quem | Conteúdo |
|---|---|---|
| `saida/ranking.md` | Uma pessoa | As duas listas, um parágrafo explicando cada escolha, e o que o método não enxerga |
| `saida/ranking.json` | Outro sistema | O mesmo, com todos os números, percentis, pesos aplicados e o manifesto das fontes |
| `saida/ranking.html` | Uma pessoa, de relance | As mesmas listas como página autocontida |
| `saida/relatorio_qualidade.md` | Quem precisa confiar nos números | O funil de elegibilidade contra o baseline |
| `saida/validacao.md` | Quem precisa confiar no método | O teste fora da amostra |
| `README.md` | Quem for rodar | Como instalar e executar, o que cada etapa faz |
| Código + testes | Quem for manter | Um comando para rodar tudo, funções importáveis |

**`saida/` é versionada.** O enunciado pede o `ranking.md` no repositório, e um arquivo que só passa a existir depois que alguém roda o pipeline não está entregue, além de virar link quebrado no README de quem clona. `dados/` não é versionada: é pesada, reconstruível, e o que a prende a uma execução não é o arquivo e sim o SHA-256 de cada fonte, que já viaja dentro do `ranking.json`.

Formato do `ranking.json`:

```json
{
  "schema_version": "1.1.0",
  "reference_date": "2025-12-31",
  "lookback_months": 12,
  "window_start": "2025-01-01",
  "benchmark_label": "CDI",
  "benchmark_by_group": { "Renda Fixa Duração Baixa Soberano": "CDI" },
  "sources": { "inf_diario_fi_202512.zip": "3f9a..." },
  "profiles": [{
    "profile_id": "varejo_liquidez",
    "label": "Retail: emergency reserve",
    "eligible_universe_size": 195,
    "weights":           { "admin_fee": 25, "volatility": 20, "redemption_days": 10 },
    "effective_weights": { "admin_fee": 33, "volatility": 22 },
    "inert_metrics": ["redemption_days"],
    "manager_share": { "ITAU UNIBANCO ASSET MANAGEMENT LTDA.": 0.2752 },
    "displaced": [{
      "cnpj_classe": "09215250000113",
      "name": "BTG PACTUAL TESOURO SELIC ...",
      "score": 74.8,
      "duplicate_of": "BTG PACTUAL CDB I ...",
      "tracking_difference": 0.000363
    }],
    "top": [{
      "rank": 1,
      "cnpj_classe": "51998694000139",
      "name": "...",
      "manager": "...",
      "peer_group": "Renda Fixa Duração Média Grau de Invest.",
      "score": 86.8,
      "score_pool": 72.0,
      "appearance_rate": 0.99,
      "appearance_rate_variable_only": 0.72,
      "metrics": {
        "retorno": 0.1432, "excesso": -0.00001, "volatilidade": 0.00071,
        "pior_queda": 0.0, "taxa_adm": 0.0004, "dias_resgate": 0,
        "patrimonio_medio": 19152092772.66, "cotistas": 141715,
        "observacoes": 252, "fonte_taxa": "EXTRATO",
        "regime_tributario": "tabela_regressiva"
      },
      "percentiles": { "admin_fee": 0.97, "volatility": 1.0 },
      "rationale": "..."
    }]
  }]
}
```

Sete campos existem porque um número sozinho engana, e vale dizer qual pergunta cada um responde:

| Campo | Pergunta que ele responde |
|---|---|
| `window_start` | A janela tem mesmo a duração que `lookback_months` afirma? Contagem de meses ninguém confere; duas datas qualquer um confere |
| `benchmark_by_group` | Contra o que o excesso deste fundo foi medido? Declarado grupo a grupo, para não sobrar suposição |
| `effective_weights` / `inert_metrics` | Os pesos declarados foram todos usados? Qual critério empatou para o universo inteiro e teve o peso redistribuído? |
| `displaced` | Que fundo o score alcançou e a regra de distinção deixou de fora, por repetir qual carteira, e a que distância? |
| `manager_share` | O universo de onde essa lista saiu já era concentrado? |
| `score_pool` | Esta nota é boa contra os pares, ou também contra tudo que o perfil podia comprar? |
| `appearance_rate_variable_only` | Este fundo continuaria no top 5 se fosse pontuado só por desempenho, ignorando taxa e prazo? |
| `regime_tributario` | A comparação bruta é justa com este fundo? Fundo incentivado de infraestrutura é isento para pessoa física |

O campo `schema_version` existe para que outro time possa depender do arquivo sem medo: acréscimo de campo sobe a versão menor, mudança incompatível sobe a maior.

---

## 10. Armadilhas que encontrei nos dados

Fui aos arquivos antes de desenhar. Três coisas que quebrariam o projeto se eu não tivesse olhado:

**1. O dado não é mais por fundo, é por classe.** A regra CVM 175 reorganizou os fundos em "classes", e desde janeiro de 2024 o informe diário identifica a classe, não o fundo. Quem escrever o código assumindo o formato antigo faz o cruzamento errado e **não recebe nenhum erro**, só um resultado silenciosamente errado.

**2. O arquivo de cadastro que todo mundo usa está obsoleto.** O `cad_fi.csv`, que é o que aparece em qualquer tutorial, cobre apenas **10%** dos fundos de renda fixa de hoje, e **nenhum deles** tem a taxa preenchida. Taxa e prazo de resgate estão em outros dois arquivos (Extrato e Lâmina).

**3. A data de início do fundo não é a data de início do fundo.** O campo `Data_Inicio` do registro é, na verdade, a data em que o fundo se adaptou à regra CVM 175, quase todos em 2024 ou 2025:

| CNPJ | `Data_Inicio` | Data real de constituição |
|---|---|---|
| 00068305000135 | 2025-05-12 | **1994-05-26** |
| 00089915000115 | 2024-10-01 | **1994-06-21** |

Um filtro inocente de "só fundos com mais de um ano" **jogaria fora 66% do universo**, incluindo fundos de trinta anos. A idade verdadeira mediana é de **7,4 anos**. Isso vira um teste automatizado.

---

## 11. Ferramentas

Escolhi o mínimo que resolve. Cada dependência precisa justificar por que existe.

| Ferramenta | Para quê |
|---|---|
| Python 3.12 | linguagem |
| Polars | ler e cruzar as tabelas (rápido e enxuto) |
| Pandera | declarar os schemas das tabelas em um arquivo, em vez de espalhar `if` pelo código |
| Pydantic | garantir que o `ranking.json` sai exatamente no formato prometido |
| httpx + tenacity | baixar com repetição em caso de falha |
| NumPy | contas de risco e as simulações |
| pytest | testes |
| Typer | a linha de comando |
| PyYAML | ler os arquivos de configuração |
| uv | instalar as dependências de forma reprodutível |
| Docker | rodar em máquina limpa |

**O que deliberadamente não usei:** banco de dados, orquestrador de tarefas, Spark, camadas de "data lake". São ~1.000 fundos e ~200 MB de arquivo. O projeto roda em minutos num notebook. Colocar infraestrutura de escala aqui seria complexidade sem benefício, e complexidade que ninguém vai avaliar.

**Como isso viraria produção:** a função `rodar(data_ref)` é o programa inteiro. Para rodar diariamente, basta agendá-la (cron, Airflow, o que o time já usar) e apontar a pasta de saída para um bucket. O código não muda, só onde ele escreve.

---

## 12. Limitações

Em ordem de gravidade, não de conveniência. As três primeiras são as que eu levaria ao vídeo.

**1. Os pesos são arbitrários.** Não existe demonstração de que 30/20/15/15/10/10 seja melhor
que outro conjunto qualquer. A escolha tem argumento, porque a taxa é o único número que se sabe
sobre 2026 e apenas 40% dos fundos bateram o CDI em 2025, mas argumento não é prova.
Encontrar pesos ótimos é um problema quantitativamente difícil que este projeto **não resolve**.
O que ele garante é outra coisa: se os pesos certos existirem e forem informados, o pipeline
produz o ranking correto a partir deles. Os pesos vivem em YAML, a simulação mede o quanto o
resultado depende deles, e trocá-los não exige tocar em uma linha de código.

**2. O método não olha a carteira.** Mede resultado, não conteúdo. Dois fundos com números
idênticos podem carregar riscos de crédito completamente diferentes. Crédito privado no Brasil
paga um spread pequeno e constante por muitos meses e devolve tudo de uma vez quando o emissor
quebra, e nada na série de cotas antecipa isso.

**3. Doze meses não dizem o que acontece em 2026.** A simulação mede a incerteza da amostra,
não o risco de cauda: reamostrar 2025 nunca produzirá uma crise de crédito que 2025 não teve.

**4. Viés de sobrevivência.** Fundos que quebraram em 2025 não estão na base. O universo é,
por construção, otimista.

**5. A volatilidade de fundos de crédito é subestimada.** Dívida privada não é remarcada
diariamente, o que faz esses fundos parecerem mais tranquilos do que são e melhora
artificialmente a nota de quem carrega mais risco.

**6. Parte da estabilidade medida é mecânica.** Taxas e prazos não variam entre simulações,
então um fundo bem ranqueado por custo aparenta mais robustez do que a evidência sustenta.

**7. Fundos indexados à inflação são medidos contra o CDI**, não contra o IMA-B, porque a
ANBIMA publica o IMA como foto do dia e não como série. Afeta 8,2% do universo, e a comparação
intra-grupo absorve o efeito no ranking por excesso mas **não** no retorno por unidade de risco,
que divide o excesso deslocado por volatilidades diferentes.

**8. Ignora imposto de renda, e isso não é neutro para todo mundo.** A comparação é
pré-tributação. Para a maioria dos fundos, que segue a mesma tabela regressiva, a ordem
relativa continua justa. **Fundo incentivado de infraestrutura é isento para pessoa física**,
então o que o cliente leva para casa é maior do que a tabela mostra e a comparação bruta o
subestima. Por isso todo fundo publica `regime_tributario`: a ressalva geral seria falsa se
aplicada sem exceção, e a exceção existe dentro do universo elegível.

**9. A lista mistura categorias e soma percentis calculados dentro delas.** Ser o primeiro de
dezoito vale 1 num grupo forte e num grupo fraco, e o Top 5 junta os dois. Não invento um termo
de qualidade de grupo para corrigir a soma, porque isso exigiria afirmar que uma categoria vale mais
que outra, exatamente o julgamento que a comparação intra-grupo existe para evitar. Publico as
duas notas, `score` e `score_pool`, e o leitor decide.

**10. A taxa é contada duas vezes, de propósito.** A cota já vem líquida, então o excesso
dentro dela **já** pune o fundo caro; dar à taxa o maior peso conta o mesmo custo de novo. É
escolha e não descuido, já que a primeira contagem fala de 2025 e a segunda fala de 2026, mas quem
lê precisa saber que está lá.

**11. Cada fundo é avaliado isoladamente.** A única restrição de carteira é não repetir a mesma
carteira duas vezes: dois invólucros de um portfólio ocupam uma vaga, não duas. Isso é bem menos
que otimizar a combinação dos cinco, e a lista continua concentrando em poucas gestoras pelo
motivo da seção 12.1.

**12. O cadastro é uma foto de hoje.** A CVM não guarda versões antigas do registro.

### 12.1 Sobre a concentração em poucas gestoras

Vale contar esta parte com a ordem em que aconteceu, porque a primeira conclusão estava errada.

Até 24/08, sete das dez posições eram do Itaú, e o projeto explicava isso como aritmética
coerente do critério: a gestora pratica taxas baixas nos fundos de casa e custo é o maior peso.
O número publicado em `manager_share` parecia sustentar a leitura, porque a mesma gestora
responde por cerca de um quarto do universo elegível.

**A explicação estava incompleta.** Aquelas classes declaravam 0,040% e cobravam de 0,40% a
1,81%. Quando a taxa passou a ser medida, o Itaú saiu inteiro da lista de liquidez e das duas
listas sobraram nomes de sete casas diferentes. Boa parte da concentração era artefato de
preenchimento, não retrato de mercado.

O número de `manager_share` continua publicado e continua útil: **essa gestora responde por
26,2% dos 195 fundos do perfil de liquidez e por 19,2% dos 348 do perfil de prazo**, e agora
não aparece em nenhuma das duas listas. O que a história ensina é que um número que explica
um resultado incômodo merece a mesma desconfiança que um número que o contradiz.

## 13. O que fica em aberto

**O corte de cotistas não separa varejo de institucional.** Ele nasceu para tirar fundo com 17
cotistas e dezenas de bilhões, e faz isso. Não pega um fundo com 1.360 cotistas e R$ 23 bi, que
é o mesmo veículo com outro tamanho. A pergunta certa não é quantos cotistas há, é se quem
está lá dentro é varejo, e patrimônio por cotista responde melhor. Não foi implementado porque
a escolha do limite viria depois de eu já saber quais fundos ele removeria, o que a regra 11
proíbe. Ver `docs/05-conferencia-externa.md`.

**Eu ranqueio os fundos pelo resultado, não pelo que eles têm dentro.**

Esta é a lacuna principal do projeto, e é honesto colocá-la na frente. Dois fundos podem ter rentabilidade, oscilação e pior queda praticamente idênticos, e um deles estar cheio de dívida de uma única empresa em dificuldade enquanto o outro só tem título público. **Pelos meus dez números, eles são gêmeos. No risco real, não são.**

É exatamente o risco que mais importa em renda fixa brasileira: crédito privado paga um prêmio pequeno e constante por muitos meses e devolve tudo de uma vez quando o emissor quebra. Meu ranking de 2025 não teria como distinguir, em janeiro de 2023, um fundo com Americanas na carteira de um sem.

**A CVM publica esse dado.** É o arquivo de Composição da Carteira (CDA), mensal, com os ativos de cada fundo. Não coube nos 8 dias porque é um volume muito maior e exige entender a estrutura de tipos de ativo, mas o caminho está aberto: seria uma nova fonte na Etapa 1 e novos números na Etapa 4, sem tocar no resto.

---

## 14. Como o projeto evolui depois

Em ordem de quanto cada coisa melhora o resultado por unidade de esforço:

| # | Melhoria | O que resolve |
|---|---|---|
| 1 | **Olhar a carteira (CDA)** | A lacuna da seção 13: mede risco de crédito de verdade, em vez de inferir |
| 2 | **Testar o ranking no passado** | Montar o ranking com dados até jun/2025 e ver como o Top 5 se comportou no segundo semestre. Transforma "é defensável em teoria" em "funcionou" |
| 3 | **Separar habilidade de sorte** | Descontar do retorno a parte que veio só de estar exposto a juros e a crédito, e ranquear pelo que sobra |
| 4 | **Corrigir a oscilação subestimada** | Ajustar a medida de risco pela autocorrelação dos retornos, que denuncia marcação suavizada |
| 5 | **Incluir imposto** | Rentabilidade líquida de verdade, respeitando o prazo de cada perfil |
| 6 | **Escolher os 5 como carteira** | Hoje escolho os 5 melhores individualmente, que podem ser cinco fundos quase iguais. Escolher o melhor conjunto diversificaria |
| 7 | **Aumentar a cobertura de taxas** | Buscar taxa em outras fontes para recuperar parte dos 44% perdidos |

A estrutura em seis etapas foi desenhada para que qualquer item acima seja **uma adição**, não uma reescrita: nova fonte entra na Etapa 1, novo número na Etapa 4, novo peso em um arquivo de configuração.

---

## 15. Cronograma

| Dia | Data | O que fica pronto |
|---|---|---|
| 1 | 20/08 | Estrutura do projeto, dependências, testes escritos antes do código |
| 2–3 | 21–22/08 | Etapas 1 e 2: baixar e conferir |
| 4–5 | 23–24/08 | Etapas 3 e 4: juntar e calcular, com testes das fórmulas |
| 6 | 25/08 | Etapas 5 e 6: ranquear, simular e publicar |
| **7 manhã** | 26/08 | **Teste no passado (seção 8.1): três datas de corte, medição e relatório** |
| 7 tarde | 26/08 | README, `ranking.md`, revisão |
| 8 | 27/08 | Folga, vídeo de 5 minutos |
| | **28/08 20h** | **Entrega** |

---

## 16. Resumo das decisões

| Decisão | Escolha | Por quê | O que aceito perder |
|---|---|---|---|
| Unidade de análise | Classe | É o que a CVM publica desde 2024 | Séries anteriores a 2021 ficam de fora |
| Janela | 12 meses | Mantém 93% do universo e um só regime de juros | Menos dados por fundo |
| Universo | Só quem publica taxa e prazo | Não recomendo o que não sei precificar | Perco 44%, sobretudo no qualificado |
| Comparação | Só entre fundos parecidos | Evita premiar quem só tomou mais risco | Grupos pequenos ficam ruidosos |
| Peso maior | Taxa, não rentabilidade | Taxa é o que persiste em 2026 | Contraintuitivo à primeira vista |
| Resultado | Top 5 com grau de confiança | Honesto sobre o ruído | Menos vendável que "o melhor fundo do Brasil" |
| Perfis | 2 | É a divisão que a CVM já faz | Menos granular que 3 ou 4 |
| Infraestrutura | Mínima | 1.000 fundos, 200 MB | Não demonstra escala de cluster |
