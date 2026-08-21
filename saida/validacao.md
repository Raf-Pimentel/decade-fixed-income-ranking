# O método funciona? Teste fora da amostra

O ranking foi reconstruído em três datas passadas, usando **nada publicado depois de cada uma**, e os cinco fundos escolhidos foram medidos até 31/12/2025.

O critério de sucesso e a regra do fundo descontinuado foram escritos em `configs/profiles.yaml` e commitados **antes** desta execução. A regra 11 do contrato de trabalho proíbe alterá-los agora: resultado ruim se reporta, não se conserta.

## Veredito: Método validado. Acima do percentil 60% das carteiras aleatórias em — varejo_liquidez: 2 de 3 · varejo_prazo: 3 de 3.

| Corte | Perfil | Top 5 rendeu | CDI | Mediana dos elegíveis | Vantagem | Contra o acaso | Contra os baratos | Bateram a mediana |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 31/03/2025 | varejo_liquidez | +10.57% | +11.00% | +10.67% | **-9 pb** | p68% ✅ | p75% | 3 de 5 |
| 31/03/2025 | varejo_prazo | +10.61% | +11.00% | +10.66% | **-4 pb** | p71% ✅ | p76% | 4 de 5 |
| 30/06/2025 | varejo_liquidez | +7.36% | +7.43% | +7.14% | **+21 pb** | p99% ✅ | p100% | 5 de 5 |
| 30/06/2025 | varejo_prazo | +7.28% | +7.43% | +7.13% | **+15 pb** | p94% ✅ | p95% | 5 de 5 |
| 30/09/2025 | varejo_liquidez | +3.26% | +3.59% | +3.41% | **-15 pb** | p22% ❌ | p63% | 3 de 5 |
| 30/09/2025 | varejo_prazo | +3.39% | +3.59% | +3.40% | **-1 pb** | p72% ✅ | p84% | 4 de 5 |

**Contra o acaso** é a coluna que decide o veredito: em que percentil o Top 5 caiu numa distribuição de mil carteiras de cinco fundos sorteados do mesmo universo elegível naquela data. Bater a mediana dos pares é fácil; bater o sorteio não é.

### O que os números dizem, sem arredondar para cima

A vantagem sobre a mediana dos elegíveis ficou entre **-15 e +21 pontos-base**, e o Top 5 ficou acima dessa mediana em **2 dos 6 recortes**. Em mais da metade dos casos, portanto, escolher os cinco melhores pelo método rendeu **menos** que pegar o fundo do meio da lista.

Contra o CDI, o Top 5 ficou à frente em **0 dos 6 recortes**. Nenhum. Os fundos escolhidos renderam menos que o CDI em todos os cortes, o que não é surpresa num universo em que só 40% dos fundos bateram o CDI no ano — mas precisa estar escrito, porque é a comparação que o cliente faz de cabeça.

Isso convive com percentis altos contra o sorteio sem contradição: fundos de renda fixa pós-fixados rendem todos perto do CDI, então a distribuição das carteiras aleatórias é muito estreita. Ficar num percentil alto de uma distribuição apertada significa ganhar de quase todo mundo **por muito pouco** — e ficar num percentil baixo significa perder de quase todo mundo, também por muito pouco. Nos dois casos, o que está em jogo são dezenas de pontos-base ao ano. Em renda fixa, onde a taxa mediana é 0,50% ao ano, é exatamente a ordem de grandeza do que há para ganhar — e é também pequeno o bastante para que três recortes não distingam método de sorte.

### Contra os baratos: separando o que é seleção do que é aritmética

A taxa de administração já sai da cota antes de qualquer medição. Como ela é o maior peso dos dois perfis, parte da vantagem sobre a mediana **não é escolha, é subtração**: fundo mais barato entrega mais do mesmo retorno bruto, e isso se sabia antes de rodar qualquer teste.

A coluna **contra os baratos** repete o sorteio usando apenas o quartil mais barato do mesmo universo. O Top 5 ficou entre **p63% e p100%** contra esse controle.

**Leia essa coluna com cuidado, porque ela não é um experimento limpo.** Segurar o custo aproximadamente constante também muda a composição do grupo de comparação: o quartil mais barato é dominado por fundos de título público, que rendem bruto menos que os de crédito. Um percentil mais alto contra os baratos é, em parte, o Top 5 sendo comparado com fundos de risco menor. A coluna é um segundo ângulo sobre o mesmo resultado, não uma decomposição entre custo e habilidade.

Ela é **reportada, não faz parte do critério**. O critério foi congelado antes de existir e continua sendo a comparação contra o universo inteiro.

## O que este teste não prova

Que o método funciona em 2026. Ele mostra o que aconteceu em três recortes de um ano só, com um regime de juros só. É evidência, não garantia — e três datas de corte dentro do mesmo ano não são três observações independentes.
