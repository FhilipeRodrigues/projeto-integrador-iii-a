# TechSpec: Consulta de servidores municipais (TCM-GO)

- **Data:** 2026-11-16
- **PRD:** [prd.md](prd.md)
- **Status:** aprovado (2026-11-16). **Revisão 2026-11-18** (seção "Revisão 2026-11-18"): aprovada pelo estudante em 2026-11-18. **Revisão 2026-11-24** (seção "Revisão 2026-11-24"): aba Regras, pedida pelo estudante em 2026-11-24.

## Visão geral

Projeto novo, sem código anterior e sem molde interno. O sistema são dois programas Python, só com a biblioteca padrão:

- **Servidor** (`consulta.servidor`): carrega a base fictícia (arquivo JSON) na memória, escuta em TCP protegido por TLS e atende cada conexão em uma thread. Busca, filtra e calcula idade e tempo de contribuição.
- **Cliente** (`consulta.interface`): janela Tkinter. Cada ação do usuário vira uma requisição JSON ao servidor, feita em thread de trabalho para não travar a janela.

A confiança vem de uma **CA local** gerada por script com o `openssl`: a CA assina o certificado do servidor, e o cliente confia somente nessa CA.

Ambiente verificado em 2026-11-16: Python 3.15.0, Tk 9.0, OpenSSL 3.5.9 (`ssl`, `tkinter` e o executável `openssl` presentes). Código escrito para Python 3.10 ou superior. A doc consultada no Context7 cobre o CPython **3.13.14**, não a 3.15.0 instalada. O comportamento na 3.15 é confirmado pelos testes, não pela doc.

Estrutura de pastas:

```
consulta/            pacote do sistema
  dominio.py         normalização, busca, anos completos, montagem da ficha
  base.py            carrega e valida data/servidores.json
  protocolo.py       enquadramento das mensagens e códigos de erro
  servidor.py        TLS, threads, despacho das operações
  cliente.py         ClienteRede: uma requisição TLS por chamada
  interface.py       janela Tkinter
scripts/
  gerar_base.py      gera data/servidores.json com semente fixa
  gerar_certificados.py   gera a CA e o certificado do servidor (openssl)
data/servidores.json base fictícia (versionada)
tests/               unittest
README.md
```

## Componentes tocados

| Camada | Arquivo / módulo | Mudança | Molde |
|---|---|---|---|
| Dados | `scripts/gerar_base.py`, `data/servidores.json` | novo: gera 10 municípios e 50 servidores com `random.Random(2026)` | — |
| Dados | `consulta/base.py` | novo: lê o JSON e valida campos, tipos e datas; o servidor não sobe se a base for inválida | — |
| Domínio | `consulta/dominio.py` | novo: `normalizar`, `anos_completos`, `buscar`, `montar_ficha` | — |
| Protocolo | `consulta/protocolo.py` | novo: lê e escreve uma linha JSON, limite de tamanho, erros | — |
| Servidor | `consulta/servidor.py` | novo: contexto TLS, laço de `accept`, uma thread por conexão, log | exemplo "Create server SSL socket" da doc do `ssl` |
| Cliente (rede) | `consulta/cliente.py` | novo: contexto TLS que confia só na CA, `consultar(requisicao)` | doc do `ssl`, `create_default_context(cafile=...)` |
| Cliente (UI) | `consulta/interface.py` | novo: `ttk`, lista (`Treeview`), painel da ficha, faixa "dados fictícios", fila entre thread e janela | — |
| Segurança | `scripts/gerar_certificados.py` | novo: chama o `openssl` e grava em `certs/` | — |
| Infra | `.gitignore` | adicionar `certs/` | — |
| Doc | `README.md` | novo: passos de execução | — |

## Modelo de dados

Sem banco. Um arquivo, `data/servidores.json`, é a fonte de verdade e vai para o repositório (é fictício). O `gerar_base.py` o reproduz com semente fixa na mesma versão do Python.

```json
{
  "ficticio": true,
  "servidores": [
    {
      "id": 1,
      "nome": "Maria da Conceição Alves",
      "sexo": "F",
      "data_nascimento": "1968-04-12",
      "municipio": "Anápolis",
      "orgao": "Secretaria Municipal de Educação",
      "pcd": false,
      "doenca_profissional": null,
      "data_ingresso": "1994-03-01",
      "data_solicitacao": "2026-09-15",
      "ultima_remuneracao_centavos": 485000
    }
  ]
}
```

