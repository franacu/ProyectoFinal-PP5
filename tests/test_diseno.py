"""Reglas de diseño del profesor, verificadas sobre el código fuente del dominio.

La corrección repetida fue: el comportamiento que depende del tipo o del estado
se delega (polimorfismo), no se decide preguntando por clase. Este test lo vigila.
"""

import re
from pathlib import Path

import pytest

DOMINIO = Path(__file__).resolve().parent.parent / "dominio"
ARCHIVOS = sorted(DOMINIO.glob("*.py"))


def sin_comentarios(archivo: Path) -> str:
    """Código sin docstrings ni comentarios (ahí se puede nombrar lo que se prohíbe)."""
    return re.sub(r'""".*?"""|#.*', "", archivo.read_text(), flags=re.S)


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=lambda a: a.name)
def test_el_dominio_no_pregunta_por_la_clase_de_los_objetos(archivo):
    codigo = sin_comentarios(archivo)

    assert "isinstance(" not in codigo
    assert "type(" not in codigo
    assert "__class__" not in codigo


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=lambda a: a.name)
def test_el_dominio_solo_usa_la_biblioteca_estandar(archivo):
    importados = re.findall(r"^(?:from|import)\s+([\w.]+)", archivo.read_text(), flags=re.M)
    ajenos = [m for m in importados if m.split(".")[0] not in
              {"dominio", "__future__", "abc", "collections", "dataclasses", "datetime", "enum",
               "operator", "typing", "uuid"}]

    assert ajenos == []


def test_el_dominio_no_toma_la_hora_del_sistema():
    codigo = "".join(sin_comentarios(a) for a in ARCHIVOS)

    assert "datetime.now" not in codigo
    assert "utcnow" not in codigo
