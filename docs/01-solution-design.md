# Desenho da solução

**Ranking de fundos de renda fixa brasileiros · data de referência 31/12/2025**

---

## 1. O problema, e a ideia

Existem 36.594 classes de fundos registradas na CVM. A pergunta é quais cinco um cliente
deveria comprar.

"Melhor" não tem resposta única: depende de quanto o cliente pode investir, de quando vai
precisar do dinheiro e de quanto risco aguenta. Então o trabalho tem duas partes, **medir** os
fundos de forma correta e **decidir** o que "melhor" significa, com essa decisão explícita e
fácil de mudar.

A ideia em um parágrafo: pego os fundos que um cliente comum consegue de fato comprar, calculo
dez números por fundo a partir da cota diária, comparo cada um **apenas com fundos parecidos**,
somo com pesos que dependem do perfil, e refaço a conta mil vezes sacudindo dados e pesos.
Publico os cinco que continuam aparecendo no topo. O resultado não é "o fundo número 1". É
"estes cinco se sustentam, e a ordem entre eles não significa muita coisa".

---

## 2. Quais fundos entram na disputa

Todos os números abaixo foram medidos nos arquivos reais.

| Corte | Sobram |
|---|---:|
| Classes registradas na CVM | 36.594 |
| Só renda fixa | 7.759 |
| Em funcionamento normal | 7.337 |
| Condomínio aberto | 6.580 |
| Não exclusivo | 3.498 |
| Com série de cotas | 3.270 |
| Pelo menos 200 observações | 2.924 |
| Patrimônio ≥ R$ 10 milhões | 2.690 |
| Pelo menos 500 cotistas | 787 |
| Taxa e prazo verificáveis | 514 |
| **Alcançáveis por pessoa física** | **472** |

Destes, 455 são acessíveis ao varejo e 17 restritos a qualificado. O funil é
impresso a cada execução e conferido contra este baseline: se algum passo sair mais de 3% do
esperado, o programa **para** em vez de publicar.

Dois cortes merecem explicação.

**Taxa e prazo verificáveis.** Não recomendo um fundo se não consigo dizer quanto ele custa e
em quantos dias o dinheiro volta. A palavra é *verificáveis* e não *publicados*, porque para
classes que investem através de outros fundos o valor publicado não é o preço que o cliente
paga. Ver a seção 6.1.

**Alcançáveis por pessoa física.** O campo `Publico_Alvo` da CVM classifica a *qualificação* do
investidor, não a *natureza* dele: um fundo vendido apenas a empresas é "Público Geral" para a
CVM. Quatro dos dez fundos publicados antes desta regra eram restritos a pessoa jurídica pelo
próprio regulamento, e um quinto era corporativo na prática apesar de a cláusula permitir
pessoa física.

A correção mede em vez de ler. O perfil mensal da CVM traz a base de cotistas de cada classe
quebrada por tipo de detentor, com cobertura de 514 em 514, e a pergunta deixa de ser *quem
pode entrar* para ser **quem está dentro**. Classe sem nenhuma pessoa física e sem nenhum
cotista por distribuidor sai. Cotista por distribuidor conta a favor, porque é uma linha opaca
que esconde justamente o varejo; classe sem o arquivo entregue fica, porque ausência do
relatório não é ausência de pessoas. Não há limiar: uma pessoa basta. Ver a seção 6.2 e a D-050.

**Quinhentos cotistas.** O corte começou em 10, e o primeiro ranking trouxe fundos com 17, 31 e
70 cotistas e dezenas de bilhões de patrimônio: veículos institucionais rotulados "Público
Geral". A lacuna que isso revela não é aleatória, porque fundos de varejo são obrigados a
publicar lâmina e os restritos a qualificado não. É desenho da regulação.

---

## 3. De onde vêm os dados

Tudo público, sem credencial.

| Fonte | O que traz |
|---|---|
| CVM, informe diário | cota, patrimônio, cotistas, aplicações e resgates de cada dia |
| CVM, registro de fundos e classes | classificação, público-alvo, aberto ou fechado, exclusivo |
| CVM, extrato e lâmina | taxa de administração, prazo de resgate, aplicação mínima |
| CVM, composição de carteira (CDA) | qual fundo cada classe compra |
| CVM, perfil mensal | a base de cotistas de cada classe, por tipo de detentor |
| Banco Central, série 12 | CDI de cada dia |
| ANBIMA | a classificação que define os grupos de comparação, que chega dentro do registro da CVM |

