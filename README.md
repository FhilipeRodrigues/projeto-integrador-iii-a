# Consulta de servidores municipais (protótipo do PI III-A)

Protótipo cliente-servidor para consultar servidores de prefeituras de Goiás, como faria o TCM-GO. O **servidor** guarda a base e responde por um canal TLS. O **cliente** é uma janela Tkinter que busca servidores e mostra a ficha de cada um. O cliente só confia na CA local do projeto, então recusa um servidor com certificado de outra origem.

> **Os dados são fictícios.** A base (`data/servidores.json`) é gerada por script, com 10 municípios e 50 servidores. Os nomes são combinações aleatórias de nomes e sobrenomes comuns e **podem coincidir por acaso com pessoas reais**. Nenhum dado é de pessoa real.

## Pré-requisitos

Nada além do que está abaixo. O projeto usa **só a biblioteca padrão do Python** e não há `pip install`.

| Item | Versão | Observação |
|---|---|---|
| Python | 3.10 ou superior (testado na 3.15) | https://www.python.org/downloads/ |
| Tkinter | o que acompanha o Python | No Windows e no macOS vem junto. No Linux: `sudo apt install python3-tk` |
| `openssl` (programa) | 3.x | Só para gerar os certificados. Veja abaixo onde obter |

Onde obter o `openssl`:

- **Windows:** instale o [Git for Windows](https://git-scm.com), que o inclui. O script o procura em `C:\Program Files\Git\usr\bin`.
- **Linux:** `sudo apt install openssl`.
- **macOS:** `brew install openssl`.

Nos comandos abaixo, use `python3` no lugar de `python` se for o nome no seu sistema.

## Como executar

Rode tudo a partir da pasta do projeto. Use três terminais, ou um para os dois primeiros passos e outro para o cliente.

**1. Gerar os certificados** (uma vez; cria a pasta `certs/`):

```
python scripts/gerar_certificados.py
```

Isso cria a CA local e o certificado do servidor. As chaves privadas ficam só na sua máquina: `certs/` está no `.gitignore` e não vai para o repositório.

**2. Conta de login** (uma vez): não há nada a fazer agora. Sem o arquivo `.env`, o servidor sobe e avisa que ainda não há conta; você a cria pela janela, no passo 4 (botão **Criar conta**). O servidor gera o hash (scrypt com sal) e grava o `.env`, que não vai para o repositório e guarda só o **hash**, nunca a senha. Só se cria a conta uma vez: com o `.env` pronto, o servidor recusa uma segunda. Para refazer (por exemplo, para gravar o vídeo de novo), pare o servidor, apague o `.env` e suba o servidor outra vez.

Se preferir criar a conta à mão, rode `python -m scripts.gerar_hash`, copie `.env.example` para `.env`, escreva o `USUARIO=` que quiser e cole a linha `SENHA_HASH=...` que o script imprime. Um `.env` com hash preenchido, mas malformado, faz o servidor recusar subir e explicar o que corrigir.

**3. Iniciar o servidor** (deixe esse terminal aberto):

```
python -m consulta.servidor
```

Ele escuta em `127.0.0.1:8443`. Opções: `--host`, `--porta`, `--certs` (pasta dos certificados) e `--env` (caminho do `.env`). Se a porta estiver ocupada, use `--porta 9443` aqui e no cliente.

**4. Abrir o cliente** (em outro terminal):

```
python -m consulta.interface
```

Opções: `--host`, `--porta` e `--ca` (caminho do `ca.crt`). A janela abre pelo **login**. Na primeira vez, clique em **Criar conta**, informe usuário e senha (de 4 a 100 caracteres) duas vezes e confirme: a janela volta ao login com o usuário preenchido, e você entra com a senha criada. Qualquer outro usuário ou senha é recusado com "Usuário ou senha inválidos.", e o programa só mostra os dados depois de entrar. Então digite `maria` e clique em Buscar. A lista mostra os servidores com esse nome (1 na base fictícia). Escolha um para ver a ficha.

Na aba **Solicitações**, escolha um requerimento para ver o documento e clique em **Aprovar** ou **Desaprovar**. A janela pede a senha de novo e o **servidor** confere a credencial antes de gravar; com senha errada nada é gravado. A última decisão vale, e a situação aparece na lista, no documento e na ficha do servidor (aba Consulta).

A aba **Regras** mostra, só para consulta, as regras básicas de aposentadoria (regra geral, PCD e doença profissional ou acidente de trabalho). O texto vem do servidor e é simplificado: o sistema não calcula nem diz se um servidor atende.

**Limitação conhecida:** só a decisão é protegida no servidor. As consultas (busca, ficha, solicitações, regras) não exigem credencial: quem falasse com o servidor sem usar a janela conseguiria listá-las, mas não decidir. Um token de sessão fecharia isso, ao custo de estado e expiração no servidor, e ficou fora do protótipo.

**Zerar as decisões:** pare o servidor, apague `data/solicitacoes.json` e inicie o servidor de novo. Ele sorteia 10 solicitações novas, todas pendentes. A decisão fica nesse arquivo, por isso sobrevive a reiniciar o servidor.

## Demonstração de segurança: o cliente recusa um servidor falso

O cliente só aceita certificados assinados pela CA em `certs/ca.crt`. Para ver a recusa, suba um servidor com um certificado de **outra CA**:

1. Gere uma segunda CA e outro certificado, em outra pasta (dentro de `certs/`, que o git ignora):

   ```
   python scripts/gerar_certificados.py certs/falso
   ```

2. Pare o servidor verdadeiro (Ctrl+C) e suba o falso na mesma porta:

   ```
   python -m consulta.servidor --certs certs/falso
   ```

3. Abra o cliente normalmente (`python -m consulta.interface`) e faça uma busca. O aperto de mão TLS falha e a janela mostra "Servidor não confiável: o certificado não foi emitido pela CA do projeto." Nenhum dado é trocado.

Para voltar ao normal, pare o servidor falso e rode de novo o passo 3.

## Testes

```
python -m unittest discover -s tests -v
python -m compileall -q consulta scripts tests
```

Os testes de integração geram certificados em pasta temporária e sobem o servidor em porta livre. Sem o `openssl`, eles são pulados com uma mensagem. Os testes de janela são pulados se não houver ambiente gráfico.

## Estrutura

```
consulta/    servidor, cliente de rede, protocolo, regras e janela
scripts/     gerar_base.py (reproduz a base), gerar_certificados.py e gerar_hash.py (login)
data/        servidores.json (base fictícia) e solicitacoes.json (criado pelo servidor)
tests/       testes automatizados
docs/        PRD, TechSpec, tasks e checkpoints
```

Para regenerar a base fictícia: `python scripts/gerar_base.py` (semente fixa, mesmo resultado na mesma versão do Python).
