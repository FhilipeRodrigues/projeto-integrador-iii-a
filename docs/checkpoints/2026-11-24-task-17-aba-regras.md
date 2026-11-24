# Checkpoint: task 17 (aba Regras) feita (24/11/2026)

Complementa [2026-11-24-capturas-e-resumo.md](2026-11-24-capturas-e-resumo.md). Onde houver conflito, vale este.

## Progresso

- **Task 17 feita** (RF-19): operação `regras` no servidor, `regras()` no cliente e terceira aba "Regras" na janela, só para consulta. Plano em [../plans/2026-11-24-aba-regras.md](../plans/2026-11-24-aba-regras.md).
  - `consulta/regras.py` (texto em blocos, `listar()` devolve cópia), `consulta/servidor.py`, `consulta/cliente.py`, `consulta/interface.py` (`_montar_regras`, `_carregar_regras`, `_mostrar_regras`; `_ao_trocar_aba` ficou com um ramo por aba).
  - Spec: RF-19 no PRD, seção "Revisão 2026-11-24" no TechSpec, `tasks/17-aba-regras.md` e `.feature`, linha 17 no `tasks.md`.
  - Testes novos: `tests/test_regras.py` (6), `RegrasPelaRedeTest` (4) e `InterfaceAbaRegras*` (8). Suíte: **209 testes OK (1 pulado)** na última rodada, e `compileall` sem erro.
  - Captura real `docs/resumo/img/12-regras.png`; resumo (HTML e PDF), roteiro do vídeo e README atualizados.
- Estudante confirmou o escopo: **só consulta** (RF-09 vale, nada é calculado) e **o servidor envia o texto**.

## Decisões

- O rótulo da moldura da aba é "Regras básicas", sem a palavra "aposent...": o teste da ficha varre todos os textos da janela atrás dessa raiz (RF-09).
- O texto carrega na primeira abertura da aba e só repete o pedido se a rede falhou.
- Conteúdo é o do estudante, com rodapé: "Texto simplificado, de apoio à demonstração. Não substitui a legislação."

## Pendências

- **Não commitado.** Commit só a pedido.
- **Teste instável:** 2 de 4 rodadas completas de hoje tiveram uma falha "a janela não concluiu a consulta" (limite de 5 s do `JanelaBase.esperar`); a primeira foi em `InterfaceErrosDeRedeTest`, a outra não foi identificada. As rodadas seguintes passaram. O 5 s coincide com o `TIMEOUT_S` do cliente, então pode ser uma conexão que travou até o timeout (servidor reiniciando na mesma porta). Investigar se voltar.
- ~~RSA 3072 no `techspec.md`~~: resolvido em 24/11. Fica **RSA 2048** (e 825 dias de validade, também diferente do TechSpec); o TechSpec foi ajustado e os certificados não foram regerados.
- Ensaio do fluxo com a janela e demonstração à Juliana (RP-02, antes de 26/11).