**Três armadilhas que quebrariam o projeto se eu não tivesse olhado os arquivos antes.** O
informe diário é por **classe** desde 2024, não por fundo, e quem assume o formato antigo cruza
errado sem receber erro nenhum. O `cad_fi.csv`, que aparece em qualquer tutorial, cobre 10% dos
fundos de renda fixa e tem 0% das taxas preenchidas. E o campo `Data_Inicio` do registro não é a
data de início do fundo, é a data de adaptação à RCVM 175: acreditar nele joga fora 66% do
universo, incluindo fundos de trinta anos, quando a idade mediana real é 7,4 anos. As treze
armadilhas conhecidas estão no `CLAUDE.md`, cada uma com teste de regressão.

**O benchmark é o CDI para todos os grupos, e a saída diz isso.** O livro-texto manda usar IMA-B
para indexados à inflação e IRF-M para prefixados, mas a ANBIMA publica o IMA como foto do dia e
não como série histórica, e uma janela que termina numa data passada não se reconstrói disso.
Medi o custo antes de aceitá-lo: **91,8% do universo de varejo é corretamente servido pelo
CDI**, 8,2% precisaria de IMA-B, e prefixado puro é zero. A comparação intra-grupo absorve a
maior parte do resto, porque um benchmark deslocado move todos os 8,2% juntos. O que ela não
absorve é o retorno por unidade de risco, que divide esse excesso deslocado por volatilidades
diferentes. Por isso `benchmark_by_group` sai preenchido grupo a grupo: um campo vazio seria
pior que um ausente.

---

## 4. As seis etapas

Cada uma é uma pasta de código, recebe uma coisa e devolve outra. Nenhuma depende de como a
anterior foi escrita por dentro, só do formato do que ela devolve.

**1. Baixar.** Com repetição em caso de falha, disjuntor por servidor, e verificação de que o
arquivo é mesmo o que diz ser, porque a CVM devolve página de erro com status 200. Cada arquivo
é lido uma vez e guardado como Parquet sob um nome que carrega o SHA-256 da origem: **a chave é
o hash, não o nome**, porque a CVM sobrescreve arquivos em retificação e um cache por nome
serviria número velho para sempre.

**2. Conferir.** Toda linha passa por um schema declarado. O que falha vai para quarentena
**com o motivo escrito**, e se mais de 5% de um arquivo for descartado o programa para. Variação
diária acima de 20% é marcada e não descartada, porque pode ser amortização legítima.

**3. Juntar.** O painel de cotas é montado varrendo os arquivos colunares, não empilhando uma
dúzia de frames abertos ao mesmo tempo.

**4. Calcular.** Os dez números da seção 5, mais a taxa medida da seção 6.1.

**5. Ranquear.** Percentil dentro do grupo de pares, soma ponderada, e mil simulações.

**6. Publicar.** Os arquivos da seção 9.

```bash
uv run ranking --reference-date 2025-12-31
```

Um comando, mesmo resultado. `--validate` roda também o teste fora da amostra. A linha de
comando é casca fina: o programa inteiro é a função `pipeline.run(reference_date=...)`, e outro
time a importa sem precisar de shell.

**Point-in-time é aplicado em três lugares**, na validação do informe, na escolha do extrato
vigente e na montagem do painel. Parece exagero e não é: uma única linha com data posterior não
levantaria erro nenhum, apenas deixaria o teste no passado silenciosamente otimista.

---

## 5. Os dez números

Todos saem do valor da cota, que **já vem descontado das taxas**. É o retorno que o cotista
embolsou.

| Número | Como se calcula |
|---|---|
| Rentabilidade | cota final ÷ cota inicial − 1 |
| Ganho sobre o CDI | rentabilidade − CDI acumulado sobre os mesmos dias |
| Oscilação | desvio-padrão dos retornos diários, anualizado por 252 |
| Retorno por unidade de risco | ganho sobre o CDI ÷ oscilação |
| Pior queda | maior perda do topo ao fundo no período |
| Dias no vermelho | % dos dias em que o fundo perdeu |
| Taxa de administração | medida contra o fundo master, ou declarada (seção 6.1) |
| Prazo de resgate | conversão + pagamento, tudo convertido para dias corridos |
| Tamanho | patrimônio e número de cotistas |
| Estabilidade do dinheiro | (aplicações − resgates) ÷ patrimônio |

