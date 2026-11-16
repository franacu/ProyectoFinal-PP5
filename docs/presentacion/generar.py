"""Arma presentacion.md a partir de plantilla.md tomando el código REAL del dominio.

En la plantilla, una línea como

    {{codigo dominio/mision.py:Mision.reasignar}}

se reemplaza por el código actual de esa clase, método o función (lo busca con `ast`,
así que no depende de números de línea). Se puede agregar `sin-doc` para quitar
el docstring:

    {{codigo dominio/mision.py:Rescate sin-doc}}

Uso, desde la raíz del repo:

    python docs/presentacion/generar.py
"""

import ast
import re
import sys
import textwrap
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
MARCA = re.compile(r"\{\{codigo\s+([\w./]+):([\w.]+)(\s+sin-doc)?\s*\}\}")


def buscar(nodo: ast.AST, nombres: list[str]) -> ast.AST | None:
    """Baja por el árbol: ['Mision', 'reasignar'] -> el método reasignar de Mision."""
    actual = nodo
    for nombre in nombres:
        encontrado = None
        for hijo in getattr(actual, "body", []):
            if isinstance(hijo, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and hijo.name == nombre:
                encontrado = hijo
                break
        if encontrado is None:
            return None
        actual = encontrado
    return actual


def fuente(ruta: str, nombre: str, sin_doc: bool) -> str:
    archivo = RAIZ / ruta
    texto = archivo.read_text(encoding="utf-8")
    nodo = buscar(ast.parse(texto), nombre.split("."))
    if nodo is None:
        sys.exit(f"No encontré {nombre} en {ruta}")
    lineas = texto.splitlines()
    inicio = (nodo.decorator_list[0].lineno if nodo.decorator_list else nodo.lineno) - 1
    codigo = "\n".join(lineas[inicio:nodo.end_lineno])
    codigo = textwrap.dedent(codigo)
    if sin_doc:
        codigo = re.sub(r'\n[ ]+"""(?:.|\n)*?"""\n', "\n", codigo, count=1)
        codigo = codigo.replace(":\n\n", ":\n", 1)
    return codigo


def reemplazo(m: re.Match) -> str:
    return "```python\n" + fuente(m.group(1), m.group(2), bool(m.group(3))) + "\n```"


def main() -> None:
    plantilla = (AQUI / "plantilla.md").read_text(encoding="utf-8")
    salida = MARCA.sub(reemplazo, plantilla)
    (AQUI / "presentacion.md").write_text(salida, encoding="utf-8")
    print(f"presentacion.md generada ({len(MARCA.findall(plantilla))} fragmentos de código)")


if __name__ == "__main__":
    main()
