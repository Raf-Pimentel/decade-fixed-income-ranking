# Fase 1 — Desenho da Solução

**Projeto:** Ranking de fundos de renda fixa brasileiros
**Data de referência:** 31/12/2025
**Prazo:** 28/08/2026, 20h

---

## 1. O problema

Existem milhares de fundos de renda fixa registrados no Brasil. A pergunta é: **quais são os cinco melhores para um cliente?**

"Melhor" não tem uma resposta única. Depende de quanto o cliente pode investir, de quando ele vai precisar do dinheiro de volta, e de quanto risco ele aguenta. Então o trabalho tem duas partes: **medir** os fundos de forma correta, e **decidir** o que "melhor" significa — deixando essa decisão explícita e fácil de mudar.

---

## 2. A ideia, em um parágrafo

Eu pego todos os fundos de renda fixa que um cliente comum consegue de fato comprar. Para cada um, calculo dez números simples a partir do valor da cota de 2025: quanto rendeu, quanto oscilou, quanto caiu no pior momento, quanto cobra de taxa, em quantos dias devolve o dinheiro, e qual o tamanho. Comparo cada fundo **apenas com fundos parecidos com ele** — um fundo que só compra título público não disputa com um que compra dívida de empresa. Somo esses números com pesos que dependem do perfil do cliente. Aí, antes de publicar, **testo se o resultado se sustenta**: refaço a conta mil vezes mexendo levemente nos dados e nos pesos, e só recomendo os fundos que continuam aparecendo no topo. O resultado final não é "o fundo nº 1", é **"estes cinco são consistentemente bons, e a ordem entre eles não significa muita coisa"**.

---

## 3. Quais fundos entram na disputa

Parti de todas as classes registradas na CVM e fui cortando. Todos os números abaixo foram **medidos nos arquivos reais**, não estimados:

| Corte | Sobram | Por que corto |
|---|---:|---|
| Todas as classes registradas na CVM | 36.598 | ponto de partida |
| Só renda fixa | 7.759 | é o escopo do case |
| Em funcionamento normal | 7.337 | fundo cancelado ou liquidado não serve |
| Condomínio aberto | 6.580 | fundo fechado não aceita aplicação nova |
| Não exclusivo | 3.498 | fundo exclusivo é de um único dono |
| Tem série de cota em dez/25 | 3.268 | sem cota não dá para medir nada |
| Patrimônio ≥ R$ 10 milhões | 2.944 | fundo minúsculo não é recomendável |
| Pelo menos 10 cotistas | 1.801 | corta fundos que são exclusivos na prática |
| **Tem taxa e prazo de resgate publicados** | **1.003** | **ver abaixo** |

O último corte merece explicação. **Eu não recomendo um fundo se não consigo dizer ao cliente quanto ele custa e em quantos dias o dinheiro volta.** Isso não é conveniência de dados — é o mínimo de uma recomendação responsável.

Esse corte tem um efeito desigual, e ele é explicável:

| Público-alvo | Fundos | Com taxa e prazo | Cobertura |
|---|---:|---:|---:|
| Público Geral | 1.369 | 871 | **64%** |
| Qualificado | 278 | 79 | 28% |
| Profissional | 154 | 53 | 34% |

A cobertura do varejo é boa porque **fundos de varejo são obrigados por lei a publicar lâmina**. Fundos para investidor qualificado têm obrigação de divulgação mais leve. Ou seja: a lacuna não é um defeito dos dados, é o desenho da regulação. Isso limita o ranking do perfil qualificado, e eu digo isso na entrega em vez de esconder.

**Universo final: ~1.000 fundos, sendo ~870 acessíveis ao varejo.**

---

## 4. De onde vêm os dados

Tudo é público e baixável sem cadastro. Três fontes:

| Fonte | O que traz | Formato |
|---|---|---|
| **CVM — Informe Diário** | Valor da cota, patrimônio, nº de cotistas, aplicações e resgates de cada dia | 1 arquivo ZIP por mês |
| **CVM — Registro de Fundos e Classes** | Nome, gestor, classificação, público-alvo, se é aberto/exclusivo | 1 arquivo ZIP (foto do momento) |
| **CVM — Extrato e Lâmina** | Taxa de administração, taxa de performance, prazo de resgate, aplicação mínima | Extrato: 1 por ano · Lâmina: 1 por mês |
| **Banco Central — série 12** | Taxa CDI de cada dia | API JSON |
| **ANBIMA — índices IMA** | IMA-B, IRF-M e IMA-S: as referências certas para fundos de inflação e prefixados | 1 Excel, download livre |

