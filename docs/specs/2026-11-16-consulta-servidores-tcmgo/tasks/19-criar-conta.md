---
status: feita
requisitos: [RF-22, RNF-08]
depende: ["18"]
---

# 19. Criar conta pela janela

**Objetivo:** a tela de login ganha o botão "Criar conta" (usuário, senha e repetição da senha). O servidor valida as regras, gera o hash (scrypt com sal) e grava o `.env` sozinho, desde que ainda não exista conta. Sem conta, o servidor sobe e o login falha como qualquer credencial errada.

**Aceitação:** [19-criar-conta.feature](19-criar-conta.feature)

**Arquivos prováveis:** `consulta/credenciais.py`, `consulta/protocolo.py`, `consulta/servidor.py`, `consulta/cliente.py`, `consulta/interface.py`, `tests/test_credenciais.py`, `tests/test_integracao_tls.py`, `tests/test_interface.py`, `README.md`, `.env.example`, `docs/resumo/*` e `docs/video/roteiro-video.md` (depois).

**Notas:** só cria se não houver conta; `.env` gravado por arquivo temporário e `os.replace`, sob trava. `.env` ausente ou com chaves vazias vale como "sem conta"; hash preenchido e malformado continua recusando o servidor. Usuário, senha e hash nunca vão para o log. Plano: `docs/plans/2026-11-25-criar-conta.md`.

**Validação:**
- `.venv/Scripts/python.exe -m unittest discover -s tests -v`
- `.venv/Scripts/python.exe -m compileall -q consulta scripts tests`
- `git check-ignore .env`
- servidor sem `.env` e janela de verdade: tentar entrar, criar a conta, senha errada, senha certa; reiniciar o servidor e entrar de novo; capturas de tela
