# Avance 1 — Avisos y notas

Rebanada vertical: **registrar** un aviso, **agregarle notas** y **descartarlo** (§2.1, §7.1).
Dominio en Python puro (sin FastAPI, Pydantic ni Mongo).

## 1. Diagrama de clases

```mermaid
classDiagram
    direction LR

    class Aviso {
        <<entidad>>
        -id: str
        -reportante_id: str
        -ubicacion: Ubicacion
        -tipo: TipoSituacion
        -gravedad_estimada: Gravedad
        -descripcion: str
        -registrado_en: datetime
        -estado: _Estado
        -notas: list~Nota~
        -descarte: Descarte | None
        +agregar_nota(autor_id, texto, fecha_hora) Nota
        +descartar(operador_id, justificacion, fecha_hora)
        +estado() EstadoAviso
        +notas() tuple~Nota~
        +restaurar(...)$ Aviso
    }

    class _Estado {
        <<abstracta>>
        +permitir_nota()
        +descartar() _Estado
        +validar_descarte(descarte)
    }

    class _Pendiente
    class _Aceptado
    class _Descartado

    class Ubicacion {
        <<valor · inmutable>>
        +direccion: str
        +localidad: str
    }

    class Nota {
        <<valor · inmutable>>
        +autor_id: str
        +texto: str
        +fecha_hora: datetime
    }

    class Descarte {
        <<valor · inmutable>>
        +operador_id: str
        +justificacion: str
        +fecha_hora: datetime
    }

    class EstadoAviso {
        <<enumeration · nombre público>>
        PENDIENTE
        ACEPTADO
        DESCARTADO
    }

    class TipoSituacion {
        <<enumeration>>
        INUNDACION
        INCENDIO
        ACCIDENTE_VIAL
    }

    class Gravedad {
        <<enumeration>>
        BAJA
        MEDIA
        ALTA
    }

    Aviso *-- "1" Ubicacion
    Aviso *-- "0..*" Nota : notas (ordenadas)
    Aviso *-- "0..1" Descarte
    Aviso --> "1" _Estado : delega
    _Estado <|-- _Pendiente
    _Estado <|-- _Aceptado
    _Estado <|-- _Descartado
    _Estado ..> EstadoAviso : etiqueta
    Aviso --> "1" TipoSituacion
    Aviso --> "1" Gravedad : estimada
```

**Por qué así**

- `Aviso` es la única **entidad**: tiene identidad (`id`) y cambia de estado.
- `Ubicacion`, `Nota` y `Descarte` son **objetos valor** (`@dataclass(frozen=True)`): se validan al nacer, no cambian y no tienen identidad propia. Una nota sin autor o un descarte sin justificación no pueden existir.
- Composición (`*--`): las notas y el descarte no viven fuera de su aviso.
- `TipoSituacion` y `Gravedad` son `Enum`: un valor fuera de catálogo no se puede construir.
- `aviso.notas` devuelve una **tupla**: desde afuera no hay `append`, la única puerta es `agregar_nota()`.
- El **estado es un objeto** (State): `Aviso` no pregunta "¿estás pendiente?", le delega a `_Estado` (`permitir_nota()`, `descartar()`). El objeto estado no sale del aviso: afuera solo se ve `aviso.estado`, que devuelve el nombre (`EstadoAviso`).
- Sin comparar clases: la pertenencia a los catálogos se verifica con `Catalogo.contiene()` y los datos obligatorios con `_hay_texto()`.

## 2. Diagrama de estados del aviso

```mermaid
stateDiagram-v2
    [*] --> Pendiente : registrar(datos, fecha_hora)

    Pendiente --> Pendiente : agregar_nota(autor, texto, fecha_hora)
    Pendiente --> Descartado : descartar(operador, justificación, fecha_hora)
    Pendiente --> Aceptado : aceptar() — avance 2

    note right of Pendiente
        descartar con justificación vacía
        se rechaza y sigue Pendiente (R4, R6)
    end note

    note right of Descartado
        Rechaza: agregar_nota, descartar, aceptar
        Conserva justificación y fecha
    end note

    note right of Aceptado
        Rechaza: agregar_nota, descartar, aceptar
        Origina una única emergencia
    end note

    Descartado --> [*]
    Aceptado --> [*]
```

| Operación       |