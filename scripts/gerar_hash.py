"""Gera a linha SENHA_HASH para o `.env` (a senha é pedida sem aparecer na tela).

Uso, a partir da pasta do projeto: python -m scripts.gerar_hash
"""

import getpass
import sys

from consulta import credenciais


def main() -> int:
    senha = getpass.getpass("Senha: ")
    if not senha or len(senha) > credenciais.TAMANHO_MAXIMO:
        print(f"Erro: a senha deve ter de 1 a {credenciais.TAMANHO_MAXIMO} caracteres.", file=sys.stderr)
        return 1
    if getpass.getpass("Repita a senha: ") != senha:
        print("Erro: as senhas não conferem.", file=sys.stderr)
        return 1
    print(f"{credenciais.CHAVE_HASH}={credenciais.gerar_hash(senha)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