**Por que 12 meses e não 3 anos.** Cada ano a mais de histórico custa cerca de 10% do universo:
12 meses mantém 93% dos fundos, 24 meses 82%, 36 meses 74%. Além disso, 2021 a 2023 teve a Selic
indo de 2% a 13,75%, um mundo diferente de 2025, e esticar a janela mistura dois regimes e ainda
enche a amostra de fundos velhos que sobreviveram.

**E doze meses são doze meses.** A janela é contada da própria data de referência: 31/12/2025
menos doze meses começa em **01/01/2025** e contém **252 dias úteis**, contra os **14,3242%** que
o CDI fez no ano-calendário. Começar no primeiro dia do mês doze meses atrás daria 01/12/2024,
treze meses e 273 dias, e o que sairia errado é justamente o que o leitor consegue conferir: um
retorno que não bate com o que o fundo publica. Por isso o `ranking.json` publica `window_start`
como data, e não só a contagem de meses.

---

## 6. Como se decide o que é "melhor"

O corte é **quando o cliente precisa do dinheiro de volta**, e sai do próprio dado: 58% do
universo de varejo devolve em até um dia (D+0 ou D+1), então uma lista única entregaria os mesmos
cinco fundos para quem guarda para uma viagem e para quem guarda para três anos.

O enunciado sugere varejo contra investidor qualificado, e eu comecei por aí. **O dado não
sustentou:** só 28% dos fundos restritos a qualificado publicam taxa e prazo, contra 64% no
varejo, e o universo elegível cai para 17 fundos.

| | **Reserva de emergência** | **Dois anos ou mais** |
|---|---|---|
| Aplicação mínima aceita | até R$ 5 mil | até R$ 50 mil |
| Prazo de resgate aceito | até D+1 | até D+30 |
| Fundos elegíveis | 165 | 313 |

Os universos se sobrepõem de propósito: quem tem horizonte longo pode comprar um fundo D+0,
porque liquidez sobrando não é defeito.

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

A taxa é o maior peso individual nos dois perfis. Custo é o único número que se sabe com certeza
sobre o ano que vem, e apenas 40% dos fundos bateram o CDI em 2025. Mas ele **não** é o que mais
separa os fundos: medido no universo elegível, o excesso sobre o CDI vai de −2,46% a +0,29% entre
o percentil 10 e o 90, amplitude de 2,75 pontos, contra 1,60 da taxa. O que sustenta o peso da
taxa é a persistência dela, não a dispersão.

### 6.1 A taxa é medida, não lida

O extrato traz uma taxa declarada, e para uma família de classes ela não é o preço do cliente.
No arquivo, 580 das 2.655 classes presentes em 2024 e 2025 tiveram a taxa declarada cair três
vezes ou mais, e 235 foram parar em exatamente 0,040%, algumas vindas de 2,60%.

Uma classe alimentadora aplica quase todo o patrimônio num único fundo, então as duas séries de
cota são a mesma carteira precificada duas vezes, e o que as separa é o que a classe retém:

> taxa = 1 − (crescimento da classe ÷ crescimento do master) ^ (1 ÷ anos)

Três regras decidem o número, e cada uma custa ao fundo em vez de premiá-lo. Onde os dois valores
existem, vence o **maior**. Classe que investe através de outros fundos e **não pôde** ser medida
fica sem taxa e sai pelo corte da seção 2. Todo o resto mantém o que declarou.

Os dois números são publicados lado a lado. Evidência e conferência externa em
`docs/04-a-taxa-e-a-conferencia.md`.

### 6.2 Quem está dentro, e não quem pode entrar

Pela mesma razão da taxa, o acesso de pessoa física é medido e não lido. O detalhe está na
seção 2, junto do corte que ele implementa; o que importa aqui é que as duas correções têm a
mesma forma. O projeto perguntava ao formulário e passou a perguntar ao dado.

Resta um terceiro caso do mesmo padrão, ainda aberto: o corte de cotistas, que quer saber se
quem investe é varejo e responde com quantos cotistas existem. A seção 12 o declara.

