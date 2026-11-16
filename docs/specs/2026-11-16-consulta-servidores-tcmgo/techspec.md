# TechSpec: Consulta de servidores municipais (TCM-GO)

- **Data:** 2026-11-16
- **PRD:** [prd.md](prd.md)
- **Status:** aprovado (2026-11-16)

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
- **Chaves RSA 3072**, validade de 3 anos para a CA e 1 ano para o servidor. O material cita RSA, e o tamanho é folgado e rápido de gerar.
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