Volume total para rodar o projeto: **cerca de 15 arquivos, ~200 MB**. Cabe em qualquer notebook.

**Sobre a ANBIMA.** Cheguei a descartar essa fonte porque a base de fundos (`data.anbima.com.br`) exige credencial. Mas os índices IMA são públicos e baixam sem cadastro — e são justamente o que faltava. Comparar **todo** fundo com o CDI é errado: um fundo indexado à inflação tem que ser comparado ao IMA-B, e um prefixado ao IRF-M. Contra o CDI, um fundo de IMA-B parece péssimo num ano de juros altos, quando na verdade só está fazendo o trabalho dele.

Então o benchmark passa a ser **escolhido por grupo**:

| Grupo do fundo | Comparado com |
|---|---|
| Pós-fixado / soberano curto / crédito | CDI |
| Indexado à inflação | IMA-B |
| Prefixado | IRF-M |

A classificação ANBIMA que define o grupo já vem dentro do registro da CVM, então não dependo da API autenticada para nada.

---

## 5. As etapas do projeto

Seis etapas. Cada uma é uma pasta de código, recebe uma coisa e devolve outra. Nenhuma depende de como a anterior foi escrita por dentro — só do formato do que ela devolve.

### Etapa 1 — Baixar

| | |
|---|---|
| **Entrada** | Data de referência (`2025-12-31`) e quantos meses de histórico |
| **Saída** | Arquivos originais salvos em `dados/brutos/`, mais um `manifesto.json` com o nome, o tamanho e a impressão digital (hash) de cada arquivo |
| **O que faz** | Baixa os arquivos da CVM, do Banco Central e da ANBIMA. Se a conexão falhar, tenta de novo 3 vezes com espera crescente. Se o arquivo já existe e a impressão digital bate, não baixa de novo |
| **Tolerância a falha** | Três camadas: **repetição** (3 tentativas com espera crescente), **disjuntor** (após 5 falhas seguidas no mesmo servidor, para de insistir e falha com mensagem clara em vez de travar), e **verificação de conteúdo** (a CVM devolve página de erro com status 200 — confiro se o arquivo é mesmo um ZIP antes de aceitar) |
| **Por que o manifesto** | A CVM **sobrescreve os arquivos** quando corrige um dado, sem avisar e sem manter versão. O manifesto é a única forma de eu provar, daqui a três meses, com qual versão do dado o ranking foi feito |

### Etapa 2 — Conferir

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
| Variação diária acima de 20% | **marco, mas não descarto** — pode ser amortização legítima |
| Fundo tem pelo menos 200 dias de cota no período | tiro da disputa |

**Regra de freio:** se mais de 5% das linhas de um arquivo forem descartadas, o programa **para com erro**. Prefiro não entregar ranking a entregar um ranking torto sem ninguém perceber.

### Etapa 3 — Juntar

| | |
|---|---|
| **Entrada** | Tabelas limpas |
| **Saída** | Uma tabela única: uma linha por fundo por dia, com os dados de cadastro e taxa colados ao lado |
| **O que faz** | Liga a série de cotas ao cadastro do fundo, à taxa e ao prazo de resgate, e ao CDI do dia |

Aqui mora a parte mais difícil do projeto, explicada na seção 10.

### Etapa 4 — Calcular

| | |
|---|---|
| **Entrada** | Tabela única |
| **Saída** | Uma linha por fundo, com os dez números da seção 6 |
| **O que faz** | Calcula rentabilidade, risco, custo e liquidez de cada fundo |

Cada fórmula é uma função pequena com teste próprio. Exemplos de teste: uma série de cota constante tem que dar rentabilidade zero; uma série que dobra tem que dar 100%; a rentabilidade acumulada calculada dia a dia tem que bater com a calculada ponta a ponta.

### Etapa 5 — Ranquear

