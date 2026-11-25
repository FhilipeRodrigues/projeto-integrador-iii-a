"""Credencial do analista: usuário e hash da senha lidos do `.env` (RNF-08).

O hash é `scrypt$<sal hex>$<hash hex>`, da biblioteca padrão. A senha em si nunca é guardada.
"""

import hashlib
import hmac
import secrets
from pathlib import Path

ESQUEMA = "scrypt"
CUSTO_N, BLOCO_R, PARALELISMO_P = 2**14, 8, 1
TAMANHO_SAL = 16
TAMANHO_MAXIMO = 100  # usuário e senha; limita o trabalho que um pedido pode causar
CHAVE_USUARIO = "USUARIO"
CHAVE_HASH = "SENHA_HASH"

MENSAGEM_SEM_CONFIGURACAO = (
    "Configuração de login ausente ou inválida em '{caminho}'. "
    "Copie .env.example para .env, informe USUARIO e gere a linha SENHA_HASH com: "
    "python -m scripts.gerar_hash"
)


class CredenciaisAusentes(RuntimeError):
    """O `.env` não existe ou não traz um usuário e um hash válidos."""


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


class Credenciais:
    def __init__(self, usuario: str, hash_da_senha: str):
        partes = hash_da_senha.split("$")
        try:
            if len(partes) != 3 or partes[0] != ESQUEMA or not usuario:
                raise ValueError
            self._sal, self._esperado = bytes.fromhex(partes[1]), bytes.fromhex(partes[2])
        except ValueError:
            raise ValueError("usuário vazio ou hash de senha em formato inválido") from None
        self._usuario = usuario

    @classmethod
    def do_env(cls, caminho) -> "Credenciais":
        try:
            valores = carregar_env(caminho)
            return cls(valores[CHAVE_USUARIO], valores[CHAVE_HASH])
        except (OSError, KeyError, ValueError) as erro:
            raise CredenciaisAusentes(MENSAGEM_SEM_CONFIGURACAO.format(caminho=caminho)) from erro

    @property
    def usuario(self) -> str:
        return self._usuario

    def verificar(self, usuario: str, senha: str) -> bool:
        """Confere os dois sempre, com o scrypt também quando o usuário erra (tempo igual)."""
        derivado = _derivar(senha, self._sal)
        usuario_certo = hmac.compare_digest(usuario.encode("utf-8"), self._usuario.encode("utf-8"))
        senha_certa = hmac.compare_digest(derivado, self._esperado)
        return usuario_certo and senha_certa
