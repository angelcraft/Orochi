# Groove Recorder · ciclo de ventanas de Switch 1.0.0

Base de referencia confirmada en consola por el usuario: `635204f`. Respaldo anterior: `7cbaf92`. Este lote mantiene los 84 hooks y el escritor existentes.

| Etapa | Evidencia en `main` | Registro experimental |
| --- | --- | --- |
| Alta | `0x12F0F0` llama a `0x12DB30`, que inicializa el ID en `+0x10` y el tiempo relativo en `+0x34`. `0x12DD60` inserta en la lista. | ID, clave de filtro `+0x44`, tiempo y cuatro umbrales efectivos |
| Evaluación | `0x12E180` comprueba el ID y clasifica el tiempo frente a los umbrales `+0x24..0x30`. | Código original, tiempo relativo y umbrales efectivos |
| Entrada lógica y selección | `0x12A690 → 0x12E500` filtra, selecciona y llama al virtual `+0x30` en `0x12E698` con el código de admisión y el argumento nativo. La consulta `0x12E6F0` también evalúa sin seleccionar. | ID, argumentos y retorno del despachador. El retorno identifica que se seleccionó alguna ventana. |
| Avance y vencimiento | `0x12DE60` suma el delta. En el cruce por cero activa el bit `+0x39` y llama al virtual `+0x40`. Si sigue pendiente y excede el límite `+0x30`, limpia `+0x3A` y llama al virtual `+0x28`. | Instantánea antes y después solo si cambian los bits `+0x38/+0x39/+0x3A`. Una limpieza observada puede tener otras causas durante las llamadas virtuales. |
| Rearme | `0x12F4DC → 0x12E020` resta el delta y restablece `+0x39/+0x3A` a 0/1. | Delta original y tiempo relativo posterior |

Guardas nuevas: `0x12DE60 = A9BE7BFD` y `0x12E020 = B9403408`. Ambas entradas tienen ABI `void(void*, s32)`. El gestor lee la ventana después de la actualización virtual en `0x12E4CC`. Los hooks llaman al original una vez, conservan argumentos y encolan fuera de las llamadas de escritura.

## Tres rutas verificadas estáticamente

- Hoop Trundling: `0x217538 → 0x2182C0`, `0x2182E8 → 0x12F0F0`, y `0x217360 → 0x12A690`.
- Lightning Bolting: `0x27D8A4 → 0x27F010`, `0x27F048 → 0x12F0F0`, y `0x27D68C → 0x12A690`.
- Flydisc: `0x18D8FC → 0x12F0F0`, y `0x18CE6C → 0x12A690`.

La ruta lógica consulta transiciones de ranura en `0x506C80` y encola en `0x12D8F0`. `0x12AF74 → 0x12D930` consume esas entradas mediante virtuales. La máscara física del mando queda por vincular. El entero que devuelve el proveedor virtual de `0x515660` pasa desde `0x12AEAC` al gestor en `0x12AF68`. El tiempo de ventana se puede observar como relativo. Su origen musical absoluto y la relación con el BGM siguen pendientes. Los códigos 0/1/2 se conservan sin etiquetas de precisión.

## Lector y prueba

`GROOVE_NATIVE2` agrega un token de identidad de objeto a los 12 campos anteriores. La correlación se limita a la sesión. El alta y el rearme inician un nuevo ciclo en JSONL. Un salto de secuencia o aviso de pérdidas invalida el contexto anterior. El historial de identidad del lector conserva hasta 8192 objetos por sesión y cuenta las expulsiones. El log y la salida JSONL siguen siendo secuenciales. Las trazas `GROOVE_NATIVE` antiguas conservan sus estadísticas sin identidad de objeto.

El lector informa por contexto de etapa los umbrales al alta, los códigos de admisión, los retornos del despachador y las transiciones de estado. La acción anterior de la misma etapa y el número de evaluaciones previas del mismo ID son referencias temporales. Pueden incluir sondeos ajenos al despacho y no atribuyen causalidad ni identifican una ventana seleccionada.

Verificación local: `python tools/verify_native_inputs.py RUTA_AL_MAIN_NSO` con `lz4`. Comprueba SHA-256, Build ID, cinco guardas, 22 saltos, ocho punteros y cuenta 145 sitios de despacho directo.

Para probar en emuMMC, conserva una copia del `subsdk1` funcional y cambia exclusivamente ese archivo con la consola apagada. Conserva NPDM, IPS y partidas. Juega un tramo con entradas y omisiones en los tres minijuegos y revisa los registros `GROOVE_NATIVE2`. Para revertir, restaura el módulo anterior con la consola apagada. La ejecución de esta revisión queda pendiente de hardware.
