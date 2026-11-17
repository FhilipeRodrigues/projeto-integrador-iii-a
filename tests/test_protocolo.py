import io
import json
import unittest

from consulta import protocolo


class _SoqueteFalso:
    def __init__(self):
        self.enviado = b""

    def sendall(self, dados):
        self.enviado += dados


class LerMensagemTest(unittest.TestCase):
    def test_linha_valida_vira_dicionario(self):
        arquivo = io.BytesIO('{"op": "municipios", "x": "ção"}\n'.encode("utf-8"))
        self.assertEqual(protocolo.ler_mensagem(arquivo), {"op": "municipios", "x": "ção"})

    def test_linha_que_nao_e_json_e_recusada(self):
        with self.assertRaises(protocolo.ProtocoloErro):
            protocolo.ler_mensagem(io.BytesIO(b"isto nao e json\n"))

    def test_json_que_nao_e_objeto_e_recusado(self):
        with self.assertRaises(protocolo.ProtocoloErro):
            protocolo.ler_mensagem(io.BytesIO(b"[1, 2]\n"))

    def test_bytes_que_nao_sao_utf8_sao_recusados(self):
        with self.assertRaises(protocolo.ProtocoloErro):
            protocolo.ler_mensagem(io.BytesIO(b'{"a": "\xff"}\n'))

    def test_linha_grande_demais_e_recusada(self):
        grande = b'{"nome": "' + b"a" * protocolo.LIMITE_LINHA + b'"}\n'
        with self.assertRaises(protocolo.ProtocoloErro):
            protocolo.ler_mensagem(io.BytesIO(grande))

    def test_linha_no_limite_exato_e_aceita(self):
        corpo = b'{"n": "' + b"a" * (protocolo.LIMITE_LINHA - len(b'{"n": ""}\n')) + b'"}\n'
        self.assertEqual(len(corpo), protocolo.LIMITE_LINHA)
        self.assertIn("n", protocolo.ler_mensagem(io.BytesIO(corpo)))

    def test_conexao_sem_mensagem_e_recusada(self):
        with self.assertRaises(protocolo.ProtocoloErro):
            protocolo.ler_mensagem(io.BytesIO(b""))

    def test_linha_sem_quebra_final_e_recusada(self):
        with self.assertRaises(protocolo.ProtocoloErro):
            protocolo.ler_mensagem(io.BytesIO(b'{"op": "municipios"}'))


class EscreverMensagemTest(unittest.TestCase):
    def test_escreve_uma_linha_json_utf8(self):
        soquete = _SoqueteFalso()
        protocolo.escrever_mensagem(soquete, {"ok": True, "dados": ["Anápolis"]})
        self.assertTrue(soquete.enviado.endswith(b"\n"))
        self.assertEqual(soquete.enviado.count(b"\n"), 1)
        self.assertEqual(
            json.loads(soquete.enviado.decode("utf-8")), {"ok": True, "dados": ["Anápolis"]}
        )


if __name__ == "__main__":
    unittest.main()