- `doenca_profissional`: `null` = não. Texto = sim, e o texto é o qual.
- Remuneração em centavos inteiros, para evitar erro de ponto flutuante.
- Regras que o gerador cumpre e o `base.py` confere: `id` único; nascimento + 18 anos ≤ ingresso ≤ solicitação; datas válidas; `sexo` em `F` ou `M`; município e órgão não vazios.
- Conteúdo obrigatório da base, para a demonstração fazer sentido: 10 municípios de Goiás com 5 servidores cada, pelo menos 3 nomes com acento, pelo menos 2 nomes que combinam com o mesmo trecho em municípios diferentes, e alguns com PCD ou doença profissional.
- Os nomes são combinações aleatórias de nomes e sobrenomes comuns. Podem coincidir por acaso com pessoas reais, e o README avisa.
- A **data de nascimento nunca sai do servidor**: a ficha entrega só a idade (menos exposição de dado).

Sem dados existentes e sem migração. Se a base mudar, regenera-se o arquivo e reinicia-se o servidor.

## Contratos de API

**Transporte:** TCP + TLS. Uma conexão por requisição: o cliente conecta, envia **uma linha**, lê **uma linha** e fecha. Cada mensagem é um objeto JSON em UTF-8 terminado por `\n`. Limite de 64 KiB por linha e 5 s de timeout por conexão.

**Operações** (campo `op`):

| `op` | Entrada | Resposta de sucesso |
|---|---|---|
| `municipios` | — | `{"ok": true, "dados": ["Anápolis", ...]}` (ordem alfabética) |
| `buscar` | `nome` (texto até 100 caracteres, pode ser vazio) e `municipio` (texto ou `null`) | `{"ok": true, "dados": [{"id": 1, "nome": "...", "municipio": "..."}]}`, ordenada por nome normalizado |
| `ficha` | `id` (inteiro) | `{"ok": true, "dados": {"id", "nome", "sexo", "idade", "orgao", "pcd", "doenca_profissional", "data_ingresso", "data_solicitacao", "ultima_remuneracao_centavos", "tempo_contribuicao_anos", "municipio"}}` |

Datas saem em `AAAA-MM-DD`. O cliente formata para `DD/MM/AAAA` e `R$ 4.850,00`.

**Erro:** `{"ok": false, "erro": {"codigo": "...", "mensagem": "..."}}`.

| `codigo` | Quando |
|---|---|
| `REQUISICAO_INVALIDA` | linha não é JSON, não é objeto, falta campo, tipo errado, `nome` acima de 100 caracteres, `municipio` fora da lista, linha acima do limite |
| `OPERACAO_DESCONHECIDA` | `op` não existe |
| `NAO_ENCONTRADO` | `ficha` com `id` inexistente |
| `ERRO_INTERNO` | exceção inesperada; a mensagem é genérica, sem trecho de código |

Qualquer erro de uma conexão afeta só ela. O servidor continua atendendo (RF-13).

**Regras de cálculo** (`dominio.py`):
- `normalizar(texto)`: NFKD, remove marcas combinantes, `casefold()`, remove espaços nas pontas. A busca é `normalizar(filtro) in normalizar(nome)`.
- `anos_completos(inicio, fim)`: `fim.year - inicio.year`, menos 1 se `(fim.month, fim.day) < (inicio.month, inicio.day)`.
- `idade = anos_completos(data_nascimento, data_solicitacao)`.
- `tempo_contribuicao_anos = anos_completos(data_ingresso, data_solicitacao)`.

**Segurança e log:**
- O servidor escuta em `127.0.0.1` por padrão. O log (terminal) registra, por conexão: hora, endereço do cliente, versão e cifra do TLS, operação e resultado. Não registra o conteúdo da ficha.
- A ficha só é consultada por `id` que o cliente já recebeu na lista. O `nome` é usado só para comparação, nunca em caminho de arquivo nem em comando.

## Decisões

