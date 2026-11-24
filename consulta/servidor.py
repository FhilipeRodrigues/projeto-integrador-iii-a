"""Servidor TCP com TLS: uma thread por conexão, uma requisição por conexão.

Uso: python -m consulta.servidor [--host 127.0.0.1] [--porta 8443] [--certs certs]
       [--solicitacoes data/solicitacoes.json]
"""

import argparse
import socket
import ssl
import sys
import threading
from datetime import datetime
from pathlib import Path

from consulta import base, dominio, protocolo, regras, solicitacoes

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CERTS_PADRAO = RAIZ / "certs"
BASE_PADRAO = RAIZ / "data" / "servidores.json"
SOLICITACOES_PADRAO = RAIZ / "data" / "solicitacoes.json"
HOST_PADRAO = "127.0.0.1"
PORTA_PADRAO = 8443
TIMEOUT_S = 5
TAMANHO_MAXIMO_NOME = 100

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


def _invalida(motivo: str) -> protocolo.ErroDeAtendimento:
    return protocolo.ErroDeAtendimento(protocolo.REQUISICAO_INVALIDA, f"Requisição inválida: {motivo}")


def _registrar(mensagem: str) -> None:
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {mensagem}", flush=True)


class Servidor:
    def __init__(self, servidores, pasta_certs=PASTA_CERTS_PADRAO, host=HOST_PADRAO,
                 porta=PORTA_PADRAO, log=_registrar, pedidos=None):
        self._servidores = servidores
        self._pedidos = pedidos if pedidos is not None else solicitacoes.Solicitacoes(servidores)
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
                protocolo.escrever_mensagem(seguro, resposta)
                resultado = "ok" if resposta["ok"] else f"erro:{resposta['erro']['codigo']}"
                self._log(f"{origem} {tls} op={operacao} resultado={resultado}")
        except (OSError, ssl.SSLError) as erro:
            self._log(f"{origem} op=? resultado=falha_de_conexao ({type(erro).__name__})")
        finally:
            conexao.close()  # idempotente; cobre o aperto de mão que não chegou a completar

    def _responder(self, seguro):
        """Lê a requisição e devolve (operação para o log, resposta de sucesso ou de erro).

        Todo erro vira resposta e afeta só esta conexão (RF-13). A operação só vai para o
        log depois de reconhecida, para que texto do cliente não entre no registro.
        """
        operacao = "?"
        try:
            with seguro.makefile("rb") as leitor:
                try:
                    requisicao = protocolo.ler_mensagem(leitor)
                except protocolo.ProtocoloErro as erro:
                    if isinstance(erro, protocolo.LinhaGrandeDemais):
                        protocolo.descartar_excesso(leitor)
                    raise protocolo.ErroDeAtendimento(
                        protocolo.REQUISICAO_INVALIDA, f"Requisição inválida: {erro}."
                    ) from erro
            tratar = self._tratar(requisicao.get("op"))
            operacao = requisicao["op"]
            return operacao, {"ok": True, "dados": tratar(requisicao)}
        except protocolo.ErroDeAtendimento as erro:
            return operacao, protocolo.resposta_erro(erro.codigo, erro.mensagem)
        except OSError:
            raise  # timeout ou canal rompido: não há a quem responder; _atender encerra a conexão
        except Exception as erro:  # a falha vai para o log; o cliente só vê a mensagem genérica
            self._log(f"op={operacao} falha_inesperada ({type(erro).__name__})")
            return operacao, protocolo.resposta_erro(
                protocolo.ERRO_INTERNO, "Erro interno do servidor. Tente novamente."
            )

    def _tratar(self, operacao):
        if not isinstance(operacao, str):
            raise protocolo.ErroDeAtendimento(
                protocolo.REQUISICAO_INVALIDA, "Requisição inválida: informe a operação em 'op'."
            )
        tratar = {
            "municipios": self._municipios,
            "buscar": self._buscar,
            "ficha": self._ficha,
            "solicitacoes": self._solicitacoes,
            "documento": self._documento,
            "decidir": self._decidir,
            "regras": self._regras,
        }.get(operacao)
        if tratar is None:
            raise protocolo.ErroDeAtendimento(protocolo.OPERACAO_DESCONHECIDA, "Operação desconhecida.")
        return tratar

    def _municipios(self, _requisicao):
        return dominio.listar_municipios(self._servidores)

    def _buscar(self, requisicao):
        nome, municipio = requisicao.get("nome"), requisicao.get("municipio")
        if not isinstance(nome, str):
            raise _invalida("informe o nome (texto) a buscar.")
        if len(nome) > TAMANHO_MAXIMO_NOME:
            raise _invalida(f"o nome deve ter no máximo {TAMANHO_MAXIMO_NOME} caracteres.")
        if municipio is not None and (
            not isinstance(municipio, str)
            or municipio not in dominio.listar_municipios(self._servidores)
        ):
            raise _invalida("município desconhecido.")
        return dominio.buscar(self._servidores, nome, municipio)

    def _ficha(self, requisicao):
        identificacao = requisicao.get("id")
        if type(identificacao) is not int:
            raise _invalida("informe a identificação (número inteiro) do servidor.")
        for servidor in self._servidores:
            if servidor["id"] == identificacao:
                return dominio.montar_ficha(servidor, self._pedidos.situacao_do_servidor(identificacao))
        raise protocolo.ErroDeAtendimento(protocolo.NAO_ENCONTRADO, "Servidor não encontrado.")

    def _solicitacoes(self, _requisicao):
        return self._pedidos.listar()

    def _regras(self, _requisicao):
        return regras.listar()

    def _documento(self, requisicao):
        solicitacao = self._pedidos.obter(self._identificacao_da_solicitacao(requisicao))
        return self._documento_de(solicitacao)

    def _decidir(self, requisicao):
        identificacao = self._identificacao_da_solicitacao(requisicao)
        decisao = requisicao.get("decisao")
        if decisao not in solicitacoes.DECISOES:  # também recusa o que não é texto
            raise _invalida("a decisão deve ser 'aprovada' ou 'desaprovada'.")
        try:
            solicitacao = self._pedidos.decidir(identificacao, decisao)
        except OSError as erro:  # o OSError de _responder é o do canal; este é o do arquivo
            self._log(f"op=decidir falha_ao_gravar ({type(erro).__name__})")
            raise protocolo.ErroDeAtendimento(
                protocolo.ERRO_INTERNO, "Não foi possível gravar a decisão. Tente novamente."
            ) from erro
        return self._documento_de(solicitacao)

    @staticmethod
    def _identificacao_da_solicitacao(requisicao) -> int:
        identificacao = requisicao.get("id")
        if type(identificacao) is not int:
            raise _invalida("informe a identificação (número inteiro) da solicitação.")
        return identificacao

    def _documento_de(self, solicitacao):
        if solicitacao is None:
            raise protocolo.ErroDeAtendimento(protocolo.NAO_ENCONTRADO, "Solicitação não encontrada.")
        servidor = next(s for s in self._servidores if s["id"] == solicitacao["servidor_id"])
        return dominio.montar_documento(servidor, solicitacao)


def main(argumentos=None) -> int:
    analisador = argparse.ArgumentParser(description="Servidor de consulta de servidores (TLS).")
    analisador.add_argument("--host", default=HOST_PADRAO)
    analisador.add_argument("--porta", type=int, default=PORTA_PADRAO)
    analisador.add_argument("--certs", default=str(PASTA_CERTS_PADRAO), help="pasta dos certificados")
    analisador.add_argument(
        "--solicitacoes", default=str(SOLICITACOES_PADRAO),
        help="arquivo das solicitações (criado se não existir)",
    )
    opcoes = analisador.parse_args(argumentos)

    try:
        servidores = base.carregar(BASE_PADRAO)["servidores"]
        pedidos = solicitacoes.Solicitacoes(servidores, opcoes.solicitacoes)
        servidor = Servidor(servidores, opcoes.certs, opcoes.host, opcoes.porta, pedidos=pedidos)
        servidor.iniciar()
    except (base.BaseInvalida, solicitacoes.SolicitacoesInvalidas, CertificadosAusentes, OSError) as erro:
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
