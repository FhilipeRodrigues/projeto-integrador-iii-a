# Checkpoint: capturas reais e resumo regenerados (24/11/2026)

Complementa [2026-11-23-task-16-feita.md](2026-11-23-task-16-feita.md). Onde houver conflito, vale este.

## Progresso

- Estudante confirmou: `main` atualizada e **termos enviados em 20/11** (RP-01 cumprido).
- **Capturas reais regeneradas** em `docs/resumo/img/` (11 imagens, janela real contra servidor real por TLS): inicial, lista "marc", ficha (Alice), acentos ("antonia"), sem resultado, filtro Formosa, aba Solicitações pendente, aprovada, desaprovada, ficha com a situação e CA falsa. As antigas "joana" e "fatima" foram removidas.
- Elas usaram um arquivo de solicitações temporário; `data/solicitacoes.json` não foi tocado (10 solicitações, todas Pendentes).
- **`resumo-do-projeto.html` atualizado** (nomes, seis operações, aba Solicitações, 191 testes, 18 RF / 7 RNF, passo a passo com 4 passos novos de solicitações, termos enviados) e **PDF regenerado: 11 páginas** (eram 8). Não é o relatório RP-03.
- Checks: `python -m unittest discover -s tests` com 191 testes OK (1 pulado) e `compileall` sem erro.

## Decisões

- Mantidas as anteriores. O PDF continua fora do git (`*.pdf` no `.gitignore`).
- As capturas saem de um script de captura (GDI via ctypes, sem dependências) que ficou só no scratchpad da sessão e não foi para o repositório.

## Pendências e observações

- **Teste instável:** na primeira rodada completa de hoje `test_interface.InterfaceErrosDeRedeTest.test_O_servidor_volta_ao_ar_e_os_municipios_aparecem` falhou; passou em 3 execuções isoladas e em outra rodada completa. Mesma família do flake já registrado (limite de 5 s em `JanelaBase.esperar` com carga na máquina). Se voltar, aumentar o limite.
- Nas capturas da aba Solicitações o documento ocupa as 17 linhas do campo e a assinatura fica na borda inferior, com barra de rolagem. É o comportamento real; avaliar se vale mais uma linha ou duas.
- **Alterações ainda não commitadas** (imagens, HTML, checkpoint e checklist). Commit só a pedido.

## Próximos passos

1. Commitar as capturas e o resumo (quando o estudante pedir).
2. **RP-02, antes de 26/11:** demonstração à Juliana pelo passo a passo do resumo (passos 2 a 12 e 16), registrando as considerações.
3. **Até 07/12 23h59:** relatório PDF (até 5 págs), vídeo (até 10 min) e envio, pela checklist.