- **Protocolo:** JSON por linha sobre socket TLS, em vez de HTTP/REST. A proposta fala em "comunicação em rede" e o material usa cliente-servidor sobre TCP. O formato é fácil de mostrar no vídeo e não exige framework. HTTP traria mais peças sem ganho.
- **Uma conexão por requisição**, em vez de conexão persistente. Não há estado de sessão (sem autenticação), cada consulta é independente, e queda de servidor aparece só na ação que falhou. O custo do handshake local é desprezível (RNF-03).
- **Threads (`threading`), uma por conexão**, em vez de `asyncio` ou atendimento sequencial. Atende RF-11 com pouco código. A base é somente leitura em memória, então não há trava.
- **Handshake TLS dentro da thread do cliente**, não no laço de `accept`. Um cliente lento não bloqueia os outros.
- **CA local gerada com o executável `openssl`**, em vez de certificado autoassinado ou da biblioteca externa `cryptography`. A CA é a decisão do estudante e o material trata de Autoridade Certificadora. A biblioteca externa violaria o RNF-04. O custo é depender do `openssl` na hora de gerar os certificados (ver riscos).
- **Cliente verifica servidor** (`ssl.SSLContext(PROTOCOL_TLS_CLIENT)`, `check_hostname` e `CERT_REQUIRED` ligados) carregando só a `ca.crt` do projeto. O certificado do servidor tem SAN `DNS:localhost` e `IP:127.0.0.1`. Não há autenticação do cliente (mTLS fica fora do escopo). TLS mínimo: 1.2.
- **Certificados compatíveis com a verificação estrita.** A partir do Python 3.13, `create_default_context` liga `VERIFY_X509_STRICT` e `VERIFY_X509_PARTIAL_CHAIN` (doc do CPython 3.13.14). Por isso o script emite a CA com `basicConstraints` crítico (`CA:TRUE`), `keyUsage` crítico (`keyCertSign, cRLSign`) e `subjectKeyIdentifier`. O certificado do servidor leva `authorityKeyIdentifier`, `keyUsage` (`digitalSignature, keyEncipherment`) e `extendedKeyUsage = serverAuth`. Não desligo o modo estrito.
- **Chaves RSA 2048 com SHA-256**, validade de 825 dias para a CA e para o servidor (valores de `scripts/gerar_certificados.py`). O material cita RSA, e 2048 bits basta para o protótipo local e gera rápido. *(Ajustado em 2026-11-24: o texto original dizia RSA 3072, 3 anos para a CA e 1 ano para o servidor, mas a implementação sempre usou estes valores.)*
- **Cálculos no servidor.** O RF-10 diz que o servidor processa e devolve. O cliente só apresenta. A fórmula fica em um lugar só e é testada sem janela.
- **Remuneração em centavos inteiros** na base e no protocolo.
- **`nome` vazio** na busca devolve todos os servidores (respeitando o município). Facilita a demonstração e a navegação. Confirmado pelo estudante e incorporado ao RF-03 do PRD.
- **Aprovações do estudante em 2026-11-16:** (1) manter as extensões exigidas pela verificação estrita do Python; podem ser relaxadas no futuro se pesarem. (2) Manter o `openssl` como gerador de certificados. O `openssl` é um executável, não uma biblioteca Python, então o RNF-04 continua valendo. Se o `openssl` virar problema, fica autorizado o plano B: a biblioteca `cryptography`, com o RNF-04 relaxado só para o script de certificados. (3) Nome vazio lista todos. (4) O comportamento na Python 3.15 fica confirmado pelos testes.
- **Tkinter com `ttk`**, rede em thread de trabalho e resultado devolvido à janela por uma `queue.Queue` consultada com `after()`. Tk não é seguro para threads. Isso cumpre RF-12 (janela não trava).
- **A interface recebe o `ClienteRede` por parâmetro.** Isso permite testar a janela com um cliente falso, sem rede nem certificados.
- **Opções de linha de comando mínimas.** Servidor: `--host` (padrão `127.0.0.1`), `--porta` (8443), `--certs` (pasta, padrão `certs`). Cliente: `--host`, `--porta`, `--ca`. Existem porque a demonstração do RF-14 sobe um servidor com certificado de outra CA, e porque a porta pode estar ocupada.
- **Testes com `unittest`**, em vez de `pytest`, que é dependência externa.
- **Base versionada e gerada por script**, em vez de gerada a cada execução. A banca vê a base, e o resultado não depende da versão do Python da máquina.

## Riscos

- **Verificação estrita rejeita o certificado** (erro `CERTIFICATE_VERIFY_FAILED`, por exemplo "Missing Authority Key Identifier") — mitigação: extensões listadas nas decisões e teste de aperto de mão real, com CA e servidor gerados em pasta temporária.
- **`openssl` ausente na máquina de quem rodar** — mitigação: o script procura `openssl` no PATH e, no Windows, em `C:\Program Files\Git\usr\bin`. O README informa que o Git for Windows o inclui e mostra como instalar nos outros sistemas. Não versiono as chaves, porque o RNF-02 proíbe.
- **Chave privada vazando** — mitigação: `certs/` no `.gitignore` (já existem `*.key` e `*.pem`), e conferência com `git check-ignore` nos checks.
- **Janela travar ou quebrar por exceção na thread** — mitigação: a thread captura toda exceção de rede e devolve à fila uma mensagem tratada. A janela nunca chama a rede.
- **Cliente lento ou mal-intencionado prendendo threads** — mitigação: timeout de 5 s, limite de 64 KiB por linha e bind em `127.0.0.1`.
- **Tk 9.0 com Python 3.15 e fonte pequena no vídeo** — mitigação: fonte nomeada de 12 pt ou mais para todos os widgets (RNF-05) e verificação visual com captura de tela. Uma captura vira evidência do relatório.
- **Aniversário em 29 de fevereiro** — mitigação: a comparação `(mês, dia)` trata o dia 29/02 como anterior a 01/03 em ano não bissexto, e há teste dedicado.
- **Nomes fictícios coincidirem com pessoas reais** — mitigação: o README e a faixa da interface dizem que são dados fictícios.