| | |
|---|---|
| **Entrada** | Números por fundo + arquivo de pesos por perfil |
| **Saída** | Uma lista ordenada por perfil, com nota e com o **grau de confiança** de cada posição |
| **O que faz** | Converte cada número em posição relativa dentro do grupo de fundos parecidos, aplica os pesos, e depois testa se o resultado aguenta (seção 8) |

### Etapa 6 — Publicar

| | |
|---|---|
| **Entrada** | Listas ranqueadas |
| **Saída** | `ranking.json` (para outro sistema consumir) e `ranking.md` (para uma pessoa ler) |
| **O que faz** | Escreve os dois arquivos, com todos os números que justificam cada escolha |

### Como se roda

```bash
python -m ranking --data-ref 2025-12-31
```

Um comando. Mesmo comando, mesma data, mesmo resultado. E qualquer etapa pode ser chamada isolada, de dentro de outro programa:

```python
from ranking import baixar, calcular, ranquear
```

---

## 5.1 Como garanto a qualidade dos dados

Três camadas. Nenhuma delas é uma ferramenta pesada — são três perguntas diferentes.

### Camada 1 — O dado tem a forma certa? (contrato)

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

### Camada 2 — O dado faz sentido? (regras de negócio)

Coisas que o schema não pega, porque dependem de conhecer o mercado. Cada regra é uma função com nome e teste próprio:

| Regra | O que faz |
|---|---|
| `cota_nao_esta_parada` | mesma cota por 10 dias úteis ⇒ fundo saiu da disputa |
| `serie_tem_densidade_minima` | menos de 200 dias no período ⇒ fora |
| `variacao_diaria_plausivel` | acima de 20% ⇒ **marca, não descarta** (pode ser amortização) |
| `cnpj_tem_digito_valido` | valida o dígito verificador, não só o formato |
| `idade_vem_da_fonte_certa` | bloqueia uso de `Data_Inicio` como idade |

Linha rejeitada não some: vai para um arquivo de quarentena **com o motivo**. Assim eu consigo olhar o que foi descartado em vez de confiar que estava tudo bem.

### Camada 3 — O resultado bate com o que eu já sei? (regressão de dados)

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

Se um teste passa de primeira, ele está errado — não testa o que eu acho que testa.

### Os quatro tipos de teste, e por que cada um existe

| Tipo | Exemplo concreto | Que erro pega |
|---|---|---|
| **Invariante financeira** | cota constante ⇒ retorno 0 · cota que dobra ⇒ 100% · composição dia a dia = ponta a ponta · pior queda nunca é positiva | Fórmula errada. É o erro mais caro e o mais silencioso |
| **Contrato** | schema rejeita CNPJ com 13 dígitos, cota negativa, data futura | Dado ruim entrando |
| **Armadilha** | `Data_Inicio` do CNPJ `00068305000135` é 2025, mas a idade tem que sair 31 anos | Regressão das 8 armadilhas que já descobri |
| **Ponta a ponta** | pipeline roda em fixture de 20 fundos × 60 dias e gera JSON válido | Peças que funcionam sozinhas e quebram juntas |

Mais um: **arquivo dourado**. Congelo o `ranking.json` de uma fixture. Se ele mudar sem eu ter mexido de propósito, algo aconteceu.

### Fixtures

Recortes **reais e pequenos** da CVM — 20 fundos, 60 dias — congelados no repositório. Nenhum teste baixa da internet: teste que depende de rede não é teste, é aposta.

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

Cada ano a mais de histórico custa cerca de 10% do universo. Além disso, 2021–2023 teve a Selic indo de 2% a 13,75% — um mundo diferente do de 2025. Esticar a janela mistura dois regimes e ainda enche a amostra de fundos velhos e grandes que sobreviveram, o que enviesa o resultado.

**Uso 12 meses para pontuar** e reporto 3, 6 e 24 meses junto, para quem quiser discordar do meu critério com os números na mão. A janela é um parâmetro de configuração.

---

## 7. Dois perfis de cliente

Não inventei personas. Usei **a divisão que a própria CVM faz** — o campo "público-alvo" do registro — porque é ela que determina o que o cliente pode legalmente comprar.

| | **Varejo** | **Qualificado** |
|---|---|---|
| Quem é | Qualquer pessoa | Quem tem mais de R$ 1 milhão investido |
| Fundos disponíveis | 871 | 1.003 |
| Aplicação mínima aceita | até R$ 50 mil | qualquer |
| Prazo de resgate aceito | até 30 dias | até 90 dias |
| O que importa mais | não pagar caro e conseguir sacar | ganhar do CDI de forma consistente |

