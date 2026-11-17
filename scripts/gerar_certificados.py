"""Gera a CA local e o certificado do servidor, usando o executável `openssl`.

O cliente confia somente na CA gerada aqui. Os certificados atendem à verificação
estrita do Python 3.13+ (extensões de identificador de chave e de uso de chave).
As chaves privadas ficam fora do git (certs/ no .gitignore).

Uso: python scripts/gerar_certificados.py [pasta]   (padrão: certs/)
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DESTINO_PADRAO = Path(__file__).resolve().parent.parent / "certs"
ARQUIVOS = ("ca.crt", "ca.key", "servidor.crt", "servidor.key")
# No Windows, o Git for Windows traz o openssl fora do PATH.
CANDIDATOS_OPENSSL = (r"C:\Program Files\Git\usr\bin\openssl.exe",)
VALIDADE_DIAS = "825"

EXTENSOES_CA = (
    "basicConstraints=critical,CA:TRUE",
    "keyUsage=critical,keyCertSign,cRLSign",
    "subjectKeyIdentifier=hash",
)
EXTENSOES_SERVIDOR = """\
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
subjectAltName=DNS:localhost,IP:127.0.0.1
"""

MENSAGEM_SEM_OPENSSL = (
    "O programa 'openssl' não foi encontrado. Ele gera os certificados do projeto. "
    "No Windows, instale o Git for Windows (https://git-scm.com), que o inclui. "
    "No Linux, instale o pacote 'openssl' (ex.: sudo apt install openssl). "
    "No macOS, use 'brew install openssl'. Depois rode o script de novo."
)


class OpenSslAusente(RuntimeError):
    """O executável openssl não está disponível nesta máquina."""


class FalhaOpenSsl(RuntimeError):
    """O openssl terminou com erro."""


def localizar_openssl() -> str:
    caminho = shutil.which("openssl")
    if caminho:
        return caminho
    for candidato in CANDIDATOS_OPENSSL:
        if Path(candidato).is_file():
            return candidato
    raise OpenSslAusente(MENSAGEM_SEM_OPENSSL)


def _executar(openssl: str, *argumentos: str) -> None:
    resultado = subprocess.run(
        [openssl, *argumentos], capture_output=True, text=True, check=False
    )
    if resultado.returncode != 0:
        raise FalhaOpenSsl(
            f"openssl {argumentos[0]} falhou: {resultado.stderr.strip() or resultado.stdout.strip()}"
        )


def _gerar_em(trabalho: Path, openssl: str) -> None:
    extensoes_ca = [arg for ext in EXTENSOES_CA for arg in ("-addext", ext)]
    _executar(
        openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(trabalho / "ca.key"), "-out", str(trabalho / "ca.crt"),
        "-days", VALIDADE_DIAS, "-subj", "/CN=CA local - Consulta TCM-GO (prototipo)",
        *extensoes_ca,
    )
    _executar(
        openssl, "req", "-new", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(trabalho / "servidor.key"), "-out", str(trabalho / "servidor.csr"),
        "-subj", "/CN=localhost",
    )
    arquivo_extensoes = trabalho / "servidor.ext"
    arquivo_extensoes.write_text(EXTENSOES_SERVIDOR, encoding="ascii", newline="\n")
    _executar(
        openssl, "x509", "-req", "-in", str(trabalho / "servidor.csr"),
        "-CA", str(trabalho / "ca.crt"), "-CAkey", str(trabalho / "ca.key"),
        "-CAcreateserial", "-out", str(trabalho / "servidor.crt"),
        "-days", VALIDADE_DIAS, "-extfile", str(arquivo_extensoes),
    )


def gerar_certificados(destino=DESTINO_PADRAO) -> Path:
    """Cria ca.crt, ca.key, servidor.crt e servidor.key em `destino`.

    Gera tudo numa pasta de trabalho e só então copia os quatro arquivos: se o
    openssl faltar ou falhar, nada é deixado em `destino`.
    """
    destino = Path(destino)
    openssl = localizar_openssl()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino.parent, prefix=".certs-") as bruto:
        trabalho = Path(bruto)
        _gerar_em(trabalho, openssl)
        for nome in ARQUIVOS:
            if nome.endswith(".key"):
                trabalho.joinpath(nome).chmod(0o600)  # sem efeito prático no Windows
        criada = not destino.exists()
        destino.mkdir(exist_ok=True)
        copiados = []
        try:
            for nome in ARQUIVOS:
                shutil.move(str(trabalho / nome), destino / nome)
                copiados.append(destino / nome)
        except OSError:
            for arquivo in copiados:
                arquivo.unlink(missing_ok=True)
            if criada:
                shutil.rmtree(destino, ignore_errors=True)
            raise
    return destino


def main(argumentos=None) -> int:
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    alvo = Path(argumentos[0]) if argumentos else DESTINO_PADRAO
    try:
        gerar_certificados(alvo)
    except (OpenSslAusente, FalhaOpenSsl) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    print(f"Certificados gravados em {alvo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
