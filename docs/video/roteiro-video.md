# Roteiro do vídeo (RP-05): até 10 min, alvo 9min30

Rascunho para o estudante gravar. O texto falado é uma sugestão: adapte para a sua voz. Os comandos foram testados em 24/11/2026 no Git Bash (servidor na porta de ensaio, resposta e log conferidos); o fluxo de login e criação de conta, em 25/11/2026, com servidor e janela reais.

O vídeo precisa mostrar a **aplicação, as funcionalidades e a comunicação cliente-servidor** (RP-05). O foco pedido é a **segurança da informação**: certificados, TLS e o que o sistema se recusa a fazer.

## Resumo de tempo

| Bloco | Tempo | Acumulado |
|---|---|---|
| 1. Contexto | 0:45 | 0:45 |
| 2. Arquitetura | 1:00 | 1:45 |
| 3. Login e funcionalidades (rápido) | 2:15 | 4:00 |
| 4. Certificados e CA | 1:45 | 5:45 |
| 5. TLS ao vivo | 1:30 | 7:15 |
| 6. O que não pode ser feito | 1:30 | 8:45 |
| 7. Fechamento | 0:45 | 9:30 |

## Antes de gravar

- [ ] Três janelas prontas: **T1** servidor (Git Bash, fonte grande), **T2** comandos (Git Bash) e a **janela do cliente**. Esconder o que não é do projeto (abas, notificações, e-mail).
- [ ] `data/solicitacoes.json` **e `.env`** apagados (parar o servidor, apagar, subir de novo): as 10 voltam Pendentes e não há conta, para criar no vídeo. O T1 mostra "Ainda não há conta: crie uma pela janela".
- [ ] Escolher o usuário e a senha que vai digitar (a senha aparece mascarada; não fale a senha em voz alta).
- [ ] Certificados já gerados. Gerar a pasta do servidor falso uma vez: `python scripts/gerar_certificados.py certs/falso`.
- [ ] **Nunca abrir, listar o conteúdo nem dar `cat` em `*.key`.** `ls certs` (só nomes) pode.
- [ ] Servidor falso preparado, mas **fora do ar**, para subir no bloco 6 em outra porta (9443).
- [ ] Ensaio com cronômetro. Se passar de 9min40, cortar do bloco 3.

## 1. Contexto (0:45)

**Na tela:** capa do resumo ou a janela do cliente com a faixa "Dados fictícios".

**Falar:**
- "Sou estudante de [curso], e este é o meu Projeto Integrador III-A. A instituição é o TCM-GO, onde trabalho na Secretaria de Atos de Pessoal."
- "O problema: para analisar uma aposentadoria, o analista consulta a situação funcional de servidores de vários municípios, hoje em fontes separadas."
- "O protótipo é um servidor que guarda uma base e uma janela cliente que consulta por rede. Os dados são **100% fictícios**: 10 municípios e 50 servidores, gerados por script."
- "O foco do vídeo é a segurança da comunicação."

## 2. Arquitetura (1:00)

**Na tela:** o diagrama da seção 2 do resumo (cliente, TLS, servidor, `servidores.json`) ou `ls consulta`.

**Falar:**
- "Python, só com a biblioteca padrão: `socket`, `ssl`, `threading` e Tkinter. Sem `pip install`."
- "Cada ação da janela vira **uma requisição**: o cliente conecta, manda uma linha JSON, recebe uma linha JSON e a conexão fecha."
- "O servidor atende **vários clientes ao mesmo tempo**, uma thread por conexão. Nove operações: municípios, buscar, ficha, solicitações, documento, decidir, regras, login e criar conta."
- "Toda a conversa passa por **TLS**, e o cliente só confia em servidor com certificado assinado pela **CA do projeto**."

## 3. Login e funcionalidades (2:15)

**Na tela:** T1 com o servidor no ar (`python -m consulta.servidor`) e a janela (`python -m consulta.interface`).

**Login (0:30):**
1. A janela abre só na tela **Entrar**. Digitar um usuário e uma senha e clicar Entrar: "Usuário ou senha inválidos." ("ainda não existe conta, e a mensagem não diz o que errou").
2. **Criar conta**: usuário, senha e repetição, mascaradas. Mostrar uma repetição diferente ("As senhas não conferem.") e depois confirmar. A janela volta ao login com "Conta criada. Entre com ela."
3. **Falar:** "A senha vai pelo TLS; o **servidor** gera um hash scrypt com sal e grava só o hash no `.env`, que fica fora do Git. A conta só pode ser criada uma vez."
4. Entrar com a **senha errada** (recusada, com pausa de 1 s) e depois com a certa: abre a janela.