## Estratégia de teste

- **Comandos do projeto:** não há `CLAUDE.md`, `package.json` ou `.claude/quality.json`. Os comandos desta spec são:
  - Testes: `python -m unittest discover -s tests -v`
  - Sintaxe (build): `python -m compileall -q consulta scripts tests`
  - Lint: nenhum configurado, e não vou instalar linter. Os dois comandos acima são a barreira.
  - Segredo fora do git: `git check-ignore certs/servidor.key certs/ca.key`
- **Unidade:** `test_dominio.py` (normalização com acento e maiúsculas, `anos_completos` em aniversário no dia, véspera e 29/02, busca com e sem município), `test_base.py` (base válida, e campos ou datas inválidos recusados), `test_protocolo.py` (linha válida, não-JSON, grande demais).
- **Integração com TLS real:** `test_integracao_tls.py` gera CA e certificado em pasta temporária (usa o mesmo `gerar_certificados.py`), sobe o servidor em porta livre numa thread e chama pelo `ClienteRede`. Casos: as três operações, os quatro códigos de erro, duas consultas simultâneas, servidor com certificado de **outra CA** (o cliente recusa), servidor parado (erro tratado), busca abaixo de 1 s. Pula (`skip`) com mensagem clara se o `openssl` não existir.
- **Interface:** `test_interface.py` monta a janela com cliente falso e verifica lista, ficha, mensagem de "nenhum resultado", mensagem de erro de rede, faixa "dados fictícios" e fonte de pelo menos 12 pt. Pula se não houver ambiente gráfico. Complementa com verificação manual e captura de tela (a evidência vai para o relatório). Playwright não se aplica a Tkinter.
- **Gerador:** `test_gerar_base.py` roda o gerador duas vezes e compara os resultados byte a byte, depois valida a base com `base.py` (RF-01).
- **Dependências:** `test_sem_dependencias_externas.py` percorre os imports de `consulta/` e `scripts/` com `ast` e confere cada um contra `sys.stdlib_module_names` (RNF-04).

## Revisão 2026-11-18: nomes, solicitações e decisão

Cobre RF-01 (revisado), RF-15 a RF-18 e RNF-07 do PRD. O resto do documento continua valendo, com as exceções listadas aqui: **a base de servidores segue somente leitura, mas o servidor passa a ter um estado que muda (as decisões), guardado em arquivo.**

### Componentes tocados

| Camada | Arquivo / módulo | Mudança |
|---|---|---|
| Dados | `scripts/gerar_base.py` | Listas de 25 nomes masculinos e 25 femininos (do `nomes-comuns.txt`, embutidas no script: o arquivo tem numeração e "Sofia / Sophia", e ler texto livre seria mais frágil que uma lista no código). Cada nome é usado uma vez, embaralhado com a semente fixa entre os 50 lugares. Dois sobrenomes diferentes sorteados dos 14 atuais. O sexo vem da lista do nome. O gerador repete o embaralhamento (mesma semente, determinístico) até Antônio e Antônia ficarem em municípios diferentes, e Francisco e Francisca também. |
| Dados | `data/servidores.json` | Regenerado. O `joana` deixa de existir; o README passa a usar `maria`. |
| Estado | `consulta/solicitacoes.py` (novo) | `Solicitacoes`: carrega ou sorteia `data/solicitacoes.json`, lista, obtém e decide. Um `threading.Lock` protege a decisão e a gravação. |
| Domínio | `consulta/dominio.py` | `montar_documento(servidor, solicitacao)`; `montar_ficha` ganha o campo `situacao_solicitacao`. |
| Protocolo | `consulta/protocolo.py`, `servidor.py` | Operações `solicitacoes`, `documento` e `decidir`. Opção `--solicitacoes` (caminho do arquivo, padrão `data/solicitacoes.json`). |
| Cliente (rede) | `consulta/cliente.py` | Métodos `solicitacoes`, `documento` e `decidir`. |
| Cliente (UI) | `consulta/interface.py` | `ttk.Notebook` com as abas "Consulta" (a janela atual, sem mudar de comportamento) e "Solicitações" (lista, documento e botões). A ficha ganha a linha "Situação da solicitação". |
| Infra | `.gitignore`, `README.md` | `data/solicitacoes.json` ignorado; README explica como zerar as decisões (apagar o arquivo). |

