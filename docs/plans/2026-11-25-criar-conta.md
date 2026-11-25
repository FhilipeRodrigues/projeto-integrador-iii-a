# Plano: criar conta pela janela (task 19, RF-22)

Pedido do estudante em 25/11/2026, para dinamizar o vídeo: mostrar a tentativa de entrar **antes** de existir conta, criar a conta pela janela (sem rodar `gerar_hash` no terminal) e depois entrar com senha errada. Decisões: **tela de login com botão "Criar conta"** (a janela sempre abre pelo login), **só cria se ainda não houver conta**, processo **task 19 em fluxo curto**. O estudante disse que a criação passa uma vez só na apresentação; por isso a proteção contra troca de senha é só a mínima (recusar quando já há conta), sem tela de "trocar senha".

## Objetivo

O servidor pode subir sem `.env`. Sem conta, o login falha como qualquer credencial errada, e a janela oferece "Criar conta" (usuário, senha, repetir senha). O servidor gera o hash (scrypt, sal) e grava o `.env` sozinho. Com conta já existente, a criação é recusada.

## Desenho

- **`consulta/credenciais.py`:** `Credenciais` passa a poder nascer **sem conta** e a guardar o `caminho` do `.env`. Novos: `configurada`, `criar(usuario, senha)` (sob trava; recusa com `ContaJaExiste` se já há conta; valida usuário e senha; grava o `.env` por arquivo temporário + `os.replace`; só depois ativa a conta na memória). `verificar` sem conta roda o scrypt à toa e devolve falso (mesmo tempo, mesma mensagem). `do_env`: arquivo ausente, ou chaves ausentes/vazias, vira "sem conta"; hash preenchido mas malformado continua recusado (`CredenciaisAusentes`), para não permitir sobrescrever um `.env` corrompido sem perceber.
- **Servidor:** operação `criar_conta` (`usuario`, `senha`); código novo `CONTA_JA_EXISTE`. Falha ao gravar o `.env` vira `ERRO_INTERNO` com mensagem genérica. `main` não recusa mais subir sem `.env`: avisa "sem conta, crie pela janela". Usuário e senha nunca vão para o log.
- **Cliente:** `criar_conta(usuario, senha)`; `ContaJaExiste(ErroDeRede)`.
- **Janela:** `DialogoCredenciais` ganha `repetir_senha` (terceiro campo, confere as duas senhas) e `ao_criar_conta` (botão "Criar conta" só no login). Criar conta cancelado volta ao login; criada com sucesso volta ao login com o usuário preenchido e a instrução "Conta criada. Entre com ela."
- **Regras de conta (servidor confere; a janela confere antes para dar mensagem clara):** usuário de 1 a 100 caracteres, imprimíveis e sem espaço nas pontas; senha de 4 a 100 caracteres.
- **Reiniciar a demonstração:** parar o servidor, apagar `.env` e `data/solicitacoes.json`, subir o servidor.
- **Mantido:** `scripts/gerar_hash.py` (caminho manual continua valendo); consultas sem credencial no servidor (limitação já registrada).

## Passos

1. Spec: PRD (RF-22, RNF-08 e "Fora de escopo" ajustados), TechSpec (seção "Revisão 2026-11-25b"), `tasks/19-criar-conta.md` e `.feature`, `tasks.md`.
2. `credenciais.py` + testes (`tests/test_credenciais.py`).
3. Servidor (`criar_conta`, `main` sem recusar) + cliente + testes de integração (`tests/test_integracao_tls.py`).
4. Janela + testes (`tests/test_interface.py`).
5. README e `.env.example`.
6. Ensaio real (servidor sem `.env`, janela real): tentar entrar, criar, senha errada, senha certa; capturas.

## Arquivos afetados

`consulta/credenciais.py`, `consulta/protocolo.py`, `consulta/servidor.py`, `consulta/cliente.py`, `consulta/interface.py`, `tests/test_credenciais.py`, `tests/test_integracao_tls.py`, `tests/test_interface.py`, `README.md`, `.env.example`, `docs/specs/2026-11-16-consulta-servidores-tcmgo/*`, e depois `docs/resumo/*` e `docs/video/roteiro-video.md`.

## Validação

- `python -m unittest discover -s tests -v` e `python -m compileall -q consulta scripts tests` sem falhas nem warnings novos (usar `.venv/Scripts/python.exe`).
- Ensaio real: sem `.env`, o servidor sobe; login falha; criar conta grava o `.env` (com hash, sem a senha); reiniciar o servidor mantém a conta; segunda criação é recusada.
- O log não contém usuário nem senha. `git check-ignore .env` continua confirmando.