**Roteiro de cliques (rápido):**
1. A janela **já abre com os 50 servidores listados** ("50 servidor(es) encontrado(s)"), sem clicar em nada. Depois buscar `antonia` (sem acento): acha "Antônia". Abrir a ficha e apontar idade e tempo de contribuição ("calculados no **servidor**, o cliente só apresenta").
2. Aba **Solicitações**: lista de 10, documento formal, **Aprovar** em uma e **Desaprovar** em outra. Cada clique **pede a senha de novo** ("o servidor confere a credencial antes de gravar; não há sessão"). A situação muda na lista e no documento.
3. Voltar à aba Consulta, abrir a ficha de um servidor decidido: campo "Situação da solicitação".
4. Aba **Regras**: regra geral, PCD (por tempo e por idade) e doença profissional. "O texto vem do **servidor**; a aba só consulta. O sistema **não diz** se o servidor pode se aposentar: quem decide é o analista."
5. Olhar o **log do servidor (T1)**: "uma linha por consulta, com a versão do TLS e a cifra"; o `login` errado aparece como `erro:CREDENCIAIS_INVALIDAS`, sem usuário nem senha.

## 4. Certificados e CA (1:45)

**Falar primeiro:** "Para o cliente ter certeza de que fala com o servidor certo, usei uma **Autoridade Certificadora local**. Ela assina o certificado do servidor, e o cliente só confia nela."

**Comandos (T2):**
```bash
ls certs
openssl x509 -in certs/ca.crt -noout -subject -issuer -dates -ext basicConstraints,keyUsage
openssl x509 -in certs/servidor.crt -noout -subject -issuer -ext subjectAltName,extendedKeyUsage,basicConstraints
openssl verify -CAfile certs/ca.crt certs/servidor.crt
```

**Apontar na saída:**
- **CA:** `subject` e `issuer` iguais (autoassinada, é a raiz), `CA:TRUE` crítico, uso `Certificate Sign`.
- **Servidor:** `issuer` é a CA, `CA:FALSE`, `TLS Web Server Authentication`, nome válido só para `localhost` e `127.0.0.1` (SAN).
- `openssl verify` -> `certs/servidor.crt: OK`. "A cadeia de confiança fecha."
- Chave RSA de 2048 bits e SHA-256 (se quiser citar).

**Falar também (as chaves):**
- "As **chaves privadas** da CA e do servidor são geradas por script (`scripts/gerar_certificados.py`) e **nunca vão para o repositório**."

```bash
git check-ignore -v certs/servidor.key certs/ca.key
git ls-files certs
```
- A primeira mostra as chaves ignoradas pelo `.gitignore`; a segunda não lista nada.

## 5. TLS ao vivo (1:30)

**Falar:** "Agora a prova de que a conexão é cifrada e autenticada."

**Comandos (T2), com o servidor real no ar na porta 8443:**
```bash
openssl s_client -CAfile certs/ca.crt -connect 127.0.0.1:8443 </dev/null 2>&1 | grep -E "Verification|Protocol  |Cipher"
```
Esperado: `Verification: OK`, `Protocol: TLSv1.3` e `Cipher: TLS_AES_256_GCM_SHA384`.

```bash
printf '{"op":"buscar","nome":"antonia"}\n' | openssl s_client -quiet -CAfile certs/ca.crt -connect 127.0.0.1:8443 2>/dev/null
```
Esperado: `{"ok": true, "dados": [{"id": 9, "nome": "Antônia Rodrigues Barbosa", "municipio": "Goiânia"}]}`.

**Falar:**
- "Aqui falo o protocolo na mão, sem a janela: uma linha JSON, uma linha de resposta. Por baixo, o **handshake TLS 1.3** verificou o certificado contra a CA."
- "Olhem o log do servidor (T1): versão, cifra e operação, e o resultado. **O conteúdo da ficha não aparece no log.**"
- "O servidor aceita no mínimo TLS 1.2, e o cliente também."

## 6. O que não pode ser feito (1:30)

Cada item mostra o sistema **recusando**. Falar o motivo em uma frase.

### 6.1 Servidor falso é recusado (0:30)
O servidor real continua no ar. Suba o falso em outra porta (T3) e abra um segundo cliente:
```bash
python -m consulta.servidor --certs certs/falso --porta 9443
python -m consulta.interface --porta 9443
```
Na segunda janela, buscar qualquer nome. Esperado: **"Servidor não confiável: o certificado não foi emitido pela CA do projeto."**, lista vazia.

