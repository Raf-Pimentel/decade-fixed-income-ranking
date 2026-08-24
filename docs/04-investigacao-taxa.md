# A taxa de administração declarada no extrato de 2025 não é o custo do cliente

Investigação feita em 24/08/2026, depois de comparar o nosso Top 5 com listas
publicadas na imprensa. Este documento registra o que foi medido e de onde saiu cada
número, para que qualquer pessoa possa refazer o caminho.

## Como começou

A InfoMoney, com dados da Economática, publicou os 25 fundos de renda fixa com mais
cotistas do mercado e seus retornos de 2025. Dois fundos do nosso Top 5 estão na lista,
e neles o retorno e a contagem de cotistas batem com os nossos, mas a taxa não:

| Fundo | Cotistas (nós / InfoMoney) | Retorno 2025 (nós / InfoMoney) | Taxa (nós / InfoMoney) |
|---|---|---|---|
| Itaú Crédito Bancário Créd Priv | 141.715 / 143.057 | 14,32% / 14,38% | **0,040% / 0,37%** |
| Itaú RF Diferenciado Créd Priv | 179.029 / 179.560 | 14,62% / 14,68% | **0,040% / 0,42%** |

Cotistas e retorno batem, então são as mesmas classes. A taxa diverge por dez vezes.

## O que a CVM diz

O `extrato_fi_2025.csv` traz `TAXA_ADM = 0.040000` para os dois. **A nossa leitura está
fiel à fonte.** O problema é o que a fonte significa.

Os dois são classes alimentadoras, e isso vem do registro da CVM, sem depender de
interpretar nome: `registro_classe.csv` traz `Classe_Cotas = S` e
`Tipo_Classe = "Classes de Cotas de Fundos FIF"` para ambos. Há 9.996 classes assim no
registro.

Baixei a composição de carteira (`cda_fi_202512.zip`, 24,2 MB,
sha256 `aa4c2d5bf24069bc223ff04be85452abf3ee5e69822c5b6b165e6fb99d07e8b1`) para achar o
fundo master de cada uma. O bloco `BLC_2`, de cotas de fundos, mostra:

- Itaú Crédito Bancário (`51.998.694/0001-39`) aplica R$ 27,4 bi em `56.915.560/0001-20`
- Itaú RF Diferenciado (`20.335.522/0001-51`) aplica R$ 31,3 bi em `10.264.255/0001-15`

E os dois masters declaram `TAXA_ADM = 0.000000`. Ou seja, somando as camadas, a CVM
afirma que o custo total é 0,04%. Isso contradiz a Economática.

## O que decide a questão

A mesma classe, o mesmo CNPJ, em três anos de extrato:

| Fundo | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Itaú Crédito Bancário | 0,400 | 0,400 | **0,040** |
| Itaú Janeiro RF Longo Prazo | 0,900 | 0,900 | **0,040** |
| Itaú Global Dinâmico | | 0,900 | **0,040** |
| Itaú RF Diferenciado | | 0,450 | **0,040** |

De 0,900 para 0,040 não é vírgula deslocada. E o padrão não é desses quatro fundos:

- **580 das 2.655 classes** presentes nos dois anos tiveram a taxa declarada cair três
  vezes ou mais de 2024 para 2025.
- **235 delas foram parar em exatamente 0,040%**, e 135 dessas são do Itaú.
- Entre elas há fundos que declaravam **2,60%, 2,50% e 2,45%** em 2024.

Nenhuma gestora corta a taxa de 2,60% para 0,04%. O valor de 2025 é artefato da forma
como a casa passou a preencher o extrato depois da reorganização em classes da RCVM 175,
e não o preço que o cliente paga.

Há ainda uma classe irmã sobre a mesma carteira, a `ITAÚ CRÉDITO BANCÁRIO RF
DISTRIBUIDORES FIF DA CIC`, que declara **0,400%** no extrato de 2025. Mesma carteira,
canal de distribuição diferente, taxa dez vezes maior no mesmo arquivo e no mesmo ano.

Um sinal independente, dentro do nosso próprio dado: o Itaú Crédito Bancário é um fundo
de crédito bancário e rendeu **exatamente o CDI**, com excesso de −0,00%. Um fundo de
crédito cobrando 0,04% deveria bater o CDI. Render o CDI líquido é o que se espera se
houver perto de 0,4% de custo comendo o prêmio de crédito.

## Por que isso importa para o ranking

A taxa de administração é o **maior peso** dos dois perfis, 30 e 25 de 100. Classes que
declaram 0,040% ficam no topo do percentil de custo em qualquer grupo de pares.

