# Checkpoint: task 19 (criar conta pela janela) feita (25/11/2026)

Complementa [2026-11-25-login.md](2026-11-25-login.md). Onde houver conflito, vale este. Plano: [../plans/2026-11-25-criar-conta.md](../plans/2026-11-25-criar-conta.md).

## Progresso

- **Task 19 feita** (RF-22, RNF-08 ajustado), **sem commit ainda**. Spec: PRD, TechSpec (seção "Revisão 2026-11-25b" e rastreio), `tasks/19-criar-conta.md` e `.feature`, `tasks.md`.
- Código: `consulta/credenciais.py` (`Credenciais` pode nascer sem conta; `criar`, `configurada`, `ContaJaExiste`, `DadosDeContaInvalidos`; `.env` gravado por arquivo temporário e `os.replace`, sob trava), operação `criar_conta` e código `CONTA_JA_EXISTE` no servidor, `criar_conta` no cliente, botão "Criar conta" e campo "Repita a senha" em `DialogoCredenciais`. README e `.env.example` atualizados.
- Testes: **272 OK (1 pulado)**; `compileall` sem erro; `git check-ignore .env` confirma. Ensaio real (servidor em processo próprio, sem `.env`, janela Tk com cliente TLS): login sem conta falha, senhas diferentes barram, conta criada volta ao login com o usuário, senha errada falha (~1,3 s) e a certa entra com 50 servidores, segunda criação dá `CONTA_JA_EXISTE`, log sem usuário nem senha.

## Decisões

- O **servidor** gera o hash e grava o `.env` (a janela só envia a senha pelo TLS). Só cria se **não houver conta** (proteção mínima; troca de senha segue fora de escopo). Regras: usuário de 1 a 100 caracteres, imprimíveis e sem espaço nas pontas; senha de 4 a 100.
- `.env` ausente ou com valores vazios vale como "sem conta"; hash preenchido e malformado continua recusando o servidor (para não sobrescrever um arquivo corrompido sem aviso).
- Regras da conta só no servidor; a janela confere apenas campos vazios e senhas diferentes, e mostra a mensagem do servidor.

## Pendências

- **Commitar** (por caminho; sem `check-spec.md`) e abrir PR.
- **Seu `.env` atual tem uma conta**: para a demonstração de criação, pare o servidor, **apague o `.env`** e `data/solicitacoes.json`, e suba o servidor de novo.
- `check-spec.md` ainda não cobre as tasks 17, 18 e 19.
- Capturas reais (login sem conta, criar conta, login com senha errada), resumo (HTML e PDF), roteiro do vídeo (passo de criar conta) e README do vídeo.
- Ensaio do fluxo e demonstração à Juliana (RP-02); relatório e vídeo até 07/12.
- Limitação para o relatório: quem alcançar o servidor antes do analista cria a conta (servidor local, 127.0.0.1).