### Pesos

| Número | Varejo | Qualificado |
|---|---:|---:|
| Taxa de administração | **25** | 20 |
| Prazo de resgate | **20** | 10 |
| Ganho sobre o CDI | 15 | **25** |
| Retorno por unidade de risco | 15 | 20 |
| Pior queda | 10 | 15 |
| Oscilação | 5 | — |
| Tamanho e estabilidade | 10 | 10 |
| **Total** | **100** | **100** |

**Por que a taxa é o maior peso do varejo, e não a rentabilidade.** Essa é a decisão menos óbvia do projeto, então vale a justificativa: em renda fixa, a taxa é o único número que se sabe com certeza sobre o **futuro**. A rentabilidade passada de 12 meses é, em boa parte, CDI — que todo fundo pegou igual — mais um prêmio de risco de crédito que ainda não deu problema. A taxa, ao contrário, vai ser cobrada em 2026 exatamente como foi em 2025. Dar peso maior ao que persiste é mais defensável do que dar peso maior ao que não persiste.

### Comparação só entre iguais

Antes de aplicar os pesos, converto cada número na **posição relativa do fundo dentro do seu grupo** (fundos de título público competem com fundos de título público, fundos de crédito com fundos de crédito). Uso a classificação ANBIMA, que já vem dentro do arquivo de registro da CVM.

Sem isso, o ranking viraria automaticamente "os cinco fundos que tomaram mais risco de crédito" — porque em 2025 eles renderam mais, e o problema deles ainda não apareceu.

---

## 8. Como lido com o fato de que o ranking é ruidoso

Esta é a parte que separa uma lista bonita de uma recomendação honesta.

Com 12 meses de dados diários, a incerteza sobre o "retorno por unidade de risco" de um fundo é **grande — da ordem de ±1,5**. Isso significa que a diferença entre o 1º e o 15º colocado, muitas vezes, **não existe de verdade**: é ruído. Publicar "este é o melhor fundo do Brasil" com esse nível de incerteza seria desonesto.

Então faço duas coisas antes de publicar:

**Teste 1 — os dados poderiam ter sido diferentes.** Reembaralho a série de retornos de cada fundo em blocos (preservando o comportamento de dias seguidos) e refaço todos os cálculos. Mil vezes.

**Teste 2 — meus pesos poderiam ser outros.** Sorteio variações nos pesos, dentro de faixas razoáveis (a taxa do varejo pode valer entre 20 e 30, não entre 0 e 100). Mil vezes.

Depois, para cada fundo, conto: **em quantas das mil simulações ele apareceu entre os cinco primeiros?**

O Top 5 final são os cinco com maior taxa de aparecimento — não os cinco com maior nota pontual. E cada um sai na entrega com o número junto:

> **1. Fundo X** — apareceu no Top 5 em **91%** das simulações
> **2. Fundo Y** — apareceu no Top 5 em **88%** das simulações

Um fundo que só é primeiro na conta exata, e some quando eu mexo um pouco nos pesos, **não é uma boa recomendação** — e esse teste revela isso.

Isso também responde à crítica mais óbvia que se pode fazer ao projeto: *"os pesos são arbitrários"*. São. Mas eu mostro o quanto o resultado depende deles.

---

## 8.1 O teste no passado: o método funciona?

Tudo até aqui diz que o método é **razoável**. Nada até aqui diz que ele **funciona**. Essa é a diferença entre um argumento e uma evidência, e é a pergunta que qualquer pessoa experiente faz primeiro.

Então faço o teste óbvio: **monto o ranking com dados de meio do ano e vejo o que aconteceu depois.**

### Como funciona

Rodo o pipeline inteiro fingindo que hoje é 30 de junho de 2025. Mesmo código, mesma configuração, nenhuma linha nova:

```bash
python -m ranking --data-ref 2025-06-30
```

Congelo o Top 5 que sair. Depois meço quanto esses cinco fundos renderam de **julho a dezembro de 2025** — período que o ranking não viu.

