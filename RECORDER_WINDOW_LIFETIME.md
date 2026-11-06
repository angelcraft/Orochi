# Vida útil de las ventanas · Groove Switch 1.0.0

Auditoría desde `76a52a9`. Las direcciones se expresan como offsets de `main`. El verificador fija el SHA-256 y Build ID del NSO original y comprueba 24 palabras ARM64 de esta auditoría además de las guardas, saltos y tablas existentes.

| Hook | Precondición y evidencia posterior |
| --- | --- |
| Alta `0x12DD60` | El único salto directo es `0x12A680`, en el adaptador del constructor. `0x12DB30` inicializa ID, desplazamiento, clave y umbrales antes de publicar. `0x12DD7C` escribe en la ventana sin comprobación de nulo. La rama que admite temporalmente un gestor nulo al calcular umbrales converge en la inserción de lista, que usa el gestor en `0x12DE2C..0x12DE48`. El contrato de la ruta observada exige ambos objetos válidos. Tras el alta, el propio constructor relee la ventana en `0x12F1B0`. |
| Evaluación `0x12E180` | Empieza con `ldr w8,[x0,#0x10]`. Sus tres llamadas directas provienen de recorridos que ya han leído el candidato. `x2` es una salida opcional. La llamada virtual de escalado en `0x12E1DC` recibe el proveedor y la clave; tras volver el juego restaura el puntero guardado en `x19`, lee los umbrales nominales y escribe los efectivos. El despachador también relee los candidatos admitidos en `0x12E5A8` y `0x12E63C`. El camino de ID distinto no actualiza umbrales y el hook lo excluye. |
| Avance `0x12DE60` | La continuación desde `0x12F3BC` recibe la ventana original y lee `+0x34/+0x39` sin comprobación de nulo. Aunque ejecuta virtuales de activación, actualización y vencimiento, el recorrido del gestor lee `+0x38` del mismo puntero después del retorno en `0x12E4CC`. Si procede, invoca el destructor virtual en `0x12E3D0` y retira el nodo. La ruta nativa observada mantiene viva la ventana durante el retorno del hook. |
| Rearme `0x12E020` | La función de rearme que la precede ya escribe en el objeto. La rutina es hoja: lee y escribe `+0x34`, escribe dos bytes en `+0x39` y retorna. Carece de llamada o salto que pueda liberar o sustituir el objeto. |

El constructor común inicializa `+0x10`, `+0x34` y `+0x44`. Los umbrales efectivos ocupan `+0x24..0x30` y los indicadores `+0x38..0x3A` se leen en las rutas nativas. El registrador lee esos campos sobre el hilo que ejecuta la función y copia valores. El escritor recibe una identidad opaca y nunca desreferencia la ventana. La evidencia confirma los contratos de las rutas observadas. No demuestra seguridad frente a un puntero ya inválido, una destrucción concurrente fuera del contrato del motor o modificaciones ajenas.

`lastCreatedStage` es un atómico global que publica el último resultado de la factoría. Una creación posterior en otro hilo puede cambiar el contexto de un evento de una ventana anterior. Cambiar el orden de memoria no establece propiedad. El lector declara `last_factory_result` y enlaza la ventana por sesión, token y ciclo independientemente de ese contexto. Las estadísticas por etapa siguen describiendo el contexto observado.

La auditoría no encontró un motivo para insertar comprobaciones de nulo en los hooks. Las funciones nativas ya exigen el objeto y saltarse una llamada cambiaría el comportamiento. El módulo queda con los mismos hooks y campos. Este lote añade evidencia reproducible y una regresión del lector, sin nueva validación en consola.

    python tools/verify_native_inputs.py RUTA_AL_MAIN_NSO
    python -m unittest discover -s tests -p "test_*.py"
