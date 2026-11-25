---
status: feita
requisitos: [RF-12, RF-20, RF-21, RNF-08]
depende: ["16", "17"]
---

# 18. Login e reverificação ao decidir

**Objetivo:** a janela pede usuário e senha ao abrir (operação `login`) e pede a senha de novo ao aprovar ou desaprovar. O servidor guarda só o hash da senha (scrypt com sal, no `.env`) e valida a credencial antes de gravar a decisão. Sem sessão e sem token.

**Aceitação:** [18-login.feature](18-login.feature)

**Arquivos prováveis:** `consulta/credenciais.py` (novo), `consulta/protocolo.py`, `consulta/servidor.py`, `consulta/cliente.py`, `consulta/interface.py`, `scripts/gerar_hash.py` (novo), `tests/test_credenciais.py` (novo), `tests/test_integracao_tls.py`, `tests/test_interface.py`, `.gitignore`, `.env.example` (novo), `README.md`, `docs/resumo/*` e `docs/video/roteiro-video.md` (depois).

**Notas:** um único usuário, no `.env`. A credencial é conferida antes de id e decisão, com a mesma mensagem para qualquer falha e 1 s de pausa. As consultas não exigem credencial no servidor (limitação a registrar no relatório). Usuário e senha nunca vão para o log.

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- `git check-ignore .env`
- abrir servidor e janela de verdade, entrar, decidir com a senha certa e com a errada, e tirar capturas de tela