Se o point-in-time da Etapa 1 estiver correto, isso é literalmente um comando. **É aqui que a disciplina de "nenhuma linha com data posterior entra no cálculo" para de ser virtude teórica e vira benefício concreto.** Se o teste for difícil de fazer, é sinal de que o point-in-time está furado — o próprio teste vira uma auditoria da arquitetura.

### Contra o que comparo

| Referência | Pergunta que responde |
|---|---|
| Mediana do grupo | Meu Top 5 bate o fundo típico da mesma categoria? |
| CDI / IMA-B / IRF-M | Bate o benchmark que o fundo promete seguir? |
| **1.000 carteiras de 5 fundos sorteados** ao acaso do universo elegível | **Meu método bate o acaso?** |

A terceira é a que importa. É o controle que quase ninguém faz, e é o que separa análise de horóscopo. O número que reporto é: **em que percentil da distribuição de carteiras aleatórias meu Top 5 caiu.**

### Três datas de corte, não uma

Um único semestre é uma amostra de tamanho 1 — pode ter sido sorte. Como cada rodada é um comando, faço três: **31/03**, **30/06** e **30/09/2025**, cada uma medida contra o que veio depois.

### O critério de sucesso, declarado antes de rodar

> **O método é considerado validado se o Top 5 ficar acima do percentil 60 da distribuição de carteiras aleatórias em pelo menos 2 das 3 datas de corte.**

Declarar o critério **antes** de ver o resultado é o que me impede de racionalizar qualquer número que apareça. Sem isso, o teste não vale nada — sempre dá para contar uma história bonita depois do fato.

### Duas regras que valem mais que o resultado

**Regra 1 — proibido ajustar os pesos depois de ver o teste.** Se eu mexer nos pesos até o teste passar, eu não validei nada: apenas decorei o segundo semestre de 2025. Isso é a forma mais comum de fraudar a si mesmo em finanças quantitativas, e costuma ser feita sem má intenção.

**Regra 2 — se falhar, eu reporto que falhou.** E digo o que mudaria. Um resultado negativo relatado com honestidade vale mais do que um Top 5 sem validação nenhuma: mostra que o método é falseável, que é justamente o que se espera de um método.

### Um detalhe que precisa ser decidido antes

E se um dos cinco fundos parar de publicar cota entre julho e dezembro? Regra fixada **agora**, para não ser escolhida conveniente depois: o fundo é mantido na carteira com o último valor conhecido e **marcado como descontinuado no relatório**. Fingir que ele nunca esteve lá seria exatamente o viés de sobrevivência que eu critico na seção 12.

### O que este teste ainda não prova

Que o método funciona **em 2026**. Ele mostra que funcionou em três recortes de 2025 — um ano só, um regime de juros só. É evidência, não garantia, e vou escrever isso com essas palavras na entrega.

---

## 9. O que o projeto entrega

| Arquivo | Para quem | Conteúdo |
|---|---|---|
| `ranking.json` | Outro sistema | Top 5 por perfil, com todos os números, os pesos usados, a taxa de aparecimento e o manifesto das fontes |
| `ranking.md` | Uma pessoa | O mesmo, em texto, com um parágrafo explicando cada escolha |
| `README.md` | Quem for rodar | Como instalar e executar, o que cada etapa faz |
| Código + testes | Quem for manter | Um comando para rodar tudo, funções importáveis |

Formato do `ranking.json`:

```json
{
  "versao_do_formato": "1.0.0",
  "data_referencia": "2025-12-31",
  "janela_meses": 12,
  "fontes": { "inf_diario_202512.zip": "sha256:..." },
  "perfis": [{
    "perfil": "varejo",
    "fundos_avaliados": 871,
    "pesos": { "taxa_adm": 25, "prazo_resgate": 20 },
    "top5": [{
      "posicao": 1,
      "cnpj": "00000000000000",
      "nome": "...",
      "gestor": "...",
      "grupo": "Renda Fixa Duração Baixa Soberano",
      "nota": 87.4,
      "aparicao_no_top5": 0.91,
      "numeros": {
        "rentabilidade_12m": 0.1132,
        "ganho_sobre_cdi": 0.0041,
        "oscilacao": 0.0018,
        "pior_queda": -0.0002,
        "taxa_adm": 0.0020,
        "prazo_resgate_dias": 0,
        "patrimonio": 4210000000.0,
        "cotistas": 152331
      },
      "porque": "..."
    }]
  }]
}
```