### Comparação só entre iguais

Cada número vira a **posição relativa do fundo dentro do seu grupo** ANBIMA antes de receber
peso. Sem isso, o ranking viraria automaticamente "os cinco que tomaram mais risco de crédito",
porque em 2025 eles renderam mais e o problema deles ainda não apareceu. Categoria pequena demais
é jogada no universo inteiro, porque percentil entre quatro é ruído com cara de informação. Os
extremos são aparados em 1% e 99% antes do percentil, para que um fundo com cota mal informada
não defina o topo da escala para os outros.

### Duas notas, porque percentil é relativo a alguma coisa

Comparar dentro do grupo responde *este fundo é bom para o que ele é?*, que é a pergunta
respondível a partir de uma série de cotas. Ela é **silenciosa sobre o grupo**: ser o primeiro de
dezoito vale 1 numa categoria forte e numa fraca.

Então todo fundo publica duas notas, a nota contra os pares, que decide o ranking, e a mesma nota
recalculada contra todo o universo elegível do perfil. Na entrega, o primeiro do perfil de prazo
tira 82,3 no grupo e 63,6 no universo. Não invento um termo de qualidade de grupo para corrigir a
soma, porque isso exigiria afirmar que uma categoria vale mais que outra, exatamente o julgamento
que a comparação intra-grupo existe para evitar.

### Peso só vale para critério que separa

O perfil de liquidez filtra para resgate em até um dia e depois dá peso ao prazo, mas quase todo
fundo que sobra liquida em D+0. Todos empatam, o percentil sai 0,5 para todo mundo, e o peso não
decide nada.

Critério cuja dispersão fica abaixo de um piso declarado é tratado como inerte: o peso vai
proporcionalmente para os que ainda distinguem, e a saída nomeia o critério e publica os pesos
**de fato aplicados** ao lado dos declarados. É regra sobre a forma do dado, e o universo decide
qual critério cai a cada execução.

### Cinco fundos, não cinco notas

Uma gestora roda uma carteira e a vende por várias classes de distribuição, e a Caixa tem **doze**
sobre uma só. Cada uma é elegível e tira quase a mesma nota, então um Top 5 com duas delas entrega
quatro exposições sem avisar.

Dois fundos contam como um quando **a mesma gestora roda os dois** e a volatilidade anualizada da
diferença entre suas séries fica abaixo de 0,10% ao ano. Correlação não serve e não é usada: todo
fundo pós-fixado segue a mesma curva e correlaciona acima de 0,99 com todos os outros, então
qualquer limiar alto o bastante para pegar um gêmeo marca metade do universo. A pergunta certa não
é *estes dois se movem junto*, é *quanto estes dois discordam*.

---

## 7. O ranking é ruidoso, e isso é tratado

Com 12 meses de dados diários, a incerteza sobre o retorno por unidade de risco de um fundo é da
ordem de **±1,5**. A diferença entre o 1º e o 15º colocado, muitas vezes, não existe: é ruído.

Então o ranking é reconstruído **mil vezes**. Em cada rodada, as séries de retorno são reamostradas
em blocos de 21 dias e os pesos são sorteados dentro de faixas declaradas. Conta-se em quantas
delas cada fundo terminou entre os cinco primeiros, e **é essa taxa de aparição que ordena a lista
publicada**, não a nota pontual.

Três detalhes decidem se a simulação significa alguma coisa:

- **Cada fundo sorteia os próprios blocos.** Dar a todos o mesmo calendário reamostrado preserva o
  comovimento do mercado, o que soa conservador e é o contrário: move a seção transversal inteira
  junta e devolve sobrevivência perto de 100% para um ranking que ninguém estressou.
- **O benchmark é reamostrado junto com o fundo.** Medir um ano reamostrado contra o CDI do
  ano-calendário enviesa todo excesso, e o retorno por unidade de risco reordena a favor dos mais
  voláteis.
- **Cada fundo mantém o próprio comprimento de histórico.** Truncar no mais curto jogaria fora um
  quinto da evidência de todo mundo.

Com os três no lugar, as taxas de aparição ocupam a faixa de 31% a 99%, em vez do aglomerado de
97% a 100% que uma reamostragem comum produz. O ranking não ficou menos confiável: parou de
afirmar uma confiança que não tinha.

