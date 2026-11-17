# Guion breve · Backend del CRCE

Duración sugerida: 5–7 minutos. La presentación tiene 8 diapositivas. No leas el código línea por línea: señalá el fragmento y explicá la decisión.

## 1. Visión general
"El backend es el núcleo de reglas del CRCE. No es una API ni un servidor web: es un dominio Python que modela avisos, emergencias, misiones y recursos. La interfaz y los diagramas son documentación HTML estática."

## 2. Configuración y módulos
"El proyecto se configura con `pyproject.toml`, requiere Python 3.13 o superior y no tiene dependencias de producción. pytest se usa para desarrollo y pruebas. Separamos el dominio en módulos según la responsabilidad de cada concepto."

## 3. aviso.py
"Cuando se crea un aviso, queda pendiente. El método descartar primero le pregunta al estado si permite esa operación. Después valida y construye el descarte y el registro. Recién al final modifica el estado. Esto evita dejar el objeto a medio modificar si ocurre un error. Es encapsulamiento y State."

## 4. mision.py
"`Mision` es abstracta porque no tiene sentido crear una misión genérica: necesitamos una evacuación, un rescate o una asistencia sanitaria. Las clases hijas implementan sus requisitos. El resto del dominio puede trabajar contra Mision y cada tipo resuelve su comportamiento: eso es polimorfismo."

## 5. unidad.py y vehiculos.py
"La unidad reúne jefe, personal, vehículo y equipamiento. Antes de comprometerse con una misión comprueba todas las condiciones. La misión define qué vehículo necesita y el vehículo responde si puede cumplirlo. Así evitamos llenar el código de comparaciones por tipo."

## 6. flota.py y emergencia.py
"Flota controla reglas que una unidad sola no puede garantizar: que una persona, vehículo o equipo no esté repetido en otra unidad. Emergencia controla el cierre: no permite cerrar si quedan misiones pendientes y exige al menos una misión exitosa."

## 7. historial.py y errores.py
"Cada operación relevante genera un Registro inmutable con actor, fecha, operación y recursos afectados. Los errores son clases propias del dominio para que el sistema pueda distinguir por qué se rechazó una operación."

## 8. Soporte y pruebas
"Los catálogos restringen valores posibles; valores centraliza validaciones; distribución comprueba que personas distintas cubran los puestos de una misión. Las pruebas automatizadas verifican tanto el comportamiento como decisiones de diseño. Por ejemplo, test_diseno comprueba que el dominio no pregunte por el tipo concreto de los objetos."

## Preguntas que podrían hacer
- **¿Por qué no hay API o base de datos?** El alcance implementado en este repositorio es el dominio y sus reglas; no hay persistencia ni servidor web en esta entrega.
- **¿Por qué State?** Para que cada estado determine qué operaciones acepta, evitando condicionales repetidos por todo el objeto.
- **¿Dónde se ve el polimorfismo?** En las misiones y vehículos: el código llama a un método común y cada clase concreta responde según sus capacidades.
- **¿Por qué Flota y no Unidad valida duplicados?** Porque la unicidad se compara entre todas las unidades, no dentro de una sola.
- **¿Qué significa fallar antes de modificar?** Validar todos los requisitos y construir los registros antes de cambiar el estado interno.
- **¿Qué hace `frozen=True`?** Impide reasignar los campos del dataclass después de construirlo; se usa para representar valores y registros inmutables.