O campo `versao_do_formato` existe para que outro time possa depender do arquivo sem medo: se eu mudar a estrutura de forma incompatível, o número muda.

---

## 10. Armadilhas que encontrei nos dados

Fui aos arquivos antes de desenhar. Três coisas que quebrariam o projeto se eu não tivesse olhado:

**1. O dado não é mais por fundo, é por classe.** A regra CVM 175 reorganizou os fundos em "classes", e desde janeiro de 2024 o informe diário identifica a classe, não o fundo. Quem escrever o código assumindo o formato antigo faz o cruzamento errado e **não recebe nenhum erro** — só um resultado silenciosamente errado.

**2. O arquivo de cadastro que todo mundo usa está obsoleto.** O `cad_fi.csv`, que é o que aparece em qualquer tutorial, cobre apenas **10%** dos fundos de renda fixa de hoje, e **nenhum deles** tem a taxa preenchida. Taxa e prazo de resgate estão em outros dois arquivos (Extrato e Lâmina).

**3. A data de início do fundo não é a data de início do fundo.** O campo `Data_Inicio` do registro é, na verdade, a data em que o fundo se adaptou à regra CVM 175 — quase todos em 2024 ou 2025:

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

**O que deliberadamente não usei:** banco de dados, orquestrador de tarefas, Spark, camadas de "data lake". São ~1.000 fundos e ~200 MB de arquivo. O projeto roda em minutos num notebook. Colocar infraestrutura de escala aqui seria complexidade sem benefício — e complexidade que ninguém vai avaliar.

**Como isso viraria produção:** a função `rodar(data_ref)` é o programa inteiro. Para rodar diariamente, basta agendá-la (cron, Airflow, o que o time já usar) e apontar a pasta de saída para um bucket. O código não muda — só onde ele escreve.

---

## 12. Limitações

Sendo direto sobre o que este projeto **não** faz:

1. **Mede o passado.** Doze meses de histórico não dizem o que vai acontecer em 2026. O teste da seção 8 mede a incerteza, mas não a elimina.
2. **Só vê fundos que sobreviveram.** Fundos que quebraram em 2025 não estão na base. O universo é, por construção, otimista.
3. **A oscilação de fundos de crédito é subestimada.** Títulos de dívida privada no Brasil não são remarcados todo dia como uma ação. Isso faz o fundo parecer mais tranquilo do que é — e melhora artificialmente a nota de quem carrega mais risco. Compenso comparando só dentro do grupo, mas não resolvo.
4. **Ignora imposto.** Comparo todos os fundos antes do imposto de renda. Como quase todos os fundos de renda fixa seguem a mesma tabela, a comparação relativa continua justa — mas o número absoluto não é o que o cliente leva para casa.
5. **Perde 44% do universo por falta de divulgação de taxa.** Especialmente no perfil qualificado, onde sobram 79 fundos.
6. **O cadastro é uma foto de hoje.** A CVM não guarda versões antigas do registro. Sei a classificação atual do fundo, não a de dezembro de 2025.

---

## 13. O que fica em aberto

**Eu ranqueio os fundos pelo resultado, não pelo que eles têm dentro.**

Esta é a lacuna principal do projeto, e é honesto colocá-la na frente. Dois fundos podem ter rentabilidade, oscilação e pior queda praticamente idênticos — e um deles estar cheio de dívida de uma única empresa em dificuldade, enquanto o outro só tem título público. **Pelos meus dez números, eles são gêmeos. No risco real, não são.**

É exatamente o risco que mais importa em renda fixa brasileira: crédito privado paga um prêmio pequeno e constante por muitos meses e devolve tudo de uma vez quando o emissor quebra. Meu ranking de 2025 não teria como distinguir, em janeiro de 2023, um fundo com Americanas na carteira de um sem.

**A CVM publica esse dado** — é o arquivo de Composição da Carteira (CDA), mensal, com os ativos de cada fundo. Não coube nos 8 dias porque é um volume muito maior e exige entender a estrutura de tipos de ativo, mas o caminho está aberto: seria uma nova fonte na Etapa 1 e novos números na Etapa 4, sem tocar no resto.

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
| — | **28/08 20h** | **Entrega** |

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
