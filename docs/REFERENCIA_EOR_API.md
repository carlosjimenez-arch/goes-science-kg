# Referencia de ingeniería · eor-api y GOEs · 2026

La referencia local `eor-api` de 2024 ya es accesible y se revisó como material de arquitectura.
Su inventario contiene ocho módulos Python de producción y siete de pruebas. Se leyeron rutas,
servicios, configuración, middleware y modelos; se inspeccionaron pruebas, dependencias y contenedor.
Se trató como referencia, sin importar sus módulos, ejecutar sus clientes ni leer secretos.

El usuario confirmó que el alcance sigue siendo **Ciencias**. El rol de ingeniería y AIOps no cambia
las disciplinas ni convierte la semilla matemática del HTML en datos publicados.

## Adaptación al proyecto

| Patrón de referencia | Aplicación GOEs |
|---|---|
| Rutas separadas del cliente | `api*.py` delegan consultas V4 en servicios, lector y exportadores |
| Modelos de entrada y respuesta | Contratos Pydantic curriculares y respuestas tipadas de interfaz |
| Cliente con estado encapsulado | El lector fija el snapshot; el servicio conserva índices y verifica originales |
| Configuración explícita | Raíz aislada, configuración versionada y OpenAPI GOEs sin credenciales para consultar |
| Middleware operativo | `ObservabilidadHTTP`: correlación, estado y tiempos mediante el logging local existente |
| Pruebas por frontera | Contratos HTTP, servicios, fuentes sintéticas y regresiones de fallos reproducidos |
| Informes de cobertura | JUnit y cobertura propios, con denominador, fecha y huella verificables |

## Criterio crítico

Los clientes remotos de GOEs se crean cuando una operación autorizada los necesita. Importar la
aplicación y consultar datos locales no requiere abrir un proveedor de modelos. Los handlers se
configuran de forma central, sin añadir exportadores desde cada módulo o petición.

La correlación identifica cada operación. GOEs genera un UUID por petición incluso si el cliente
aporta otro identificador; no usa una identidad común ni convierte una cabecera en una identidad
institucional. Las consultas SQL de la operación local usan parámetros. La selección curricular
consulta índices verificados. Las pruebas inyectan proveedores y contrastan el comportamiento;
se evitan pruebas que sustituyen el mismo método cuya lógica pretenden comprobar.

La organización conserva el dominio GOEs, sin copiar código, nombres de negocio, marcas, claves o
infraestructura externa. Las transformaciones puras siguen siendo funciones. Los extractores firmados
y los antecedentes mantienen las excepciones de evidencia descritas en [Calidad](CALIDAD.md).

## Observabilidad HTTP local

Las respuestas HTTP gestionadas incorporan `X-Request-ID` y `Server-Timing: app;dur=...`.
La cabecera mide milisegundos desde la entrada al middleware hasta el inicio de la respuesta.
El evento final incluye `request_id`, `http_method`, `http_route`, `http_status` y `duration_ms`;
este último abarca la operación ASGI completa hasta que devuelve el control.

Los eventos GOEs usan plantillas de ruta sin valores de parámetros, query string, cuerpo ni usuario.
Se emiten a los handlers locales existentes con nivel INFO y no activan exportadores. El middleware
no configura logs de otros servidores o bibliotecas ni implementa autenticación o monitoreo remoto.
La correlación incluye los errores documentados de ausencia de datos; no acredita SLA, facturación
o eficacia educativa.

[Auditoría de versionado](auditoria/GITIGNORE_2026.md) ·
[Auditoría de producto](auditoria/QA_PRODUCTO_20261025.md) · [API de Ciencias](APLICACION_CIENCIAS.md).