---

## 8. O teste no passado

Tudo até aqui diz que o método é **razoável**. Nada até aqui diz que ele **funciona**.

O pipeline é rodado como se hoje fosse 31/03, 30/06 e 30/09 de 2025, usando nada publicado depois
de cada data. O Top 5 de cada corte é congelado e medido até o fim do ano contra quatro
referências:

| Referência | Pergunta que responde |
|---|---|
| Mediana dos elegíveis | bate o fundo típico do mesmo universo? |
| CDI, composto sobre exatamente os dias medidos | bate o benchmark que o cliente tem na cabeça? |
| **1.000 carteiras de 5 fundos sorteados** do universo elegível | **bate o acaso?** |
| 1.000 carteiras sorteadas do quartil mais barato | quanto disso é seleção e quanto é a taxa menor? |

A terceira decide o critério. A quarta é **reportada e não faz parte dele**, porque não é
experimento limpo: segurar o custo também muda a composição do grupo, já que o quartil mais barato
é dominado por título público.

**Os retornos saem do painel validado inteiro**, não do universo elegível na data final. Um fundo
escolhido em março que encolheu abaixo do corte até dezembro continua tendo tido um retorno. Ler o
resultado só de quem sobreviveu é o viés de sobrevivência que este teste existe para detectar. A
garantia é uma propriedade testada: o divisor é sempre o número de fundos que o método escolheu.

**O critério, declarado antes de rodar:**

> O método é considerado validado se o Top 5 ficar acima do percentil 60 da distribuição de
> carteiras aleatórias em pelo menos 2 das 3 datas de corte, por perfil.

E duas regras que valem mais que o resultado: **proibido ajustar os pesos depois de ver o teste**,
porque mexer até passar é decorar o segundo semestre de 2025; e **se falhar, eu reporto que
falhou**. Resultado negativo relatado com honestidade vale mais que um Top 5 sem validação, porque
mostra que o método é falseável.

O resultado está em `saida/validacao.md`.

---

## 9. O que o projeto entrega

| Arquivo | Conteúdo |
|---|---|
| `saida/ranking.md` | as duas listas, por que cada fundo está lá, e o que o método não enxerga |
| `saida/ranking.json` | o mesmo, com todos os números, percentis, pesos aplicados e o manifesto das fontes |
| `saida/ranking.html` | as mesmas listas como página autocontida |
| `saida/relatorio_qualidade.md` | o funil de elegibilidade contra o baseline |
| `saida/validacao.md` | o teste fora da amostra |
| `saida/top10.md` | os dez primeiros de cada perfil, para comparar com outros rankings |
| `README.md` | como instalar e executar |

**`saida/` é versionada.** Um arquivo que só passa a existir depois que alguém roda o pipeline não
está entregue. `dados/` não é versionada: é pesada e reconstruível, e o que prende o resultado a
uma execução é o SHA-256 de cada fonte, que já viaja dentro do `ranking.json`.

**Sobre o `top10.md`.** A entrega é de cinco, porque cinco é o tamanho que o método afirma
sustentar. Os dez existem para comparar com listas de mercado, que costumam ter vinte e cinco
nomes. Não é uma segunda resposta: os dois saem de uma única caminhada pela mesma ordem ranqueada,
os cinco entregues são os cinco primeiros dele, e um teste de produto falha se deixarem de ser.

---

## 10. Ferramentas

Python 3.12, Polars para ler e cruzar, Pandera e Pydantic para os contratos, httpx e tenacity para
baixar, NumPy para risco e simulação, pytest, Typer, PyYAML, uv e Docker.

**O que deliberadamente não usei:** banco de dados, orquestrador, Spark, camadas de data lake. São
cerca de mil fundos e 200 MB de arquivo, e o projeto roda em minutos num notebook. Infraestrutura
de escala aqui seria complexidade sem benefício.

---

## 11. Limitações

Em ordem de gravidade, não de conveniência.

**1. Os pesos são arbitrários.** Não existe demonstração de que este conjunto seja melhor que
outro. O que o projeto garante é que, informados outros pesos, o resultado sai coerente com eles:
os pesos vivem em YAML e a simulação mede o quanto o resultado depende deles.