**Falar:** "O servidor falso também usa TLS, mas o certificado dele foi assinado por **outra CA**. O aperto de mão falha **antes** de qualquer dado ser trocado. É isso que impede um servidor impostor de receber consultas." Mostrar a linha `falha_de_conexao (SSLError)` no log do falso. Encerrar o falso com Ctrl+C.

### 6.2 Sem TLS, nada responde (0:15)
```bash
python -c "import socket;s=socket.create_connection(('127.0.0.1',8443),3);s.sendall(b'{\"op\":\"buscar\",\"nome\":\"antonia\"}\n');s.settimeout(3)
try: print('resposta:',s.recv(200))
except Exception as e: print('erro',type(e).__name__)"
```
Esperado: `erro ConnectionResetError`. No log do servidor: `falha_de_conexao (SSLError)`.

**Falar:** "Quem tenta falar em texto puro não recebe nada. Não existe porta sem criptografia."

### 6.3 Pedido inválido não passa (0:25)
```bash
printf '{"op":"apagar"}\n' | openssl s_client -quiet -CAfile certs/ca.crt -connect 127.0.0.1:8443 2>/dev/null
printf '{"op":"decidir","id":1,"decisao":"aprovada","usuario":"x","senha":"y"}\n' | openssl s_client -quiet -CAfile certs/ca.crt -connect 127.0.0.1:8443 2>/dev/null
```
Esperado: `OPERACAO_DESCONHECIDA` e, depois de 1 s, `CREDENCIAIS_INVALIDAS` ("Usuário ou senha inválidos."): sem a credencial certa, o servidor nem olha o id e nada é gravado.

**Falar:** "O servidor **não confia na entrada do cliente**: valida operação, tipos, tamanho do nome (até 100 caracteres), tamanho da mensagem (64 KiB) e tempo limite de 5 s. Um pedido ruim recebe erro e **só afeta a própria conexão**. Erros internos viram uma mensagem genérica, sem expor detalhes."

### 6.4 O que o servidor nunca entrega (0:20)
**Na tela:** a ficha na janela e o campo de campos; opcionalmente o resumo da seção 5.

**Falar:**
- "A **data de nascimento** fica no servidor. Só a **idade** sai, calculada lá. É minimização de dados (LGPD)."
- "O sistema **não diz se o servidor pode se aposentar**. Quem decide é o analista; a ferramenta só apresenta os dados."
- "Chaves privadas, o `.env` com o hash da senha e o arquivo de estado das solicitações (`data/solicitacoes.json`) ficam **fora do Git**."
- "O servidor escuta só em `127.0.0.1`: não fica exposto na rede."
- "A base é fictícia, com aviso na tela, para não expor dado real."

## 7. Fechamento (0:45)

**Falar:**
- "Resumindo: **TLS 1.3** com **CA local**, cliente que só confia nessa CA, login com senha guardada como hash e conferida no servidor a cada decisão, validação de toda entrada, log sem conteúdo nem senha e dados mínimos."
- "**Limites que assumo:** um único usuário, sem perfis; as consultas só exigem login na janela, não no servidor; tudo roda local e a demonstração é em uma máquina. Perfis e sessão com token seriam o próximo passo."
- "Código, testes (272 passando) e instruções estão no repositório. Obrigado."

## Ligação com o material da disciplina

Pontos para citar no vídeo, conforme o conteúdo de Segurança da Informação (PDFs "Redes - políticas de segurança, criptografia, autenticação e certificados digitais" e "Segurança em Sistema Web I"):

| Conceito | Onde aparece no projeto |
|---|---|
| Criptografia em trânsito (TLS) | Handshake TLS 1.3, cifra AES-256-GCM (bloco 5) |
| Certificado digital e Autoridade Certificadora | CA local, certificado do servidor, cadeia verificada (bloco 4) |
| Autenticação do servidor | O cliente recusa certificado de outra CA (6.1) |
| Validação de entrada | Operação, tipos e tamanhos; resposta de erro (6.3) |
| Minimização de dados (LGPD) | Idade no lugar da data de nascimento; dados fictícios (6.4) |
| Gestão de segredos | Chaves fora do Git; `.gitignore` (bloco 4) |
| Registro seguro (log) | Log com versão, cifra e resultado, sem conteúdo das fichas (bloco 5) |

## Dicas de gravação

- Fonte do terminal em 18 pt ou mais e a janela do cliente a 12 pt (já é o padrão do cliente).
- Gravar por blocos e juntar depois: facilita refazer o 6.1 e o 6.2.
- Dizer em voz alta o que se espera ver **antes** de apertar Enter.
- Conferir no vídeo final: duração (≤ 10 min), áudio e que nenhuma chave privada ou dado pessoal real aparece.
