"""
Exceções semânticas de domínio compartilhadas pela camada de serviços.

Mantidas fora de ``src.controllers`` para que os services não dependam da camada HTTP.
O mapeamento para status HTTP é feito em ``src.controllers.response_controller``.
"""
from typing import Any, Dict, Optional


class ConfirmacaoNecessariaError(ValueError):
    """
    Operação válida, porém sensível a uma regra de negócio, que só pode prosseguir
    com confirmação explícita do usuário (HTTP 409 Conflict).

    O frontend deve identificar o caso pelo ``codigo`` (estável, nunca pela mensagem),
    exibir a ``mensagem`` ao usuário e, se confirmado, reenviar a mesma requisição
    com o parâmetro ``confirmacao`` = true.

    Herda de ValueError para manter compatibilidade com chamadas internas/ETL que
    já tratam ValueError.
    """

    def __init__(
        self,
        mensagem: str,
        codigo: str,
        confirmacao: str,
        contexto: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo = codigo
        self.confirmacao = confirmacao
        self.contexto = contexto or {}

    def para_dict(self) -> Dict[str, Any]:
        return {
            "codigo": self.codigo,
            "mensagem": self.mensagem,
            "confirmacao": self.confirmacao,
            "contexto": self.contexto,
        }


__all__ = ["ConfirmacaoNecessariaError"]

