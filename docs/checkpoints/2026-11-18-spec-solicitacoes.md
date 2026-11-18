# Checkpoint: resumo do projeto e spec das solicitações (18/11/2026)

Complementa [2026-11-17-sistema-pronto.md](2026-11-17-sistema-pronto.md). Onde houver conflito, vale este.

## Progresso

- **Sistema das tasks 01 a 12 conferido de ponta a ponta:** 117 testes OK (1 pulado, POSIX), `compileall` sem erro, janela Tkinter aberta de verdade contra o servidor real por TLS 1.3. Isso fecha a pendência do checkpoint anterior ("janela aberta à mão").
- **Teste que falhava no Windows, corrigido:** `core.autocrlf=true` baixava `data/servidores.json` com CRLF e o teste compara byte a byte com o gerador. Criado `.gitattributes` (`data/servidores.json text eol=lf`) e a base regenerada. 117 testes OK de novo.
- **Resumo do projeto** em `docs/resumo/`: `resumo-do-projeto.html` (fonte), `img/` (7 capturas da janela real) e o PDF de 8 páginas (tomada de decisão, ferramentas, o que o sistema mostra, testes e passo a passo de teste visual). **O PDF não vai pelo git** (`*.pdf` está no `.gitignore`): para gerar de novo, rodar o Edge headless sobre o HTML (comando abaixo).
- **Spec revisada e aprovada pelo estudante** para três melhorias, com `check-spec` aprovado (2ª rodada):
  - RF-01 alterado (nomes), RF-02 e RF-09 ajustados, RF-15 a RF-18 e RNF-07 novos no PRD;
  - seção "Revisão 2026-11-18" no TechSpec;
  - tasks 13 a 16 (cada uma com `.feature`), todas `pendente`;
  - plano em `docs/plans/2026-11-18-solicitacoes-e-nomes.md`.
- **Nenhum código das tasks 13 a 16 foi escrito.**

## Decisões (do estudante, com o porquê)

- Sorteio das solicitações **uma vez, gravado em `data/solicitacoes.json`** e reutilizado até apagar o arquivo; assim os documentos e as decisões ficam iguais entre as execuções (e o vídeo pode ser regravado).
- Situação (Pendente, Aprovada, Desaprovada) **persistida no mesmo arquivo**, e exibida na lista, no documento e na ficha da aba Consulta.
- Processo: spec em fluxo curto (PRD, TechSpec, tasks, check-spec) e uma task por contexto.
- Decisões minhas, aceitas na aprovação: um documento por município (10 solicitações, servidor sorteado entre os 5); o documento **não** traz idade, tempo de contribuição, PCD, doença nem remuneração (o analista confere na aba Consulta, como no vídeo); decisão reversível (a última vale); sem confirmação em diálogo; sem autenticação (fora de escopo); listas de nomes embutidas no gerador, em vez de ler o `nomes-comuns.txt`; "Sofia / Sophia" vira "Sofia".
- Cada solicitação guarda também o `municipio`, e o servidor recusa subir se ele não bater com o do `servidor_id`. Ao regenerar a base, **apagar `data/solicitacoes.json`**.

## Próximos passos

1. Em outra máquina: `git clone` ou `git pull`, trocar para a branch deste checkpoint (ver "Como retomar") e ler este arquivo e o `tasks.md`.
2. `/clear` e executar, **uma por contexto**, com a skill `execute-task`: **task 13**, depois 14, 15 e 16 (nessa ordem). A task 16 é a maior; se estourar o contexto, dividir em "decidir e persistir" e "botões e situação na ficha".
3. A task 13 muda **toda** a base, então "joana" deixa de existir: o README passa a usar `maria`. Regenerar depois das tasks as capturas e o PDF do resumo (nomes mudam, e há uma aba nova).
4. Continuam valendo os prazos: **23/11, 23h59** (termos com a Juliana; fluxo no checkpoint `2026-11-16-prd-aprovado.md`), **antes de 26/11** (demonstração à Juliana, usando o passo a passo do resumo) e **07/12, 23h59** (relatório PDF de até 5 páginas, vídeo de até 10 minutos e envio nos dois campos da Plataforma A).

## Como retomar (outra máquina)

1. Pré-requisitos: Python 3.10+, Tkinter e `openssl` (no Windows, o do Git for Windows). Sem `pip install`.
2. Gerar os certificados (não vêm pelo git): `python scripts/gerar_certificados.py`.
3. Conferir o estado: `python -m unittest discover -s tests` deve dar OK (117 testes, 1 pulado) e `python -m compileall -q consulta scripts tests` sem erro.
4. Rodar: `python -m consulta.servidor` e, em outro terminal, `python -m consulta.interface`.
5. Gerar o PDF do resumo de novo (Windows, na pasta `docs/resumo`):
   ```
   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=resumo-do-projeto.pdf resumo-do-projeto.html
   ```
6. **Não vêm pelo git** (`.gitignore`): `certs/`, `dados-pessoais.local.md`, `documentos-preenchidos/` (Carta assinada e termos), os PDFs e DOCX das disciplinas e do resumo, e a memória local do Claude. Leve os documentos à mão.

## Referências

- Spec: `docs/specs/2026-11-16-consulta-servidores-tcmgo/` (`prd.md`, `techspec.md` com a seção "Revisão 2026-11-18", `tasks.md`, `tasks/13` a `16`, `check-spec.md`).
- Plano: `docs/plans/2026-11-18-solicitacoes-e-nomes.md`.
- Entrada da task 13: `nomes-comuns.txt` (25 nomes masculinos e 25 femininos, do estudante).
- Resumo: `docs/resumo/resumo-do-projeto.html` e `docs/resumo/img/`.
- Checkpoints anteriores: `2026-11-13-planejamento-inicial.md`, `2026-11-16-prd-aprovado.md`, `2026-11-17-sistema-pronto.md`.
- Pendência de decisão antiga resolvida: o `.feature` da task 12 manda buscar "maria", e agora a base terá uma Maria (task 13).
