---
status: pendente
requisitos: [RNF-04]
depende: ["10", "11"]
---

# 12. README e execução em pasta limpa

**Objetivo:** quem receber o código consegue gerar os certificados, subir o servidor e abrir a janela seguindo só o README, e o projeto só usa a biblioteca padrão do Python.

**Aceitação:** [12-readme-execucao.feature](12-readme-execucao.feature)

**Arquivos prováveis:** `README.md`, `tests/test_sem_dependencias_externas.py`.

**Fora de escopo:** relatório e roteiro do vídeo (requisitos de processo RP-03 e RP-05).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- `git check-ignore certs/servidor.key certs/ca.key`
- Manual: clonar o repositório em uma pasta nova e seguir o README até a janela abrir.