### Modelo de dados

`data/solicitacoes.json`, criado pelo servidor na primeira execução e **não versionado** (é estado, e mudaria a cada decisão):

```json
{
  "ficticio": true,
  "solicitacoes": [
    {"id": 1, "numero": "REQ-2026-0001", "servidor_id": 17, "municipio": "Anápolis", "situacao": "pendente", "decidida_em": null}
  ]
}
```

- `situacao`: `pendente`, `aprovada` ou `desaprovada`. `decidida_em`: data e hora da última decisão (`AAAA-MM-DDTHH:MM:SS`), ou `null`.
- **Sorteio:** `random.SystemRandom` (não reproduzível, de propósito, pois o pedido é sortear), uma vez só. São 10 solicitações, **uma por município**, com o servidor sorteado entre os 5 do município. A ordem de numeração também é sorteada. Isso cumpre "permutado entre municípios e servidores" sem repetir município.
- **Validação ao carregar:** `id` único, `servidor_id` existente na base e com o mesmo `municipio` gravado, `situacao` válida, `decidida_em` coerente. Se inválido, o servidor não sobe e diz o motivo. Arquivo apagado = novo sorteio.
- **Migração e reversão:** não há dado existente a migrar. `data/servidores.json` é regenerado (versionado, então reversível pelo git) e `data/solicitacoes.json` é novo, criado ao subir o servidor. **Regenerar a base depois de gravar as solicitações faria elas apontarem para outros servidores.** Por isso cada solicitação guarda também o `municipio`, e o servidor recusa subir se ele não bater com o do `servidor_id` (a validação acima). Ao regenerar a base, apague `data/solicitacoes.json`; o README avisa.
- **Gravação (RNF-07):** com o lock, grava em arquivo temporário na mesma pasta e troca com `os.replace`. Se a gravação falhar, a situação em memória não muda e o cliente recebe `ERRO_INTERNO`.

### Contratos de API (novos)

| `op` | Entrada | Resposta de sucesso |
|---|---|---|
| `solicitacoes` | — | lista ordenada por número: `{"id", "numero", "servidor_nome", "municipio", "situacao"}` |
| `documento` | `id` (inteiro) | `{"id", "numero", "situacao", "decidida_em", "municipio", "orgao", "servidor_nome", "sexo", "data_ingresso", "data_solicitacao"}` |
| `decidir` | `id` (inteiro) e `decisao` (`aprovada` ou `desaprovada`) | o mesmo objeto de `documento`, já atualizado |

- `ficha` ganha `situacao_solicitacao`: `null` (servidor sem solicitação) ou a situação.
- Erros: `id` ou `decisao` inválidos dão `REQUISICAO_INVALIDA`; solicitação inexistente dá `NAO_ENCONTRADO`. O `documento` **não leva** a data de nascimento, a idade, o tempo de contribuição, PCD, doença nem remuneração: esses dados o analista confere na aba "Consulta" (é o que o vídeo mostra). Nenhum campo indica elegibilidade (RF-09).
- O log registra `op=decidir resultado=ok`, sem nome de servidor.

### Decisões

- **Um estado só, no servidor.** O cliente não guarda nada: a situação vem sempre do servidor, então é a mesma em qualquer janela e depois de reiniciar.
- **Arquivo JSON e não banco**, pelo mesmo motivo da base (RNF-04). A escrita atômica evita arquivo pela metade.
- **Texto do documento montado no cliente**, a partir dos campos recebidos (modelo de ofício com concordância de gênero, "o servidor" ou "a servidora", pelo campo `sexo`). O servidor entrega dados, não layout. Modelo: "Requerimento de aposentadoria nº …, ao Setor de Pessoal da Prefeitura Municipal de …, o servidor … lotado em …, ingressado em …, requer a concessão de aposentadoria voluntária e a análise do ato pelo TCM-GO. Nestes termos, pede deferimento", com local, data da solicitação e assinatura. Rodapé: "Documento fictício, para demonstração".
- **Decisão reversível.** Aprovar e Desaprovar ficam sempre ativos e a última vale, para poder gravar o vídeo mais de uma vez. Zerar tudo é apagar o arquivo.
- **Sem confirmação em diálogo** ao decidir, para a demonstração fluir.
- **Sem autenticação** em `decidir`: qualquer cliente que confie na CA decide. Registrado como fora de escopo no PRD.
- **A aba Consulta não muda** de comportamento. Só entra num `Notebook`, e ganha uma linha na ficha.

