# O come-cotas, e quando o fundo é o veículo errado

Este documento responde a um feedback da Decade sobre o ranking: para uma reserva de liquidez
rendendo perto do CDI, um CDB direto ou o Tesouro Selic quase sempre ganham do fundo depois do
imposto. Ele quantifica isso com os próprios números do ranking, e diz onde a afirmação é forte
e onde é nuançada.

## Por que um fundo DI perde para o instrumento direto

Três coisas separam um fundo de renda fixa de comprar o mesmo risco direto:

1. **Taxa de administração.** Sai da cota todo dia. Nos cinco de liquidez vai de 0% declarado a
   0,35%.
2. **Come-cotas.** Fundos abertos não isentos (tabela regressiva) pagam IR **antecipado** no
   último dia útil de maio e novembro: 15% sobre o ganho do semestre, cobrado reduzindo a
   quantidade de cotas do investidor. O dinheiro do imposto sai do fundo antes da hora e **para
   de compor**. Um CDB ou uma LFT só pagam IR **na saída**, então o valor cheio compõe até o
   fim.
3. **A cota não vê o come-cotas.** O `VL_QUOTA` da CVM é pré-imposto — o come-cotas mexe na
   quantidade de cotas, não no valor da cota. Então o ranking, que lê a cota, **não enxerga**
   essa mordida. É por isso que ela precisa entrar por fora.

O Tesouro Selic direto tem uma desvantagem própria, pequena: a **custódia da B3**, 0,20% ao ano
sobre o que passa de R$ 10 mil. Abaixo disso, é zero.

## Os números, líquidos de IR

Retorno anualizado **depois do imposto**, projetando o CDI de 2025 (14,32% em 252 dias úteis) e
o desempenho de cada fundo em 2025. Come-cotas de 15% ao semestre, com o ajuste da alíquota
regressiva na saída (17,5% em 1 ano, 15% a partir de 2). Tesouro Selic = CDI menos 0,20% de
custódia; CDB = 100% do CDI.

| Instrumento | 1 ano | 2 anos | 3 anos |
|---|---:|---:|---:|
| **CDB 100% CDI direto** | **11,82%** | **12,29%** | **12,40%** |
| Tesouro Selic direto (líq. custódia) | 11,65% | 12,12% | 12,23% |
| BNP Paribas Match (melhor dos 5) | 11,81% | 12,17% | 12,17% |
| BTG Pactual Yield DI | 11,72% | 12,07% | 12,07% |
| BB Tesouro Selic | 11,49% | 11,83% | 11,83% |
| Bradesco FIF RF Ref. DI | 11,44% | 11,78% | 11,78% |
| Caixa Giro Empresas | 11,27% | 11,61% | 11,61% |

Gap do melhor fundo (BNP) contra o Tesouro Selic: **+16 pb** em 1 ano, **+5 pb** em 2 anos,
**−6 pb** em 3 anos. Contra o CDB: **negativo em todos**. Os três piores — BB Tesouro Selic,
Bradesco e Caixa Giro — perdem para o Tesouro Selic direto em **todo** horizonte.

## O que os números dizem, honestamente

**Contra o CDB 100% CDI, os cinco perdem depois do IR em todo horizonte.** O CDB não tem
custódia, não tem come-cotas e não tem taxa. É o teto limpo, e nenhum fundo o alcança. Aqui a
Decade está inteiramente certa.

**Contra o Tesouro Selic, o fundo perde a partir de ~2 anos.** Em 1 ano acontece uma inversão
que vale entender em vez de esconder: a custódia de 0,20% da LFT é maior que a mordida pequena
de um único come-cotas, então um fundo a ~100% do CDI empata ou ganha por alguns pontos-base.
A partir de 2 anos o come-cotas composto supera a custódia e o instrumento direto passa à
frente. **E essa inversão de 1 ano depende da custódia:** numa reserva abaixo de R$ 10 mil, onde
a custódia é zero, o Tesouro Selic vira igual ao CDB e o fundo perde já no primeiro ano.

**O BB Tesouro Selic é o pior, e o motivo é estrutural.** Ele existe para entregar Tesouro
Selic e cobra 0,30% para isso. Perde para a LFT direta em **todo** horizonte, por 17 a 39
pontos-base. É o caso mais claro de fundo como veículo errado: paga-se uma taxa por um trabalho
que o Tesouro Direto faz de graça.

## Por que isso não é um bug do ranking

O ranking responde à pergunta do case: **o melhor fundo de renda fixa a partir de dados públicos
da CVM.** O CDB e o Tesouro Selic **não são fundos** e estão fora desse universo. O ranking
achou, dentro da caixa que o case desenhou, fundos estatisticamente defensáveis — e o BNP, o
melhor deles, é competitivo em 1 ano.

O que o feedback da Decade acrescenta é de **mandato**, não de cálculo: para *parquear caixa
perto do CDI*, o veículo certo muitas vezes não é fundo nenhum. Isso é uma limitação do universo
que o case fixou, e o lugar honesto para ela é declarada, não escondida. O `ranking.json` já
publica o `regime_tributario` de cada fundo, o que é o gancho para levar o imposto a sério — e
para o perfil de **prazo**, onde entram fundos incentivados de infraestrutura **isentos** (sem
come-cotas), o imposto de fato reordenaria, a favor deles.

## Ressalvas do cálculo

- **CDI projetado achatado** em 14,32%. Em Selic mais baixa os valores caem juntos; o *gap*
  entre fundo e direto muda pouco, porque é dominado por taxa e come-cotas, não pelo nível.
- **O bruto do fundo** é o retorno líquido de taxa de 2025, projetado como se persistisse. É uma
  hipótese, não uma previsão.
- **Modelo de come-cotas** é a aproximação padrão (15% ao semestre + ajuste na saída); o valor
  exato depende do calendário de maio/novembro, e o efeito é pequeno em 1 ano e cresce com o
  prazo.
- **Risco de crédito** fica de fora: um CDB carrega risco do banco (coberto pelo FGC até R$ 250
  mil por instituição), a LFT é risco soberano, e um fundo DI de título público é risco
  soberano com uma camada de taxa. A comparação é de eficiência tributária e de custo, não de
  risco.
