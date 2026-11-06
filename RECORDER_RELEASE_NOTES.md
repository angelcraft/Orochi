# Groove Recorder · Laboratorio

**Nintendo Switch OLED, Atmosphère en emuMMC, Groove 1.0.0.**
Title ID `0100D9F01D474000`. **El arranque y la grabación en Switch están pendientes de prueba.**

## Preparación en Windows

1. Extrae este paquete en el PC. Necesitas Python 3.10 o posterior.
2. Con la Switch apagada, monta la SD en el PC. Conserva una copia de la SD y de tu partida.
3. Ejecuta `preparar_recorder_windows.cmd` con el `main.npdm` original de tu ExeFS. El archivo `main` debe estar al lado. En este PC ya están en `C:\Users\User\Downloads\RhythmHeavenGroove-Android\GrooveSwitch_Work\source\ExeFS`.
4. Indica la raíz de la SD, por ejemplo `E:\`. El preparador lee la SD, valida el Build ID y ambos SHA-256 y rechaza conflictos ExeFS e IPS desconocidos para los módulos detectados. Si rechaza un archivo, conserva ese archivo. El IPS +240 conocido se reconoce por hash.
5. Se genera `GrooveRecorder-LAB.zip` solo en el PC. Contiene tu NPDM modificado localmente. Guárdalo en privado. El ZIP distribuido por CI contiene el módulo, el preparador, el lector, el catálogo y los registros de compilación.

## Primera prueba y reversión

1. Si el preparador pasó y la SD sigue en el mismo estado, copia manualmente **solo** `main.npdm` y `subsdk1` desde la carpeta `atmosphere/contents/0100D9F01D474000/exefs/` del ZIP local a la misma ruta de la SD. Cancela si Windows ofrece reemplazar archivos.
2. Expulsa la SD, arranca en emuMMC y abre Groove normalmente. Juega unos 30 segundos a Pasar por el anillo, vuelve al menú y cierra el juego.
3. Si falla el arranque, anota la versión de Atmosphère y el código de error. Si arranca, busca `Orochi/groove-recorder.log` en la raíz de la SD. Copia el registro al PC y conviértelo desde la carpeta del lector:

   ```powershell
   py -3 read_groove_recorder.py groove-recorder.log eventos.jsonl cobertura.json
   ```

4. Con la Switch apagada, elimina únicamente los dos archivos copiados por la prueba. Comprueba sus hashes contra `npdm-preflight.json` del ZIP local si hay dudas. Conserva el registro y los IPS. Verifica que el juego vuelve a arrancar.

## Alcance de la prueba

- CI compila el NSO AArch64, prueba el buffer y ejecuta las pruebas Python. Las guardas de entrada, los desplazamientos y el Build ID pertenecen al ejecutable 1.0.0.
- 84 acciones catalogadas en 32 clases de escena, más solicitudes de escena, esperas, SFX, BGM y secuencias. El ID de escena común representa la última escena creada. El contador es del sistema.
- Los campos de beat musical, input esperado, pulsaciones y juicios quedan sin resolver. El buffer finito indica pérdidas y el archivo crece hasta el límite del sistema de archivos o del espacio disponible.
- Los diagnósticos de depuración distinguen entrada al registrador, rechazo de hook, fallo de montaje, fallo de apertura y fallo de escritura. La sesión y las acciones se guardan en SD si el montaje y la escritura funcionan.

## Permisos

El preparador añade el permiso `0x74` a ACI0 y ACID. El original carece del grupo correspondiente. Se añade un descriptor por sección, se actualizan sus tamaños y se verifica el hash de salida. Atmosphère 1.12.1 valida la firma del ACID de la aplicación base y emplea su información de verificación, mientras comprueba las capacidades del NPDM redirigido. Mesosphère también exige un handle real y un mapeo válido. La prueba de grabación añade también el bit de acceso a SD (21) en los descriptores de sistema de archivos de ACI0 y ACID. El original solo tiene el bit de depuración y fs.mitm reenvía al servicio de Horizon la apertura de SD de los juegos. No se añaden servicios ni permisos de depuración. El acceso efectivo se comprobará en la consola. La prueba conserva la verificación global y el contenido instalado.

[Loader de Atmosphère 1.12.1](https://github.com/Atmosphere-NX/Atmosphere/blob/1.12.1/stratosphere/loader/source/ldr_meta.cpp) · [Validación del proceso](https://github.com/Atmosphere-NX/Atmosphere/blob/1.12.1/stratosphere/loader/source/ldr_process_creation.cpp) · [Código del SVC](https://github.com/Atmosphere-NX/Atmosphere/blob/1.12.1/libraries/libmesosphere/source/svc/kern_svc_process_memory.cpp)
