"""Servidor TCP com TLS: uma thread por conexão, uma requisição por conexão.

Uso: python -m consulta.servidor [--host 127.0.0.1] [--porta 8443] [--certs certs]
"""

import argparse
import socket
import ssl
import sys
import threading
from datetime import datetime
from pathlib import Path

from consulta import base, dominio, protocolo

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CERTS_PADRAO = RAIZ / "certs"
BASE_PADRAO = RAIZ / "data" / "servidores.json"
HOST_PADRAO = "127.0.0.1"
PORTA_PADRAO = 8443
TIMEOUT_S = 5
OPERACOES = ("municipios",)

MENSAGEM_SEM_CERTIFICADOS = (
    "Certificados do servidor não encontrados ou inválidos em '{pasta}'. "
    "Gere-os com: python scripts/gerar_certificados.py"
)


class CertificadosAusentes(RuntimeError):
    """O servidor não tem como se identificar: faltam (ou estão inválidos) os certificados."""


def criar_contexto_tls(pasta_certs) -> ssl.SSLContext:
    pasta = Path(pasta_certs)
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        contexto.load_cert_chain(pasta / "servidor.crt", pasta / "servidor.key")
    except (OSError, ssl.SSLError) as erro:
        raise CertificadosAusentes(MENSAGEM_SEM_CERTIFICADOS.format(pasta=pasta)) from erro
    return contexto


def _registrar(mensagem: str) -> None:
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {mensagem}", flush=True)


class Servidor:
    def __init__(self, servidores, pasta_certs=PASTA_CERTS_PADRAO, host=HOST_PADRAO,
                 porta=PORTA_PADRAO, log=_registrar):
        self._servidores = servidores
        self._contexto = criar_contexto_tls(pasta_certs)
        self._host = host
        self._porta = porta
        self._log = log
        self._escuta = None
        self._parar = threading.Event()

    @property
    def porta(self) -> int:
        """Porta em que o servidor escuta (útil quando se pede a porta 0)."""
        return self._escuta.getsockname()[1]

    def iniciar(self) -> None:
        """Abre a porta e começa a aceitar conexões na fila do sistema."""
        self._escuta = socket.create_server((self._host, self._porta))
        self._escuta.settimeout(0.2)  # permite conferir o pedido de parada

    def servir(self) -> None:
        """Laço de `accept`: bloqueia até `parar()`."""
        while not self._parar.is_set():
            try:
                conexao, endereco = self._escuta.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            threading.Thread(target=self._atender, args=(conexao, endereco), daemon=True).start()
        self._escuta.close()

    def parar(self) -> None:
        self._parar.set()

    def _atender(self, conexao, endereco) -> None:
        origem = f"{endereco[0]}:{endereco[1]}"
        try:
            # O aperto de mão acontece aqui, na thread: cliente lento não trava o `accept`.
            conexao.settimeout(TIMEOUT_S)
            with self._contexto.wrap_socket(conexao, server_side=True) as seguro:
                tls = f"{seguro.version()} {seguro.cipher()[0]}"
                operacao, resposta = self._responder(seguro)
                if resposta is not None:
                    protocolo.escrever_mensagem(seguro, resposta)
                self._log(f"{origem} {tls} op={operacao} resultado={'ok' if resposta else 'erro'}")
        except (OSError, ssl.SSLError) as erro:
            self._log(f"{origem} op=? resultado=falha_de_conexao ({type(erro).__name__})")
        finally:
            conexao.close()  # idempotente; cobre o aperto de mão que não chegou a completar

    def _responder(self, seguro):
        """Lê a requisição e devolve (operação para o log, resposta ou None)."""
        try:
            requisicao = protocolo.ler_mensagem(seguro.makefile("rb"))
        except protocolo.ProtocoloErro:
            return "?", None
        operacao = requisicao.get("op")
        if operacao not in OPERACOES:
            return "?", None
        return operacao, {"ok": True, "dados": dominio.listar_municipios(self._servidores)}


def main(argumentos=None) -> int:
    analisador = argparse.ArgumentParser(description="Servidor de consulta de servidores (TLS).")
    analisador.add_argument("--host", default=HOST_PADRAO)
    analisador.add_argument("--porta", type=int, default=PORTA_PADRAO)
    analisador.add_argument("--certs", default=str(PASTA_CERTS_PADRAO), help="pasta dos certificados")
    opcoes = analisador.parse_args(argumentos)

    try:
        servidores = base.carregar(BASE_PADRAO)["servidores"]
        servidor = Servidor(servidores, opcoes.certs, opcoes.host, opcoes.porta)
        servidor.iniciar()
    except (base.BaseInvalida, CertificadosAusentes, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    print(f"Servidor no ar em {opcoes.host}:{servidor.porta} (Ctrl+C para encerrar)", flush=True)
    try:
        servidor.servir()
    except KeyboardInterrupt:
        servidor.parar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