### Riscos

- **Refatorar a janela para abas pode quebrar os 26 testes da interface.** Mitigação: a task 15 só move o conteúdo atual para a primeira aba e roda os testes antes de acrescentar a segunda.
- **Mudar a base quebra testes e documentação que citam nomes** (`joana`, as capturas do resumo). Mitigação: a task 13 troca as referências e roda tudo; os testes com base própria não são afetados.
- **Duas decisões ao mesmo tempo.** Mitigação: lock e teste de concorrência.
- **Arquivo corrompido à mão.** Mitigação: validação ao carregar e mensagem clara.
- **O sorteio não ser reproduzível** pode surpreender na demonstração. Mitigação: o arquivo gravado mantém os mesmos 10 documentos entre execuções, e o README diz como sortear de novo.

### Estratégia de teste

- `test_gerar_base.py`: 25 e 25, cada nome uma vez, sexo coerente, sobrenomes diferentes, mesmos bytes ao gerar duas vezes, Antônio e Antônia (e Francisco e Francisca) em municípios diferentes.
- `test_solicitacoes.py` (novo): 10 solicitações, uma por município, servidores distintos, todas pendentes; recarregar reutiliza; decidir grava e sobrevive ao recarregar; arquivo inválido recusado; decisões simultâneas sem perda; falha de gravação não muda a memória.
- `test_integracao_tls.py`: as três operações novas, os erros, o `documento` sem dados vedados, `ficha` com `situacao_solicitacao`, e reiniciar o servidor mantendo a decisão.
- `test_interface.py` (cliente falso): abas, lista, documento, concordância de gênero, botões, atualização de lista e ficha após decidir, erro de rede. Verificação manual e captura de tela do fluxo completo.
- Estado fora do git: `git check-ignore data/solicitacoes.json`.

## Revisão 2026-11-24: aba Regras

Cobre o RF-19. Revisão pequena: uma operação sem parâmetros e uma aba só de leitura.

### Componentes tocados

- `consulta/regras.py` (novo): o texto das regras como dado, uma lista de blocos `{"titulo", "linhas"}`, sem lógica.
- `consulta/servidor.py`: operação `regras` no despacho, que devolve esse dado.
- `consulta/cliente.py`: método `regras()`.
- `consulta/interface.py`: terceira aba "Regras" com um `Text` somente leitura (mesma fonte do documento, mínimo de 12 pt) e rodapé de aviso.

### Contratos de API (novos)

| `op` | Entrada | Resposta de sucesso |
|---|---|---|
| `regras` | — | lista de blocos `{"titulo": texto, "linhas": [texto, ...]}`, na ordem de exibição |

- Sem erro de entrada possível além dos gerais (`REQUISICAO_INVALIDA` para linha inválida). O log registra `op=regras resultado=ok`.
- A resposta é igual para todos e não depende da base nem das solicitações. Nenhum campo indica elegibilidade (RF-09).

### Decisões

- **Texto no servidor, em módulo próprio**, e não no `interface.py`: a fonte das regras fica num lugar só e a aba entra na demonstração cliente-servidor. Sem arquivo de configuração, porque o conteúdo é fixo.
- **Só apresentação.** Não há cálculo contra a ficha: aplicar as regras a um servidor seria indicar elegibilidade, o que o RF-09 proíbe e o analista decide.
- **Carregamento na primeira abertura**, com nova tentativa se a rede falhou (o texto não muda, então não recarrega a cada abertura).
- O rodapé avisa que o texto é simplificado e não substitui a legislação.

### Riscos

- **Conteúdo jurídico simplificado** pode ser lido como oficial. Mitigação: aviso no rodapé e no RF-19; texto fornecido pelo estudante.
- **A lista de abas muda de duas para três**, e há teste que confere os nomes. Mitigação: atualizar esse teste junto.

### Estratégia de teste

- `test_regras.py` (novo): três blocos com os valores do RF-19, sem campo de elegibilidade.
- `test_integracao_tls.py`: a operação `regras` pelo canal TLS e no log.
- `test_interface.py`: três abas na ordem, texto exibido e somente leitura, fonte mínima, rodapé, falha de rede com nova tentativa.

## Revisão 2026-11-25: login e reverificação ao decidir

