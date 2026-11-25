"""Credencial do analista: usuário e hash da senha, guardados no `.env` (RNF-08, RF-22).

O hash é `scrypt$<sal hex>$<hash hex>`, da biblioteca padrão. A senha em si nunca é guardada.
A conta pode ainda não existir: ela é criada uma única vez, por `Credenciais.criar`.
"""

import hashlib
import hmac
import os
import secrets
import threading
from pathlib import Path

ESQUEMA = "scrypt"
CUSTO_N, BLOCO_R, PARALELISMO_P = 2**14, 8, 1
TAMANHO_SAL = 16
TAMANHO_MAXIMO = 100  # usuário e senha; limita o trabalho que um pedido pode causar
TAMANHO_MINIMO_SENHA = 4
CHAVE_USUARIO = "USUARIO"
CHAVE_HASH = "SENHA_HASH"
_SAL_SEM_CONTA = bytes(TAMANHO_SAL)

MENSAGEM_ENV_INVALIDO = (
    "Configuração de login inválida em '{caminho}'. Corrija USUARIO e SENHA_HASH "
    "(modelo em .env.example; a linha do hash sai de: python -m scripts.gerar_hash) "
    "ou apague o arquivo para criar a conta pela janela."
)


class CredenciaisAusentes(RuntimeError):
    """O `.env` existe, mas não traz um usuário e um hash válidos."""


class ContaJaExiste(RuntimeError):
    """Só se cria a conta uma vez; trocar a senha está fora de escopo."""


class DadosDeContaInvalidos(ValueError):
    """Usuário ou senha fora das regras; `str(erro)` explica qual regra."""


def _derivar(senha: str, sal: bytes) -> bytes:
    return hashlib.scrypt(
        senha.encode("utf-8"), salt=sal, n=CUSTO_N, r=BLOCO_R, p=PARALELISMO_P, dklen=32
    )


def gerar_hash(senha: str) -> str:
    sal = secrets.token_bytes(TAMANHO_SAL)
    return f"{ESQUEMA}${sal.hex()}${_derivar(senha, sal).hex()}"


def carregar_env(caminho) -> dict:
    """Lê linhas `CHAVE=valor`; ignora linhas em branco e comentários (`#`)."""
    valores = {}
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valores[chave.strip()] = valor.strip()
    return valores


def validar_dados_da_conta(usuario, senha) -> None:
    if not isinstance(usuario, str) or not isinstance(senha, str):
        raise DadosDeContaInvalidos("informe usuário e senha (texto).")
    if not 0 < len(usuario) <= TAMANHO_MAXIMO or usuario != usuario.strip() or not usuario.isprintable():
        raise DadosDeContaInvalidos(
            f"o usuário deve ter de 1 a {TAMANHO_MAXIMO} caracteres, sem espaço no início nem no fim."
        )
    if not TAMANHO_MINIMO_SENHA <= len(senha) <= TAMANHO_MAXIMO:
        raise DadosDeContaInvalidos(
            f"a senha deve ter de {TAMANHO_MINIMO_SENHA} a {TAMANHO_MAXIMO} caracteres."
        )


def _gravar_env(caminho: Path, usuario: str, hash_da_senha: str) -> None:
    """Grava por arquivo temporário e `os.replace`: o `.env` nunca fica pela metade."""
    temporario = caminho.with_name(caminho.name + ".tmp")
    try:
        temporario.write_text(
            f"{CHAVE_USUARIO}={usuario}\n{CHAVE_HASH}={hash_da_senha}\n", encoding="utf-8"
        )
        os.replace(temporario, caminho)
    finally:
        temporario.unlink(missing_ok=True)


def _ler_conta(usuario: str, hash_da_senha: str):
    partes = hash_da_senha.split("$")
    try:
        if len(partes) != 3 or partes[0] != ESQUEMA or not usuario:
            raise ValueError
        return usuario, bytes.fromhex(partes[1]), bytes.fromhex(partes[2])
    except ValueError:
        raise ValueError("usuário vazio ou hash de senha em formato inválido") from None


class Credenciais:
    """Sem `usuario` e `hash_da_senha`, ainda não há conta. Com `caminho`, `criar` grava o `.env`."""

    def __init__(self, usuario=None, hash_da_senha=None, *, caminho=None):
        self._caminho = None if caminho is None else Path(caminho)
        self._trava = threading.Lock()
        self._conta = None
        if usuario is not None or hash_da_senha is not None:
            self._conta = _ler_conta(usuario or "", hash_da_senha or "")

    @classmethod
    def do_env(cls, caminho) -> "Credenciais":
        """`.env` ausente ou com os dois valores vazios vale como "sem conta"; hash malformado, não."""
        try:
            valores = carregar_env(caminho)
        except FileNotFoundError:
            return cls(caminho=caminho)
        except (OSError, ValueError) as erro:
            raise CredenciaisAusentes(MENSAGEM_ENV_INVALIDO.format(caminho=caminho)) from erro
        usuario, hash_da_senha = valores.get(CHAVE_USUARIO, ""), valores.get(CHAVE_HASH, "")
        if not usuario and not hash_da_senha:
            return cls(caminho=caminho)
        try:
            return cls(usuario, hash_da_senha, caminho=caminho)
        except ValueError as erro:
            raise CredenciaisAusentes(MENSAGEM_ENV_INVALIDO.format(caminho=caminho)) from erro

    @property
    def configurada(self) -> bool:
        return self._conta is not None

    @property
    def usuario(self) -> str:
        return self._conta[0]

    def criar(self, usuario, senha) -> None:
        """Cria a única conta: grava o `.env` e só então a ativa. Falha de gravação (`OSError`) não ativa."""
        with self._trava:
            if self._conta is not None:
                raise ContaJaExiste("já existe uma conta cadastrada")
            validar_dados_da_conta(usuario, senha)
            hash_da_senha = gerar_hash(senha)
            if self._caminho is not None:
                _gravar_env(self._caminho, usuario, hash_da_senha)
            self._conta = _ler_conta(usuario, hash_da_senha)

    def verificar(self, usuario: str, senha: str) -> bool:
        """Confere os dois sempre, com o scrypt também quando o usuário erra ou não há conta (tempo igual)."""
        conta = self._conta
        if conta is None:
            _derivar(senha, _SAL_SEM_CONTA)
            return False
        usuario_guardado, sal, esperado = conta
        derivado = _derivar(senha, sal)
        usuario_certo = hmac.compare_digest(usuario.encode("utf-8"), usuario_guardado.encode("utf-8"))
        senha_certa = hmac.compare_digest(derivado, esperado)
        return usuario_certo and senha_certa