Na entrega de 31/12/2025, **quatro dos cinco fundos do perfil de liquidez e três dos
cinco do perfil de prazo são classes do Itaú declarando exatamente 0,040%**. A conclusão
que o projeto registrou sobre concentração, a de que a lista reflete o mercado que o
varejo tem, precisa ser relida: parte da concentração é artefato de preenchimento, não
retrato de mercado.

O projeto já trata **taxa declarada como exatamente zero** como desconhecida, justamente
porque nesses casos a taxa é cobrada em algum lugar que não vemos. Uma classe que
declara 0,040% depois de declarar 0,900% é o mesmo fenômeno, e o teste do zero não pega.

## Fontes

| O que | Onde |
|---|---|
| Retorno, cotistas e taxa dos 25 fundos mais populares | InfoMoney, com dados da Economática: <https://www.infomoney.com.br/onde-investir/quanto-renderam-os-fundos-mais-populares-de-renda-fixa-e-di-em-2025/> |
| Taxa declarada por classe, 2023 a 2025 | `extrato_fi_2023.csv`, `extrato_fi_2024.csv`, `extrato_fi_2025.csv`, de <https://dados.cvm.gov.br/dados/FI/DOC/EXTRATO/DADOS/> |
| Marcação de classe alimentadora | `registro_classe.csv`, campos `Classe_Cotas` e `Tipo_Classe`, de <https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip> |
| Qual fundo cada alimentadora compra | `cda_fi_BLC_2_202512.csv`, de <https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_202512.zip> |
| Ausência de lâmina para esses fundos | `lamina_fi_202510/11/12.zip`, mesma origem. Apenas 1.141 classes publicam lâmina, e nenhuma das duas está entre elas |
| Retorno, cotistas e taxa que publicamos | `saida/ranking.json` desta entrega |

## A taxa medida, em vez da taxa declarada

O campo declarado não é confiável, então a taxa passa a ser **medida**. Uma classe
alimentadora aplica quase todo o patrimônio num único fundo master. As duas séries de cota
são a mesma carteira, e a única coisa que as separa é o que a classe cobra. Então:

> **taxa real da classe = retorno do master menos retorno da classe, anualizado**

Isso não depende de nenhum campo declarado, de nenhum plano de contas e de nenhuma fonte
externa. Usa `inf_diario` para as duas séries e a CDA para saber quem é o master.

Aplicado aos fundos publicados nesta entrega, sobre os 252 dias úteis de 2025:

| Fundo | Declarada | **Medida** | Erro |
|---|---:|---:|---:|
| Itaú Janeiro RF Longo Prazo | 0,040% | **1,814%** | 45x |
| Itaú Global Dinâmico | 0,040% | **0,641%** | 16x |
| Itaú RF Diferenciado Créd Priv | 0,040% | **0,511%** | 13x |
| Itaú Crédito Bancário Créd Priv | 0,040% | **0,452%** | 11x |
| BB RF Longo Prazo Corporate | 0,200% | **0,232%** | 1,2x |

Duas leituras importam aqui.

A primeira é que **o BB está quase certo**. O problema não é da CVM nem do campo: é de como
uma casa específica passou a preencher o extrato. Isso significa que a taxa declarada continua
utilizável para a maior parte do universo, e que a correção precisa ser cirúrgica.

A segunda é o tamanho do estrago. O **Itaú Janeiro é o número 2 das duas listas publicadas**.
Ele chegou lá declarando 0,040%, e cobra **1,814%**. A mediana do universo elegível é 0,50%.
Longe de ser um dos mais baratos do Brasil, ele é dos caros, e o maior peso do nosso ranking
o tratou como o mais barato possível.

O número medido também bate com a fonte externa: 0,452% e 0,511% contra os 0,37% e 0,42% da
Economática. Ordem de grandeza igual, por dois caminhos independentes.

### Limite do método

O que se mede é a diferença entre a classe e o fundo que ela compra. Quando a alimentadora
aplica 100% no master, essa diferença é a taxa da classe e nada mais. Quando ela mantém caixa
ou aplica em mais de um fundo, a diferença também carrega o efeito dessa parcela, e a medida
vira teto e não valor exato. O Itaú Global Dinâmico aplica 90% no master, então os 0,641% dele
são menos confiáveis que os demais. Os outros quatro aplicam 100%.

O método também não alcança classes que não são alimentadoras, porque não há master com que
comparar. Para essas, o campo declarado segue sendo a única fonte.

## O que ainda não foi verificado

O número da Economática vem de uma fonte só. A confirmação que falta é a lâmina ou o
regulamento no site do Itaú, que diria o preço praticado hoje. A medição contra o master resolve isso
sem depender dela: dá 0,452% e 0,511% para os dois fundos, por dado da própria CVM.