Cobre RF-20, RF-21 e RNF-08. Um usuário só, sem sessão no servidor.

### Componentes tocados

- `consulta/credenciais.py` (novo, só o servidor usa): `carregar_env`, `gerar_hash` e `Credenciais.verificar`.
- `scripts/gerar_hash.py` (novo): pede a senha sem eco (`getpass`) e imprime a linha `SENHA_HASH=...` para o `.env`.
- `consulta/protocolo.py`: código `CREDENCIAIS_INVALIDAS`.
- `consulta/servidor.py`: operação `login`; `decidir` passa a exigir `usuario` e `senha`; opção `--env`; recusa subir sem `.env` válido.
- `consulta/cliente.py`: `login`, `decidir` com credencial e `CredenciaisInvalidas(ErroDeRede)`.
- `consulta/interface.py`: diálogo de credenciais (login e confirmação), com senha mascarada; `JanelaConsulta(raiz, cliente, usuario=None)`.
- `.gitignore` (`.env`), `.env.example`, `README.md`.

### Contratos de API (novos e alterados)

| `op` | Entrada | Resposta de sucesso |
|---|---|---|
| `login` (novo) | `usuario` e `senha` (textos de até 100 caracteres) | `{"usuario": nome}` |
| `decidir` (alterado) | `id`, `decisao`, **`usuario`, `senha`** | documento atualizado, como antes |

- Credencial errada, de qualquer tipo, dá `CREDENCIAIS_INVALIDAS` com a mesma mensagem ("Usuário ou senha inválidos."), depois de 1 s de pausa. Campo ausente ou que não é texto, ou maior que 100 caracteres, dá `REQUISICAO_INVALIDA`.
- A credencial é conferida **antes** de id e decisão: quem não se autentica não descobre se um id existe.
- O log registra `op=login resultado=ok` ou `erro:CREDENCIAIS_INVALIDAS`, sem usuário nem senha.

### Decisões

- **Hash scrypt da biblioteca padrão** (`hashlib.scrypt`, n=2^14, r=8, p=1, sal de 16 bytes), no formato `scrypt$<sal hex>$<hash hex>`. Sem dependência nova (RNF-04). Texto puro no `.env` foi descartado por entregar a senha a quem lê o arquivo; desafio e resposta, porque o TLS já protege o trânsito.
- **Comparação em tempo constante e sempre com scrypt**, mesmo com usuário errado, para o tempo de resposta não revelar se o usuário existe.
- **Sem sessão.** O login ao abrir só libera a janela; cada decisão carrega a credencial e o servidor valida de novo. Não há token para vazar ou expirar.
- **Pausa de 1 s na falha** (`atraso_falha_s`, 0 nos testes) trava força bruta sem estado. Cabe no limite de 5 s do cliente.
- **Consultas sem credencial no servidor.** Quem falar com o servidor sem a janela consegue listar, mas não decidir. Fica registrado como limitação no relatório; o token de sessão resolveria, ao custo de estado e expiração.
- **`.env` com parser mínimo** (`CHAVE=valor`, `#` comenta). `--env` troca o caminho.

### Riscos

- **Senha esquecida ou `.env` perdido:** gera-se outro hash com `scripts/gerar_hash.py`. O README explica.
- **Testes de interface** passam a abrir diálogo ao decidir. Mitigação: `usuario` informado nos testes e ajuste do passo de decidir.
- **scrypt custa ~50 ms por tentativa.** Aceitável aqui; sobrecarga por tentativa é desejável.

### Estratégia de teste

- `test_credenciais.py` (novo): hash com sal diferente a cada vez, verificação certa e errada, usuário errado, `.env` com comentários e sem a chave.
- `test_integracao_tls.py`: `login` certo e errado (mesma mensagem, código `CREDENCIAIS_INVALIDAS`), `decidir` sem credencial, com senha errada (nada grava) e com a certa; pausa na falha; log sem segredo.
- `test_interface.py`: login libera a janela, falha mantém o diálogo, Cancelar encerra, senha mascarada; Aprovar e Desaprovar pedem a senha, senha errada não grava.

## Rastreio

