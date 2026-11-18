# Checkpoint: sistema implementado (17/11/2026)

## Progresso

- As 12 tasks da spec `docs/specs/2026-11-16-consulta-servidores-tcmgo/` estão `feita`, e o PR #2 foi mergeado na `main`.
- Servidor TLS, cliente Tkinter, CA local, base fictícia e README estão prontos.
- Checks: `python -m unittest discover -s tests -v` (117 testes, OK, 1 pulado por ser POSIX) e `python -m compileall -q consulta scripts tests` (sem erro).
- A execução do README em pasta limpa foi conferida por script (certificados, servidor, busca, recusa com CA falsa).

## Decisões e desvios

- O `.feature` da task 12 manda buscar "maria", mas a base fictícia não tem esse nome. O README usa **"joana"** (2 resultados), com teste que garante resultado. O `.feature` não foi alterado, porque exigiria rodar o `check-spec` de novo. Decidir depois: ajustar o `.feature` ou incluir uma "Maria" na base (mexe na task 01).
- Ainda não conferido: a **janela Tkinter aberta à mão** seguindo o README (só os testes e o cliente de rede foram exercitados).

## Próximos passos

1. **Antes de 23/11, 23h59 (RP-01):** termos com a Juliana, no fluxo do checkpoint `2026-11-16-prd-aprovado.md` (enviar sem assinatura, ela preenche, o estudante assina de novo, ela assina). A Carta já está assinada.
2. **Antes de 26/11 (RP-02):** demonstração à Juliana e registro das considerações. Antes, abrir a janela de verdade, rodar o README e conferir os campos da ficha com ela.
3. **Até 07/12, 23h59:**
   - RP-03: relatório técnico em PDF (até 5 páginas, Arial 12, margens 2,5 e 3 cm). Usar capturas de tela da ficha (task 10).
   - RP-05: vídeo de até 10 minutos mostrando a comunicação cliente-servidor.
   - RP-06: enviar nos dois campos da Plataforma A.
   - Criar uma checklist própria para o relatório e o roteiro do vídeo.

## Como retomar em outra máquina

1. `git clone` do repositório (a `main` já tem tudo). Ler este checkpoint e o `README.md`.
2. Pré-requisitos: Python 3.10+, Tkinter e `openssl` (no Windows, o do Git for Windows). Sem `pip install`.
3. Rodar: `python scripts/gerar_certificados.py`, depois `python -m consulta.servidor` e, em outro terminal, `python -m consulta.interface`.
4. **Não vêm pelo git** (`.gitignore`): `certs/` (regenere pelo script), `dados-pessoais.local.md`, `documentos-preenchidos/` (Carta assinada e termos), os PDFs e DOCX das disciplinas e a memória local do Claude. Leve esses arquivos à mão.

## Referências

- Spec: `docs/specs/2026-11-16-consulta-servidores-tcmgo/` (PRD, TechSpec, tasks, check-spec).
- Checkpoints anteriores: `2026-11-13-planejamento-inicial.md` e `2026-11-16-prd-aprovado.md` (fluxo dos termos e prazos).
- PR mergeado: https://github.com/FhilipeRodrigues/projeto-integrador-iii-a/pull/2