**2. O método não olha a carteira.** Mede resultado, não conteúdo. Dois fundos com números
idênticos podem carregar riscos de crédito completamente diferentes, e crédito privado no Brasil
paga um prêmio pequeno e constante por muitos meses e devolve tudo de uma vez quando o emissor
quebra.

**3. Doze meses não dizem o que acontece em 2026.** A simulação mede a incerteza da amostra, não o
risco de cauda: reamostrar 2025 nunca produzirá uma crise que 2025 não teve.

**4. Viés de sobrevivência.** Fundos que quebraram em 2025 não estão na base.

**5. A volatilidade dos fundos de crédito é subestimada**, porque dívida privada não é remarcada
diariamente. Isso melhora artificialmente a nota de quem carrega mais risco.

**6. Parte da estabilidade medida é mecânica.** Taxas e prazos não variam entre simulações, então
um fundo bem ranqueado por custo aparenta mais robustez do que a evidência sustenta. Por isso a
saída publica também a taxa de aparição contando **só desempenho**.

**7. Indexados à inflação são medidos contra o CDI.** Afeta 8,2% do universo, e a comparação
intra-grupo absorve o efeito no ranking por excesso, mas não no retorno por unidade de risco.

**8. Ignora imposto de renda, e isso não é neutro.** A maioria segue a mesma tabela regressiva e a
ordem relativa se mantém, mas **fundo incentivado de infraestrutura é isento para pessoa física**.
Por isso todo fundo publica `regime_tributario`.

**9. A lista mistura categorias.** Ser o primeiro de dezoito vale 1 num grupo forte e num fraco.
Publico `score` e `score_pool` e o leitor decide.

**10. A taxa é contada duas vezes, de propósito.** A cota já vem líquida, então o excesso dentro
dela já pune o fundo caro. A segunda contagem fala de 2026 enquanto a primeira fala de 2025.

**11. Cada fundo é avaliado isoladamente**, com a única restrição de não repetir a mesma carteira.

**12. O cadastro é uma foto de hoje.** A CVM não guarda versões antigas do registro.

### Sobre a concentração em poucas gestoras

Vale contar com a ordem em que aconteceu, porque a primeira conclusão estava errada.

Até 24/08, sete das dez posições eram do Itaú, e o projeto explicava isso como aritmética coerente
do critério: a gestora pratica taxas baixas nos fundos de casa e custo é o maior peso. **A
explicação estava incompleta.** Aquelas classes declaravam 0,040% e cobravam de 0,40% a 1,81%.
Quando a taxa passou a ser medida, o Itaú saiu inteiro da lista de liquidez e sobraram nomes de
sete casas diferentes.

O `manager_share` continua publicado e continua útil: essa gestora responde por 28,5% dos 165
fundos do perfil de liquidez e por 19,5% dos 313 do de prazo. O que a história ensina é que um
número que explica um resultado incômodo merece a mesma desconfiança que um número que o
contradiz.

---

## 12. O que fica em aberto

**Olhar a carteira (CDA).** É a lacuna principal. O arquivo é lido hoje só para achar o fundo por
trás de cada classe, nunca para o que esse fundo tem dentro. Meu ranking não teria como
distinguir, em janeiro de 2023, um fundo com Americanas na carteira de um sem.

**O corte de cotistas não separa varejo de institucional.** Ele nasceu para tirar fundo com 17
cotistas e dezenas de bilhões, e faz isso. Não pega um fundo com 1.360 cotistas e R$ 23 bi, que é
o mesmo veículo com outro tamanho. Patrimônio por cotista responderia melhor, e não foi
implementado porque a escolha do limite viria depois de eu já saber quais fundos ele removeria.

**Separar habilidade de sorte**, descontando do retorno a parte que veio só de estar exposto a
juros e a crédito.

**Corrigir a oscilação subestimada**, ajustando pela autocorrelação dos retornos, que denuncia
marcação suavizada.

**Incluir imposto**, respeitando o prazo de cada perfil.

**Escolher os cinco como carteira**, em vez dos cinco melhores individualmente.

A estrutura em seis etapas foi desenhada para que qualquer um desses seja **uma adição** e não uma
reescrita: fonte nova entra na etapa 1, número novo na etapa 4, peso novo num arquivo de
configuração. A taxa medida, que é a mudança mais recente e mais consequente do projeto, entrou
exatamente assim.
