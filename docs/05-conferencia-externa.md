# Conferência contra fontes externas

Feita em 24/08/2026. O objetivo não é copiar critério de ninguém, e sim ver se o nosso
resultado faz o mínimo de sentido contra o que o mercado publica. Foi essa conferência que
revelou o erro da taxa declarada, registrado em `04-investigacao-taxa.md`.

## Onde o nosso dado bate

| O que | Nosso | Fonte externa |
|---|---|---|
| Sicredi Liquidez Empresarial, taxa | 0,150% | 0,15% (Investidor10) |
| Sicredi Liquidez Empresarial, retorno 2025 | 14,24% | 14,28% (Investidor10) |
| SulAmérica Exclusive, patrimônio | R$ 2,29 bi | R$ 2,24 bi (Mais Retorno) |
| SulAmérica Exclusive, cotistas | 10.437 | 9.594 (data posterior) |
| SulAmérica Exclusive, classe ANBIMA | Duração Baixa Soberano | Duração Baixa Soberano |
| Itaú Crédito Bancário, taxa medida | 0,396% | 0,37% (Economática) |
| Itaú RF Diferenciado, taxa medida | 0,511% | 0,42% (Economática) |

Taxa, retorno, patrimônio e classificação batem por caminhos independentes.

Uma confirmação que veio de fora depois da escolha: o prospecto da família Absolute declara
que essas classes aplicam **no mínimo 95% do patrimônio no fundo master**. O corte de 95% em
`universe.yaml` foi escolhido antes, pelo resíduo que a medição aceita carregar, e coincide
com a estrutura que a indústria usa.

## Nenhum dos dez está entre os fundos populares

A lista dos 25 fundos de renda fixa com mais cotistas do mercado não contém nenhum dos nossos.
Isso é consequência do critério: aquela lista ordena por número de cotistas, e os fundos de
porta de banco que a dominam cobram de 0,30% a 1,95%. Os nossos ficam entre 0,140% e 0,202%.
Um ranking que pesa custo acima de tudo não coincide com um ranking de popularidade, e se
coincidisse seria sinal de que o custo não estava decidindo nada.

**O custo disso é real: esta lista não é o que o varejo brasileiro de fato compra.**

## O que a conferência expôs, e continua em aberto

**O primeiro colocado do perfil de prazo é vendido para empresas.** O Sicredi descreve o
Liquidez Empresarial como recomendado para empresas que buscam gestão de caixa. Ele é Público
Geral no registro da CVM, aceita aplicação dentro do nosso limite e passa em todos os filtros.
Ninguém o vende para uma pessoa guardando dinheiro por três anos.

**Dois outros parecem institucionais pelo patrimônio por cotista:**

| Fundo | Patrimônio por cotista |
|---|---:|
| Bradesco FIF Classe de Investimento | R$ 18,8 mi |
| BB Previdenciário RF Referenciado DI | R$ 16,7 mi |
| BB RF Longo Prazo Corporate | R$ 5,8 mi |
| Tivio Institucional | R$ 0,11 mi |

O corte de 500 cotistas nasceu na D-034 para tirar veículo institucional rotulado varejo. Ele
pega fundo com 17 cotistas. Não pega fundo com 610 cotistas e R$ 11 bi.

É o mesmo defeito de antes: um critério que usa o campo disponível em vez do que se quer
medir. A pergunta certa não é quantos cotistas o fundo tem, é se quem está lá dentro é varejo.

**Não foi corrigido, de propósito.** A regra 11 proíbe escolher um corte depois de ver quais
fundos ele tiraria, e eu já vi. Um limite de patrimônio por cotista escolhido agora seria
escolhido olhando para o resultado. Fica declarado, e é a primeira melhoria depois da entrega.

## Um alarme falso, registrado porque também é resultado

Desconfiei que o filtro de aplicação mínima estivesse aceitando fundos que não declararam o
valor, porque os dez publicados apareciam com o campo vazio. O campo apenas não está na lista
de métricas publicadas. No dado a cobertura é de 100%, não há nulos entre os elegíveis, e o
máximo bate exatamente no limite de cada perfil. O filtro está correto.

## Fontes

- InfoMoney, com dados da Economática: <https://www.infomoney.com.br/onde-investir/quanto-renderam-os-fundos-mais-populares-de-renda-fixa-e-di-em-2025/>
- Investidor10, Sicredi FI RF Liquidez Empresarial: <https://investidor10.com.br/fundos/sicredi-fi-rf-liquidez-empresarial-referenciado-di/>
- Mais Retorno, SulAmérica Exclusive: <https://maisretorno.com/fundo/sulamerica-exclusive-fif-rf-referenciado-di-rl>
- Sicredi, página do produto: <https://www.sicredi.com.br/site/investimentos/fundos-investimentos/fi-rf-liquidez-empresarial/>
- XP, Absolute Atenas Advisory: <https://conteudos.xpi.com.br/fundos-de-investimento/absolute-atenas-advisory-fic-firf-cp/>
