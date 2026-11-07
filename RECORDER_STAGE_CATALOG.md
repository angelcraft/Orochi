# Groove Recorder — catálogo por etapas para móvil y PC

La instrumentación existente registra **84 acciones conocidas**, ventanas lógicas
y eventos comunes para todas las etapas alcanzadas. No es necesario jugar
Remix 1 exclusivamente. El siguiente comando procesa registros de consola
sin modificar el módulo ni el juego:

```sh
python tools/export_stage_catalog.py groove-recorder.log exportacion
python tools/export_stage_catalog.py groove-recorder.log solo-remix1 --stage 89
```

El resultado contiene:

- `index.json`: sesiones, ámbitos de etapa, cantidades de eventos y acciones
  observadas. Las repeticiones de etapa se separan por el ordinal de cada
  `stage_created` de la sesión.
- `observations.csv`: llamadas de gameplay, BGM/SFX, solicitudes de escena,
  altas/evaluaciones/despachos de ventanas, tiempos relativos y tokens
  observados. Abre en una hoja de cálculo o visor CSV desde Android.
- `sessions/<sesion>/segment-XXXX-stage-YY.jsonl`: registros descodificados
  íntegros, sin perder los argumentos originales o campos desconocidos.

**Advertencias técnicas (no ocultar al exportar):**

- El contexto de etapa procede del último resultado observado de
  `StageFactory`, almacenado globalmente. No demuestra qué instancia de
  etapa originó una llamada si hay concurrencia o cambios entre callbacks.
- Un segmento es el tramo observado después de `stage_created`, no una
  prueba de que constituye la partida completa. Si falta el alta, es segmento 0.
- `seconds_from_first_record` usa el contador monotónico; **no** es el
  tiempo musical del chart. `musical_beat` se deja vacío deliberadamente.
- Las ventanas `GROOVE_NATIVE` no disponen de token; las
  `GROOVE_NATIVE2` sí, pero su identidad es válida solo durante una sesión.
  Ninguno de los registros por sí solo permite asignar un juicio
  Perfect/Good/Miss o determinar qué botón físico se pulsó.
- Una llamada de gameplay es una **acción observada**, no una definición
  completa de cue con todos sus sonidos, inputs, fases y duración.

Siguiente paso seguro: registrar una ejecución de un minijuego original
y del mismo minijuego dentro de un remix; comparar los CSV y relacionar
las secuencias con un reloj musical y el código ARM64. Aún se requiere
verificación sobre Switch antes de añadir hooks de reloj o hilo.
