# Remix 1 · del programa nativo a un cambio reversible

El puente usa el NSO original de Groove Switch 1.0.0, el proyecto local de referencia de 105 entidades y el checkout existente de Switch Studio. Reutiliza el recuperador de ARM64, el mapa de 40 parejas y el planificador IPS. No requiere una segunda extracción ni integra un cargador.

## Cómo se programa

En `0x3AD550` se preparan la escena y el BGM. El inicio de escena llama a `0x4D7B40` en `0x3AD5EC`. El arranque de BGM en `0x3AD698 → 0x139140` usa el recurso 121, que se resolvió a `t_akalui_song.cwv`. El mapa de tempo y el prerroll se conservan como metadatos RHRE derivados del WMB. Los ticks del guion y el contador monotónico del Recorder son relojes distintos.

La rutina construye objetos de secuencia mediante `0x514A90` y añade seis a la lista del runner desde `0x3AD724`, `0x3AD778`, `0x3AD7CC`, `0x3AD820`, `0x3AD874` y `0x3AD8C8`. `0x5153A0` recorre enlaces en `+8` y escribe el objeto en el enlace terminal. El primero de esos registros carga un puntero de callback en `x3` desde `0xD9BEA8` y pasa el objeto y su área `+0x280`. Esto respalda una secuencia de código y objetos nativos. En los cuatro hilos de acciones recuperados, `0x514D70` implementa las esperas y `0x514DD0` consulta cancelación. El hilo de control recuperado aporta 23 cambios visuales, además de la escena inicial. Las ventanas de entrada se materializan más tarde por callbacks de las acciones.

## Documento y exportación

`snapshot` conserva las 40 acciones, 767 esperas de los cuatro hilos, instrucciones y bytes, aristas de control, argumentos resueltos o desconocidos y los cambios visuales recuperados. Compara 64 anclas por identidad y tiempo contra el RHRE y valida las 40 correspondencias de patrón con el mapa existente. Las correspondencias son anclas de edición y sus desfases conservan el carácter de hipótesis. El documento cubre las regiones recuperadas, no todas las rutinas ni todos los caminos del nivel.

Las observaciones opcionales se resumen por sesión y último contexto de etapa 89. En la traza local, 24 llamadas de gameplay y 66 altas de hilos en ese contexto coexisten con eventos derivados y esperas de otros callbacks. Las cuentas no equivalen a llamadas del guion. Para un enlace comprobable falta una identidad de instancia de hilo y su PC de callback normalizado al Build ID, propagados al sitio de llamada y al reloj del hilo. Antes de capturarlos en el módulo queda por verificar esa propagación durante reentrada y reciclaje. Esta revisión mantiene el módulo y sus 84 hooks.

    python tools/remix1_sequence.py --research-root /local/switch-studio snapshot /local/main /local/Remix1-Switch-Referencia-Nativa.rhref secuencia.json --trace /local/groove-recorder.log
    python tools/remix1_sequence.py --research-root /local/switch-studio export /local/main secuencia-editada.json prueba.zip

Usa el entorno del recuperador de Switch Studio con Capstone y soporte NSO. Cambia solo `edits[].target_ticks`. El exportador reconstruye las identidades y los tiempos originales desde el NSO. Los campos de evidencia del documento son informativos. El backend admite 18 ventanas aislables, verifica las dependencias, reextrae las 40 acciones y comprueba el retorno byte a byte con el IPS inverso. Pasa `--existing-ips` para auditar conflictos. Conserva los JSON con bytes nativos en local.

Prueba local: el tercer aro `0x3B2370` se movió de 35.520 a 36.000 ticks, con 39 acciones intactas y reversión exacta. El IPS es idéntico al que el usuario ya probó en Switch, SHA-256 `203692b2b37c324ab4094c582eb1181d2c203d6378f63b6f85e69bc19c3f7873`. Esta revisión no ejecutó una nueva prueba en consola. Para desactivar la modificación, basta retirar su IPS. El IPS inverso es para comprobación offline.