| RF | Componentes | Como testar |
|---|---|---|
| RF-01 | `scripts/gerar_base.py`, `data/servidores.json`, `base.py` | gerador duas vezes dá o mesmo arquivo; a base tem 10 municípios e 50 servidores e passa na validação |
| RF-02 | `dominio.montar_ficha`, operação `ficha`, painel da ficha em `interface.py` | teste de integração da operação `ficha` com todos os campos; teste da janela com os rótulos exibidos |
| RF-03 | `dominio.normalizar`, `dominio.buscar`, operação `buscar` | testes de unidade com acento, maiúsculas e trecho; integração da operação |
| RF-04 | `dominio.buscar`, operações `municipios` e `buscar`, `Combobox` da interface | unidade com e sem município; integração; `municipio` inválido dá `REQUISICAO_INVALIDA` |
| RF-05 | operação `buscar`, `Treeview` e seleção em `interface.py` | teste da janela: busca preenche a lista e selecionar item pede a ficha |
| RF-06 | `interface.py` | teste da janela com resposta vazia mostra "nenhum resultado" |
| RF-07 | `dominio.anos_completos`, `montar_ficha` | unidade: datas de borda e `tempo_contribuicao_anos` esperado |
| RF-08 | `dominio.anos_completos`, `montar_ficha` | unidade: idade até a data da solicitação, aniversário no dia, véspera e 29/02 |
| RF-09 | `montar_ficha`, `interface.py` | a ficha não tem campo de elegibilidade (teste da lista exata de campos) |
| RF-10 | `servidor.py`, `cliente.py`, `interface.py` | integração: cliente e servidor em processos/threads separados trocando mensagens; verificação manual com os dois programas |
| RF-11 | `servidor.py` (thread por conexão) | integração com duas consultas simultâneas, uma delas com cliente lento |
| RF-12 | `cliente.py`, fila e mensagens em `interface.py` | integração com servidor parado; teste da janela com erro de rede |
| RF-13 | `protocolo.py`, despacho em `servidor.py` | integração: linha inválida, `op` desconhecida e `id` inexistente; depois uma consulta normal ainda funciona |
| RF-14 | `scripts/gerar_certificados.py`, contextos TLS em `servidor.py` e `cliente.py` | integração: aperto de mão com a CA do projeto funciona; com certificado de outra CA o cliente recusa e a mensagem aparece |
| RNF-01 | `base.py`, `interface.py` | campo `ficticio` na base e faixa na janela (teste da janela) |
| RNF-02 | `.gitignore` | `git check-ignore` nas chaves de `certs/` |
| RNF-03 | `servidor.py`, `dominio.py` | integração mede a busca abaixo de 1 s |
| RNF-04 | todo o projeto, `README.md` | teste dos imports; seguir o README em pasta limpa |
| RNF-05 | `interface.py` | teste da janela confere a fonte ≥ 12 pt; captura de tela |
| RNF-06 | `scripts/gerar_certificados.py` | teste gera os certificados duas vezes em pastas temporárias e verifica com `openssl verify` |
| RP-03 a RP-05 | `docs/relatorio/`, `README.md`, roteiro do vídeo | conferência manual contra a lista do PRD (fora do código) |
| RP-01, RP-02, RP-06 | documentos e envios do estudante | acompanhados no checkpoint; não são tarefas de código |
| RF-01 (rev.) | `scripts/gerar_base.py`, `data/servidores.json` | testes do gerador (nomes, sexo, sobrenomes, determinismo, nomes parecidos em municípios diferentes) |
| RF-15 | `consulta/solicitacoes.py`, `data/solicitacoes.json` | `test_solicitacoes.py`: 10, uma por município, pendentes, reutilizadas ao reiniciar |
| RF-16 | operações `solicitacoes` e `documento`, aba "Solicitações" em `interface.py` | integração das operações; teste da janela com o documento e a concordância de gênero |
| RF-17 | operação `decidir`, botões em `interface.py` | integração e teste da janela: aprovar, desaprovar e trocar a decisão |
| RF-18 | `solicitacoes.py`, `montar_ficha`, lista, documento e ficha | integração reiniciando o servidor; teste da ficha com a situação |
| RNF-07 | `solicitacoes.py`, `.gitignore` | teste de concorrência, de arquivo inválido e de falha de gravação; `git check-ignore` |
| RF-19 | `regras.py`, operação `regras`, aba "Regras" | `test_regras.py`; integração da operação; teste da janela com as três abas |
| RF-20 | `credenciais.py`, operação `login`, diálogo de login em `interface.py` | integração com credencial certa e errada; teste da janela: libera, falha, cancela, senha mascarada |
| RF-21 | operação `decidir` autenticada, diálogo de confirmação | integração: sem senha, senha errada (não grava) e certa; teste da janela: Aprovar e Desaprovar pedem a senha |
| RNF-08 | `credenciais.py`, `scripts/gerar_hash.py`, `.gitignore`, `.env.example` | teste do hash; `git check-ignore .env`; teste de que o log não traz usuário nem senha |
