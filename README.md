# CRCE — Centro Regional de Coordinación de Emergencias

TP Integrador 2026 · Paradigmas de Programación V · FIE-UNDEF

## Avance 1 — Avisos y notas

Diseño (diagramas de clases y estados, tarjetas CRC): [`docs/avance-1.md`](docs/avance-1.md)

```bash
uv sync
uv run pytest
```

```
dominio/
  catalogos.py   # TipoSituacion, Gravedad (catálogos cerrados)
  errores.py     # excepciones de dominio
  aviso.py       # Aviso (entidad) + Ubicacion, Nota, Descarte (valores)
tests/
  test_avisos.py # R1..R6
docs/
  avance-1.md
```
