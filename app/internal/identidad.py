"""Quién hace el pedido.

Etapa actual: el usuario se identifica con el encabezado `X-Usuario`. Es un lugar
provisorio y deliberadamente aislado: cuando se incorpore la autenticación con token,
solo cambia esta función. Los routers ya reciben al usuario como dependencia y no se
modifican.
"""

from typing import Annotated

from fastapi import Header


def usuario_actual(x_usuario: Annotated[str, Header(min_length=1, description="Identificador del usuario")]) -> str:
    return x_usuario
