# Por que a taxa é medida, e não lida

A taxa de administração é o maior peso do ranking, então é o número que menos se pode errar.
A CVM publica uma taxa declarada no extrato. Para uma família de classes, ela não é o preço
que o cliente paga.

## A evidência

A mesma classe, o mesmo CNPJ, em três anos de extrato:

| Fundo | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Itaú Crédito Bancário | 0,400 | 0,400 | **0,040** |
| Itaú Janeiro RF Longo Prazo | 0,900 | 0,900 | **0,040** |
| Itaú Global Dinâmico | | 0,900 | **0,040** |
| Itaú RF Diferenciado | | 0,450 | **0,040** |

De 0,900 para 0,040 não é vírgula deslocada, e o padrão não é desses quatro fundos. Das 2.655
classes presentes nos dois anos, **580 tiveram a taxa cair três vezes ou mais**, e **235 foram
parar em exatamente 0,040%**, algumas vindas de 2,60%. Nenhuma gestora corta a taxa de 2,60%
para 0,04%. É a forma como uma casa passou a preencher o extrato depois da reorganização em
classes da RCVM 175.

Isso importa porque quem declara 0,040% fica no topo do percentil de custo em qualquer grupo.
Até 24/08/2026, sete das dez posições publicadas eram dessas classes.

## A medição

Uma classe alimentadora aplica quase todo o patrimônio num único fundo. As duas séries de cota
são a mesma carteira precificada duas vezes, e a única coisa que as separa é o que a classe
retém:

> taxa = 1 − (crescimento da classe ÷ crescimento do master) ^ (1 ÷ anos)

Não depende de campo declarado. Precisa de duas séries de cota, que vêm do informe diário, e
de saber qual fundo a classe compra, que vem da composição de carteira. O desenho da solução,
seção 7.1, explica as regras de decisão; `src/ranking/transform/fees.py` as implementa.

Aplicado aos fundos que estavam publicados, sobre os 252 dias úteis de 2025:

| Fundo | Declarada | Medida |
|---|---:|---:|
| Itaú Janeiro RF Longo Prazo | 0,040% | **1,814%** |
| Itaú Global Dinâmico | 0,040% | **0,641%** |
| Itaú RF Diferenciado | 0,040% | **0,511%** |
| Itaú Crédito Bancário | 0,040% | **0,396%** |
| BB RF Longo Prazo Corporate | 0,200% | **0,202%** |

O BB estar certo é a parte que impede a conclusão preguiçosa: o campo não é inútil e a CVM não
está errada. É uma casa específica preenchendo de um jeito específico, e a correção precisava
ser cirúrgica.

## Conferência contra fontes externas

O projeto foi comparado com o que o mercado publica. Não para copiar critério, e sim para ver
se o resultado faz o mínimo de sentido.

| O que | Nosso | Fonte externa |
|---|---|---|
| Itaú Crédito Bancário, taxa | 0,396% | 0,37% (Economática) |
| Itaú RF Diferenciado, taxa | 0,511% | 0,42% (Economática) |
| Sicredi Liquidez Empresarial, taxa | 0,150% | 0,15% (Investidor10) |
| Sicredi Liquidez Empresarial, retorno 2025 | 14,24% | 14,28% |
| SulAmérica Exclusive, patrimônio | R$ 2,29 bi | R$ 2,24 bi (Mais Retorno) |
| SulAmérica Exclusive, classe ANBIMA | Duração Baixa Soberano | Duração Baixa Soberano |

Taxa medida, taxa declarada, retorno, patrimônio e classificação batem por caminhos
independentes. O prospecto da família Absolute também confirma, de fora, o corte de 95% que
`universe.yaml` usa: essas classes aplicam no mínimo 95% do patrimônio no fundo master.

## O que a conferência expôs e continua em aberto

**O corte de cotistas não separa varejo de institucional.** Ele nasceu para tirar fundo com 17
cotistas e dezenas de bilhões, e faz isso. Não pega um fundo com 1.360 cotistas e R$ 23 bi, que
é o mesmo veículo com outro tamanho. Patrimônio por cotista responderia melhor.

Não foi implementado porque a escolha do limite viria depois de já se saber quais fundos ele
removeria, o que a regra 11 do contrato de trabalho proíbe. É a primeira melhoria depois da
entrega.

**A lista não é o que o varejo de fato compra.** Nenhum dos dez publicados está entre os 25
fundos de renda fixa com mais cotistas do mercado, e dois dos vinte primeiros estão. Aquela
lista é dominada por fundos de porta de banco que cobram de 0,30% a 1,95%; os nossos ficam
entre 0,004% e 0,355%. Um ranking que pesa custo acima de tudo não coincide com um ranking de
popularidade.

## Fontes

- Taxa declarada por classe: `extrato_fi_2023/2024/2025.csv`, <https://dados.cvm.gov.br/dados/FI/DOC/EXTRATO/DADOS/>
- Qual fundo cada classe compra: `cda_fi_BLC_2_202512.csv`, <https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/>
- Marcação de alimentadora: `registro_classe.csv`, campo `Classe_Cotas`
- Retorno, cotistas e taxa dos fundos mais populares: <https://www.infomoney.com.br/onde-investir/quanto-renderam-os-fundos-mais-populares-de-renda-fixa-e-di-em-2025/>
- Fichas de fundo: <https://investidor10.com.br> e <https://maisretorno.com>
