# language: pt
Funcionalidade: Execução a partir do README
  Para que o professor consiga rodar e avaliar o sistema
  Como avaliador do projeto
  Quero instruções que funcionem em uma pasta nova, sem instalar bibliotecas

  @RNF-04 @fluxo
  Cenário: Seguir o README em uma pasta limpa
    Dado o repositório clonado em uma pasta nova, sem as pastas "certs" e sem instalar nenhuma biblioteca
    Quando sigo os passos do README: gerar os certificados, iniciar o servidor e abrir o cliente
    Então a janela abre e uma busca por "maria" mostra resultados

  @RNF-04 @fluxo
  Cenário: O projeto usa só a biblioteca padrão do Python
    Quando examino as importações dos arquivos do sistema e dos scripts
    Então toda importação é de um módulo da biblioteca padrão ou do próprio projeto

  @RNF-04 @fluxo
  Cenário: O README informa o que é preciso ter instalado
    Quando leio a seção de pré-requisitos
    Então ela cita a versão mínima do Python, o Tkinter e o programa "openssl", com a indicação de onde obtê-lo

  @RNF-04 @fluxo
  Cenário: O README ensina a demonstrar a recusa de um servidor falso
    Quando leio a seção de demonstração de segurança
    Então ela explica como gerar um certificado de outra CA, subir o servidor com ele e ver o cliente recusar

  @RNF-04 @fluxo
  Cenário: O README avisa que os dados são fictícios
    Quando leio o README
    Então ele informa que a base é fictícia e que nomes podem coincidir com pessoas reais por acaso

  @RNF-04 @fluxo
  Cenário: O repositório não carrega segredos
    Quando listo os arquivos versionados
    Então não há chaves privadas nem certificados gerados
