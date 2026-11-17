"""Cliente de rede: uma requisição TLS por chamada, confiando só na CA do projeto."""

import socket
import ssl
from pathlib import Path

from consulta import protocolo

RAIZ = Path(__file__).resolve().parent.parent
CA_PADRAO = RAIZ / "certs" / "ca.crt"
HOST_PADRAO = "127.0.0.1"
PORTA_PADRAO = 8443
TIMEOUT_S = 5
CONEXAO_INTERROMPIDA = "A conexão com o servidor foi interrompida. Tente buscar de novo."
_ERRO_NOME_DIFERENTE = 62  # X509_V_ERR_HOSTNAME_MISMATCH do OpenSSL


class ErroDeRede(Exception):
    """Falha de comunicação; `str(erro)` é uma mensagem pronta para mostrar ao usuário."""


class ClienteRede:
    def __init__(self, host=HOST_PADRAO, porta=PORTA_PADRAO, ca=CA_PADRAO):
        self._host = host
        self._porta = porta
        self._ca = Path(ca)

    def consultar(self, requisicao: dict) -> dict:
        """Envia a requisição e devolve a resposta (dicionário). Falhas viram `ErroDeRede`."""
        contexto = self._criar_contexto()
        try:
            bruto = socket.create_connection((self._host, self._porta), timeout=TIMEOUT_S)
        except TimeoutError as erro:
            raise ErroDeRede("O servidor demorou demais para responder.") from erro
        except OSError as erro:
            raise ErroDeRede(
                "Não foi possível conectar ao servidor. Verifique se ele está em execução."
            ) from erro
        try:
            with bruto, contexto.wrap_socket(bruto, server_hostname=self._host) as seguro:
                protocolo.escrever_mensagem(seguro, requisicao)
                with seguro.makefile("rb") as arquivo:
                    return protocolo.ler_mensagem(arquivo)
        except ssl.SSLCertVerificationError as erro:
            if erro.verify_code == _ERRO_NOME_DIFERENTE:
                raise ErroDeRede(
                    f"O certificado do servidor não corresponde ao endereço '{self._host}'."
                ) from erro
            raise ErroDeRede(
                "Servidor não confiável: o certificado não foi emitido pela CA do projeto."
            ) from erro
        except (ssl.SSLEOFError, protocolo.ConexaoEncerrada) as erro:
            raise ErroDeRede(CONEXAO_INTERROMPIDA) from erro
        except ssl.SSLError as erro:
            raise ErroDeRede("Falha na conexão segura (TLS) com o servidor.") from erro
        except protocolo.ProtocoloErro as erro:
            raise ErroDeRede(f"Resposta inválida do servidor: {erro}.") from erro
        except TimeoutError as erro:
            raise ErroDeRede("O servidor demorou demais para responder.") from erro
        except OSError as erro:  # reset, pipe quebrado: a conexão existia e caiu
            raise ErroDeRede(CONEXAO_INTERROMPIDA) from erro

    def municipios(self) -> list:
        """Nomes dos municípios, em ordem alfabética."""
        return self._dados({"op": "municipios"})

    def buscar(self, nome: str, municipio: str | None = None) -> list:
        """Servidores (id, nome, município) cujo nome contém `nome`, opcionalmente num município."""
        return self._dados({"op": "buscar", "nome": nome, "municipio": municipio})

    def ficha(self, identificacao: int) -> dict:
        """Ficha do servidor, com idade e tempo de contribuição calculados pelo servidor."""
        return self._dados({"op": "ficha", "id": identificacao})

    def _dados(self, requisicao: dict):
        resposta = self.consultar(requisicao)
        if resposta.get("ok") is not True:
            raise ErroDeRede("O servidor não atendeu a consulta.")
        return resposta["dados"]

    def _criar_contexto(self) -> ssl.SSLContext:
        try:
            contexto = ssl.create_default_context(cafile=str(self._ca))
        except (OSError, ssl.SSLError) as erro:
            raise ErroDeRede(
                f"Certificado da CA ausente ou inválido em '{self._ca}'. "
                "Gere-o com: python scripts/gerar_certificados.py"
            ) from erro
        contexto.minimum_version = ssl.TLSVersion.TLSv1_2
        return contexto
