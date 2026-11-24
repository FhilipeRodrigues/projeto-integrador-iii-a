# Checklist: relatório técnico (RP-03), vídeo (RP-05) e envio (RP-06)

Fechamento da pendência do `tasks.md` ("vale uma checklist própria para esses dois"). Prazo de tudo: **07/12/2026, 23h59**. Demonstração à Juliana (RP-02): **antes de 26/11**.

## 0. Antes de tudo

- [ ] Abrir a janela de verdade e rodar o fluxo do README (servidor + interface) com a base atual (nomes novos, aba Solicitações, aprovar/desaprovar).
- [x] Regenerar as capturas em `docs/resumo/img/` (nomes e aba Solicitações mudaram) e o PDF do resumo. Feito em 24/11, ver `2026-11-24-capturas-e-resumo.md`.
- [ ] Se `data/solicitacoes.json` estiver com decisões de teste, apagar antes de gravar vídeo ou capturas finais (o sorteio é regravado e a situação volta a Pendente).

## 1. Demonstração à Juliana (RP-02, antes de 26/11)

- [ ] Mostrar a aba Consulta (busca, lista, ficha com os campos que ela confere).
- [ ] Mostrar a aba Solicitações: lista de 10, documento formal, aprovar e desaprovar, situação na ficha.
- [ ] Registrar as considerações dela por escrito (data e o que pediu). Entram no relatório.

## 2. Relatório técnico (RP-03, PDF)

Formato: **até 5 páginas, Arial 12 pt, margens 2,5 cm e 3 cm** (conferir no enunciado qual lado usa cada margem).

- [ ] Conteúdo mínimo: problema e cliente (Juliana, TCM-GO), requisitos (RF/RNF do PRD), arquitetura cliente-servidor, protocolo e canal TLS com CA local, atendimento simultâneo, testes, resultado da demonstração.
- [ ] Capturas de tela: ficha (task 10), aba Solicitações (task 15) e decisão (task 16). Pequenas, para caber nas 5 páginas.
- [ ] Citar as considerações da Juliana e o que foi ajustado.
- [ ] Exportar em PDF e **contar as páginas** (não passar de 5).
- [ ] Revisar ortografia e se nenhum dado pessoal real aparece (a base é fictícia).

## 3. Vídeo (RP-05, até 10 minutos)

Deve mostrar a **comunicação cliente-servidor**.

- [ ] Roteiro (sugestão de tempo): 1 min contexto; 2 min arquitetura (cliente Tkinter, servidor, TLS, CA local); 4 min demonstração (busca, ficha, solicitações, aprovar/desaprovar); 2 min mostrando a comunicação (log do servidor, certificados, recusa com CA falsa, dois clientes simultâneos); 1 min fechamento.
- [ ] Ensaiar uma vez com cronômetro. Servidor e janela com a base e o `solicitacoes.json` limpos.
- [ ] Gravar com a tela legível (fonte da janela e do terminal grandes).
- [ ] Conferir duração (≤ 10 min), áudio e que nenhum dado pessoal ou chave privada (`certs/*.key`) aparece em tela.

## 4. Código (RP-04)

- [ ] `python -m unittest discover -s tests` OK e `python -m compileall -q consulta scripts tests` sem erro.
- [ ] README seguido em pasta limpa (clone novo, `python scripts/gerar_certificados.py`, servidor, interface).
- [ ] Confirmar que `certs/`, `dados-pessoais.local.md` e `documentos-preenchidos/` não foram para o git.

## 5. Envio (RP-06, Plataforma A, até 07/12 23h59)

- [ ] Enviar o relatório PDF e o vídeo (ou o link, conforme o campo) **nos dois campos da Plataforma A**, e o código conforme o enunciado.
- [ ] Mandar com folga (de véspera) e guardar o comprovante de envio.
