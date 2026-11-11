#!/usr/bin/env python3
#
# translations.py
# 2026-11-11
# Version: v1.0.0
#
# PURPOSE:
# The translations of the app's windows, used by i18n.py: one dictionary per
# language, from the English text (as written in _("...") or N_("...") in
# the code) to the translation. Text with values in it keeps the same
# {names}; tests/test_i18n.py checks that every text in the code has a
# translation here and that the {names} match. A missing text is shown in
# English.
#
# To add or change a text: change it in the code, then add the same English
# text here in every language. To add a language: add its code to
# i18n.LANGUAGES and a dictionary here.
#
# The Help guide (gui_help.py) and the documents the app writes stay in
# English.

CATALOGS = {}

# Spanish
CATALOGS['es'] = {
    "High (more shots)":
        "Alta (más capturas)",
    "Normal (recommended)":
        "Normal (recomendada)",
    "Low (fewer shots)":
        "Baja (menos capturas)",
    "Custom":
        "Personalizada",
    "Finished state (before next change)":
        "Estado final (antes del siguiente cambio)",
    "Right after each change":
        "Justo después de cada cambio",
    "System Theme":
        "Tema del sistema",
    "Light Theme":
        "Tema claro",
    "Dark Theme":
        "Tema oscuro",
    "seconds":
        "segundos",
    "File":
        "Archivo",
    "View":
        "Ver",
    "Help":
        "Ayuda",
    "Check for updates":
        "Buscar actualizaciones",
    "Checking for updates...":
        "Buscando actualizaciones...",
    "✓ Up to date":
        "✓ Actualizado",
    "Update available: v{v}":
        "Actualización disponible: v{v}",
    "Update check failed. Try again":
        "No se pudieron buscar actualizaciones. Reintentar",
    "Update checks turned off":
        "Búsqueda de actualizaciones desactivada",
    "Advanced Settings":
        "Configuración avanzada",
    "Output":
        "Salida",
    "Region":
        "Región",
    "Run":
        "Ejecución",
    "Name for this preset:":
        "Nombre de este ajuste predefinido:",
    "the system language":
        "el idioma del sistema",
    "Ready":
        "Listo",
    "Record Screen...":
        "Grabar pantalla...",
    "Choose Source Folder...":
        "Elegir carpeta de origen...",
    "Choose Output Folder...":
        "Elegir carpeta de salida...",
    "Open Source Folder":
        "Abrir carpeta de origen",
    "Open Output Folder":
        "Abrir carpeta de salida",
    "Archive Selected Recordings...":
        "Archivar grabaciones seleccionadas...",
    "Archived Recordings...":
        "Grabaciones archivadas...",
    "Exit":
        "Salir",
    "Language":
        "Idioma",
    "System Language":
        "Idioma del sistema",
    "Advanced Settings...":
        "Configuración avanzada...",
    "Steps":
        "Pasos",
    "Log":
        "Registro",
    "Keyboard Shortcuts":
        "Atajos de teclado",
    "Online Documentation":
        "Documentación en línea",
    "Report a Problem...":
        "Informar de un problema...",
    "Suggest an Idea...":
        "Sugerir una idea...",
    "Project on GitHub":
        "Proyecto en GitHub",
    "Release Notes":
        "Notas de la versión",
    "Check for Updates...":
        "Buscar actualizaciones...",
    "Check for Updates Automatically":
        "Buscar actualizaciones automáticamente",
    "Refresh":
        "Actualizar",
    "● Record":
        "● Grabar",
    "Recording":
        "Grabación",
    "Status":
        "Estado",
    "Process":
        "Procesar",
    "Archive...":
        "Archivar...",
    "Process All":
        "Procesar todo",
    "Process Selected":
        "Procesar selección",
    "Cancel":
        "Cancelar",
    "Highlight what changed in each step (red box)":
        "Resaltar lo que cambió en cada paso (recuadro rojo)",
    "Blur passwords, keys, IP and email addresses":
        "Difuminar contraseñas, claves, direcciones IP y de correo",
    "Remove duplicate screenshots":
        "Quitar capturas duplicadas",
    "Timing":
        "Tiempos",
    "Detection":
        "Detección",
    "Built-in presets cannot be deleted.":
        "Los ajustes predefinidos integrados no se pueden eliminar.",
    "Threshold":
        "Umbral",
    "Merge changes within":
        "Combinar cambios en",
    "Min gap":
        "Intervalo mínimo",
    "Force a shot after":
        "Forzar captura tras",
    "Lead":
        "Anticipación",
    "Settle":
        "Estabilización",
    "Analyze fps":
        "Fotogramas analizados por segundo",
    "Analyze width":
        "Ancho de análisis",
    "Duplicate tolerance":
        "Tolerancia de duplicados",
    "Choose both a source folder and an output folder.":
        "Elija una carpeta de origen y una de salida.",
    "Done":
        "Hecho",
    "New":
        "Nuevo",
    "Select one or more videos first (Ctrl+click or Shift+click for several).":
        "Seleccione primero uno o más vídeos (Ctrl+clic o Mayús+clic para varios).",
    "This recording is already processed.":
        "Esta grabación ya está procesada.",
    "No videos to process. Put recordings in the source folder, then click Refresh.":
        "No hay vídeos que procesar. Ponga grabaciones en la carpeta de origen y haga clic en Actualizar.",
    "Queued":
        "En cola",
    "Cancelling...":
        "Cancelando...",
    "Finished: {ok} processed, {skipped} skipped, {failed} failed":
        "Terminado: {ok} procesados, {skipped} omitidos, {failed} con errores",
    "Recordings":
        "Grabaciones",
    "Image format":
        "Formato de imagen",
    "Dates":
        "Fechas",
    "Times":
        "Horas",
    "Preset '{name}' applied.":
        "Ajuste predefinido «{name}» aplicado.",
    "Saved preset '{name}'.":
        "Ajuste predefinido «{name}» guardado.",
    "Delete the preset \"{name}\"?":
        "¿Eliminar el ajuste predefinido «{name}»?",
    "{app} will use {language} the next time it starts.":
        "{app} usará {language} la próxima vez que se inicie.",
    "{name} must be between {low} and {high} (got {value}).":
        "{name} debe estar entre {low} y {high} (valor: {value}).",
    "{name} must be {low} or more (got {value}).":
        "{name} debe ser {low} o más (valor: {value}).",
    "One of the settings is invalid. Check the values and try again.":
        "Uno de los ajustes no es válido. Revise los valores e inténtelo de nuevo.",
    "Process again with the current settings? The previous screenshots, captions, and exports are kept in a previous-<date> folder next to the new ones.\n\nNo skips the finished ones.":
        "¿Procesar de nuevo con los ajustes actuales? Las capturas, los pies de foto y las exportaciones anteriores se guardan en una carpeta previous-<fecha> junto a las nuevas.\n\nNo omite las ya terminadas.",
    "The source folder changed. Click Refresh to reload the video list, then try again.":
        "La carpeta de origen cambió. Haga clic en Actualizar para recargar la lista de vídeos e inténtelo de nuevo.",
    ", {n} cancelled":
        ", {n} cancelados",
    "See the Log tab or screencap.log in the output folder for details.":
        "Consulte la pestaña Registro o screencap.log en la carpeta de salida para más detalles.",
    "This video has not been processed yet.":
        "Este vídeo aún no se ha procesado.",
    "Unexpected error: {error}\n\nDetails are in the Log tab.":
        "Error inesperado: {error}\n\nLos detalles están en la pestaña Registro.",
    "About {app}":
        "Acerca de {app}",
    "Include subfolders":
        "Incluir subcarpetas",
    "Settings":
        "Ajustes",
    "Preset":
        "Ajuste predefinido",
    "Sensitivity":
        "Sensibilidad",
    "Screenshot taken":
        "Captura tomada",
    "Captions from narration":
        "Pies de foto desde la narración",
    "Delete Preset":
        "Eliminar ajuste predefinido",
    "Save as Preset...":
        "Guardar como ajuste predefinido...",
    "These apply to the next run. To keep them, save them as a preset (Save as Preset in the main window).":
        "Se aplican a la próxima ejecución. Para conservarlos, guárdelos como ajuste predefinido (Guardar como ajuste predefinido en la ventana principal).",
    "Merge changes closer than":
        "Combinar cambios más cercanos que",
    "Minimum time between screenshots":
        "Tiempo mínimo entre capturas",
    "Take a screenshot anyway after":
        "Tomar una captura de todos modos tras",
    "Screenshot before the next change":
        "Captura antes del siguiente cambio",
    "Wait after a change (right-after mode)":
        "Espera tras un cambio (modo justo después)",
    "Frames checked per second":
        "Fotogramas analizados por segundo",
    "0 = every frame":
        "0 = todos los fotogramas",
    "Analysis width":
        "Ancho de análisis",
    "pixels, 0 = full size":
        "píxeles, 0 = tamaño completo",
    "Duplicate when it differs by at most":
        "Duplicado si difiere como máximo en",
    "percent":
        "por ciento",
    "Also blur":
        "Difuminar también",
    "Regular expressions, separated by semicolons; for example corp\\.example\\.com;TICKET-\\d+":
        "Expresiones regulares separadas por punto y coma; por ejemplo corp\\.example\\.com;TICKET-\\d+",
    "For the date on exported documents and the times the app shows. System setting follows Windows, macOS, or Linux.":
        "Para la fecha de los documentos exportados y las horas que muestra la aplicación. Configuración del sistema sigue a Windows, macOS o Linux.",
    "Reprocess recordings that are already done":
        "Volver a procesar las grabaciones ya terminadas",
    "Dry run: count the steps only, save nothing":
        "Simulación: solo contar los pasos, no guardar nada",
    "Reset to Defaults":
        "Restablecer valores predeterminados",
    "Close":
        "Cerrar",
    "Clear":
        "Borrar",
    "Deleted preset '{name}'.":
        "Ajuste predefinido «{name}» eliminado.",
    "Or untick Captions from narration.":
        "O desmarque Pies de foto desde la narración.",
    "Source folder does not exist yet: {folder}":
        "La carpeta de origen aún no existe: {folder}",
    "{n} recording(s) found in {folder}":
        "{n} grabación(es) encontrada(s) en {folder}",
    "No .mp4, .mov, or .mkv files in {folder}":
        "No hay archivos .mp4, .mov ni .mkv en {folder}",
    "{n} of the selected recordings are already processed.":
        "{n} de las grabaciones seleccionadas ya están procesadas.",
    "Processing":
        "Procesando",
    "Saved {name}. It is not in the list because the Recordings folder changed.":
        "{name} guardado. No aparece en la lista porque la carpeta Grabaciones cambió.",
    "Saved {name}. Click Process Selected to make the screenshots.":
        "{name} guardado. Haga clic en Procesar selección para crear las capturas.",
    "Processing is still running. Cancel it and exit?":
        "El procesamiento sigue en curso. ¿Cancelarlo y salir?",
    "Browse...":
        "Examinar...",
    "Open":
        "Abrir",
    "Model":
        "Modelo",
    "Model (not installed)":
        "Modelo (no instalado)",
    "Replace the preset \"{name}\"?":
        "¿Reemplazar el ajuste predefinido «{name}»?",
    "Could not save the preset:\n{error}":
        "No se pudo guardar el ajuste predefinido:\n{error}",
    "Could not open {path}:\n{error}":
        "No se pudo abrir {path}:\n{error}",
    "Cancelled":
        "Cancelado",
    "Dry run":
        "Simulación",
    "Done (captions failed)":
        "Hecho (fallaron los pies de foto)",
    "Version {version}":
        "Versión {version}",
    "{name} must be a number (got '{value}').":
        "{name} debe ser un número (valor: «{value}»).",
    "Done (skipped)":
        "Hecho (omitido)",
    "Transcribing":
        "Transcribiendo",
    "Failed":
        "Error",
    "'{pattern}' in Also blur is not a valid pattern: {error}":
        "«{pattern}» en Difuminar también no es un patrón válido: {error}",
    "Processing {percent}%":
        "Procesando {percent}%",
    "No microphone":
        "Sin micrófono",
    "Whole screen is the whole X11 screen. The small Recording window shows in the recording when it is inside the recorded area; it sits in the bottom-right corner.":
        "Pantalla completa es toda la pantalla X11. La pequeña ventana Grabación aparece en la grabación si está dentro del área grabada; se sitúa en la esquina inferior derecha.",
    "To record the computer's sound, FFmpeg needs PulseAudio or PipeWire (pulse) support.":
        "Para grabar el sonido del equipo, FFmpeg necesita compatibilidad con PulseAudio o PipeWire (pulse).",
    "Whole screen":
        "Pantalla completa",
    "One window (click it after Start)":
        "Una ventana (haga clic en ella tras Iniciar)",
    "An area (draw it after Start)":
        "Un área (dibújela tras Iniciar)",
    "macOS asks for permission the first time: allow this app (or Terminal) under System Settings > Privacy & Security > Screen Recording, and Input Monitoring for keys. Whole screen is the main display.":
        "macOS pide permiso la primera vez: permita esta aplicación (o Terminal) en Ajustes del Sistema > Privacidad y seguridad > Grabación de pantalla, y en Monitorización de entrada para las teclas. Pantalla completa es la pantalla principal.",
    "Whole screen is all monitors. The small Recording window is left out of the recording.":
        "Pantalla completa son todos los monitores. La pequeña ventana Grabación queda fuera de la grabación.",
    "To record the computer's sound, switch on \"Stereo Mix\" (Sound settings > More sound settings > Recording, right-click > Show Disabled Devices) or install a virtual audio cable, then open this window again.":
        "Para grabar el sonido del equipo, active «Mezcla estéreo» (Configuración de sonido > Más opciones de sonido > Grabar, clic derecho > Mostrar dispositivos deshabilitados) o instale un cable de audio virtual, y vuelva a abrir esta ventana.",
    "To record the computer's sound, install a loopback driver such as BlackHole and send the sound to it, then open this window again.":
        "Para grabar el sonido del equipo, instale un controlador de bucle como BlackHole y envíele el sonido; luego vuelva a abrir esta ventana.",
    "Note keys pressed (Enter, Tab, shortcuts such as Ctrl+S). Typed text is never saved.":
        "Anotar las teclas pulsadas (Intro, Tab, atajos como Ctrl+S). El texto escrito nunca se guarda.",
    "Record Screen":
        "Grabar pantalla",
    "Noting keys pressed is switched off by your administrator.":
        "Su administrador ha desactivado la anotación de teclas.",
    "Drag over the area to record. Esc cancels.":
        "Arrastre sobre el área que desea grabar. Esc cancela.",
    "Click the window to record. Esc cancels.":
        "Haga clic en la ventana que desea grabar. Esc cancela.",
    "Paused (admin prompt)":
        "En pausa (aviso de administrador)",
    "Saving...":
        "Guardando...",
    "Discarding...":
        "Descartando...",
    "Recording discarded.":
        "Grabación descartada.",
    "Start Recording":
        "Iniciar grabación",
    "That window could not be found. Choose Whole screen or An area instead.":
        "No se encontró esa ventana. Elija Pantalla completa o Un área.",
    "Starting...":
        "Iniciando...",
    "Stop":
        "Detener",
    "Discard":
        "Descartar",
    "Recording {time}":
        "Grabando {time}",
    "Recording did not work.":
        "La grabación no funcionó.",
    "Do the task as usual. Each click is noted, so the steps get a red ring where you clicked and a first-draft caption such as Click \"Next\". Stop when you are done.":
        "Haga la tarea como siempre. Cada clic se anota, así que los pasos reciben un anillo rojo donde hizo clic y un primer borrador de pie de foto como Haga clic en «Siguiente». Detenga la grabación al terminar.",
    "Record":
        "Grabar",
    "Make the screenshots when I stop":
        "Crear las capturas al detener",
    "Microphone":
        "Micrófono",
    "Talk through the steps to turn your words into captions later (Captions From Narration in the Steps tab).":
        "Narre los pasos para convertir sus palabras en pies de foto más tarde (Pies de foto desde la narración en la pestaña Pasos).",
    "Also record the computer's sound (videos, alerts)":
        "Grabar también el sonido del equipo (vídeos, alertas)",
    "The recording could not be saved.":
        "No se pudo guardar la grabación.",
    "The Recordings folder cannot be used: {error}":
        "No se puede usar la carpeta Grabaciones: {error}",
    "FFmpeg did not start recording. It said:":
        "FFmpeg no empezó a grabar. Dijo:",
    "Select one or more recordings to archive (Ctrl+click or Shift+click for several).":
        "Seleccione una o más grabaciones para archivar (Ctrl+clic o Mayús+clic para varias).",
    "Archived Recordings":
        "Grabaciones archivadas",
    "Archive \"{name}\"?":
        "¿Archivar «{name}»?",
    "Archive these {n} recordings?":
        "¿Archivar estas {n} grabaciones?",
    "Bring it back any time with File > Archived Recordings.":
        "Recupérela cuando quiera con Archivo > Grabaciones archivadas.",
    "Archived":
        "Archivada",
    "Size":
        "Tamaño",
    "Restore":
        "Restaurar",
    "Archiving":
        "Archivando",
    "Archived {n} recording(s).":
        "{n} grabación(es) archivada(s).",
    "Some recordings were not archived (nothing of theirs was deleted):":
        "Algunas grabaciones no se archivaron (no se eliminó nada de ellas):",
    "Restored {n} recording(s).":
        "{n} grabación(es) restaurada(s).",
    "Shrink videos when archiving (smaller files, slightly lower picture quality)":
        "Reducir los vídeos al archivar (archivos más pequeños, calidad de imagen algo menor)",
    "Open Folder":
        "Abrir carpeta",
    "Delete...":
        "Eliminar...",
    "{n} archive(s), {size}, in {folder}. Restore puts the recording and its screenshots back in your recordings and output folders.":
        "{n} archivo(s), {size}, en {folder}. Restaurar devuelve la grabación y sus capturas a sus carpetas de grabaciones y de salida.",
    "Nothing archived yet. Archive recordings from the File menu or by right-clicking them in the list. They are kept in {folder}.":
        "Aún no hay nada archivado. Archive grabaciones desde el menú Archivo o haciendo clic derecho sobre ellas en la lista. Se guardan en {folder}.",
    "Some archives were not restored:":
        "Algunos archivos no se restauraron:",
    "Delete {n} archive(s) for good?\n\nThe recordings, screenshots, and captions in them cannot be brought back.":
        "¿Eliminar {n} archivo(s) definitivamente?\n\nLas grabaciones, capturas y pies de foto que contienen no se podrán recuperar.",
    "{n} failed.":
        "{n} con errores.",
    "The video is re-encoded to take less space.":
        "El vídeo se vuelve a codificar para ocupar menos espacio.",
    "The recording, its screenshots, captions, and exports are packed into one file in the \"{folder}\" folder in your output folder, and taken off the list.":
        "La grabación, sus capturas, pies de foto y exportaciones se empaquetan en un archivo en la carpeta «{folder}» de su carpeta de salida y se quitan de la lista.",
    "({n} of {total}, {percent}%)":
        "({n} de {total}, {percent}%)",
    "Logo and Template":
        "Logotipo y plantilla",
    "Click a blur box to switch it off (or back on). Esc cancels.":
        "Haga clic en un recuadro de difuminado para desactivarlo (o reactivarlo). Esc cancela.",
    "Arrow added.":
        "Flecha añadida.",
    "Label text:":
        "Texto de la etiqueta:",
    "Annotations cleared on this step. Click Save Changes to keep it.":
        "Anotaciones borradas en este paso. Haga clic en Guardar cambios para conservarlo.",
    "Save your changes to this recording's steps first?":
        "¿Guardar primero los cambios en los pasos de esta grabación?",
    "Saving steps...":
        "Guardando pasos...",
    "Select a processed video to edit its steps.":
        "Seleccione un vídeo procesado para editar sus pasos.",
    "Screenshot":
        "Captura",
    "Original frame":
        "Fotograma original",
    "Crop":
        "Recortar",
    "Crop All Steps (drag on the picture)":
        "Recortar todos los pasos (arrastre sobre la imagen)",
    "Crop This Step Only (drag on the picture)":
        "Recortar solo este paso (arrastre sobre la imagen)",
    "No Crop on This Step":
        "Sin recorte en este paso",
    "Clear All Crops":
        "Quitar todos los recortes",
    "Blur":
        "Difuminar",
    "Add Blur Box (drag on the picture)":
        "Añadir recuadro de difuminado (arrastre sobre la imagen)",
    "Un-blur / Re-blur (click a box)":
        "Quitar / volver a difuminar (clic en un recuadro)",
    "Blur This Step":
        "Difuminar este paso",
    "Re-scan All Steps for Sensitive Text":
        "Volver a buscar texto sensible en todos los pasos",
    "Annotate":
        "Anotar",
    "Add Arrow (drag from the start to the tip)":
        "Añadir flecha (arrastre desde el inicio hasta la punta)",
    "Add Number (click where it goes)":
        "Añadir número (clic donde va)",
    "Add Text Label (click where it starts)":
        "Añadir etiqueta de texto (clic donde empieza)",
    "Edit or Remove (click an annotation)":
        "Editar o quitar (clic en una anotación)",
    "Clear Annotations on This Step":
        "Borrar anotaciones de este paso",
    "Highlight":
        "Resaltado",
    "Red Box on This Step":
        "Recuadro rojo en este paso",
    "Zoomed Inset on This Step":
        "Ampliación en este paso",
    "Animated Clip of This Step (GIF)":
        "Clip animado de este paso (GIF)",
    "Captions From Narration":
        "Pies de foto desde la narración",
    "Word":
        "Word",
    "Save Changes":
        "Guardar cambios",
    "Open Image":
        "Abrir imagen",
    "Open Animated Clip":
        "Abrir clip animado",
    "Open steps.md":
        "Abrir steps.md",
    "Open Exports Folder":
        "Abrir carpeta de exportaciones",
    "Unsaved changes":
        "Cambios sin guardar",
    "Step {n} of {total} at {time}":
        "Paso {n} de {total} en {time}",
    "no highlight (first step, nothing changed, or whole screen changed)":
        "sin resaltado (primer paso, nada cambió o cambió toda la pantalla)",
    "There are no deleted steps to restore.":
        "No hay pasos eliminados que restaurar.",
    "The original recording was not found, so a clip cannot be made. It may have been moved or deleted from the source folder.":
        "No se encontró la grabación original, así que no se puede crear un clip. Puede que se haya movido o eliminado de la carpeta de origen.",
    "The animated clip is made when you click Save Changes.":
        "El clip animado se crea al hacer clic en Guardar cambios.",
    "Clip removed from this step.":
        "Clip quitado de este paso.",
    "Logo":
        "Logotipo",
    "Word template":
        "Plantilla de Word",
    "Save the starter Word template":
        "Guardar la plantilla de Word inicial",
    "No blur box there.":
        "No hay ningún recuadro de difuminado ahí.",
    "Removed the hand-drawn blur box.":
        "Recuadro de difuminado dibujado a mano quitado.",
    "Drag from where the arrow starts to what it points at. Press Esc to cancel.":
        "Arrastre desde donde empieza la flecha hasta lo que señala. Pulse Esc para cancelar.",
    "Drag a rectangle around the area. Press Esc to cancel.":
        "Dibuje un rectángulo alrededor del área. Pulse Esc para cancelar.",
    "Cancelled.":
        "Cancelado.",
    "Rectangle too small; nothing changed.":
        "Rectángulo demasiado pequeño; no se cambió nada.",
    "This step has no annotations.":
        "Este paso no tiene anotaciones.",
    "Arrow too short; drag from where it starts to its tip.":
        "Flecha demasiado corta; arrastre desde el inicio hasta la punta.",
    "Click Save Changes to keep it.":
        "Haga clic en Guardar cambios para conservarlo.",
    "No annotation there.":
        "No hay ninguna anotación ahí.",
    "Label text (clear it to remove the label):":
        "Texto de la etiqueta (bórrelo para quitar la etiqueta):",
    "Label changed.":
        "Etiqueta cambiada.",
    "Label removed.":
        "Etiqueta quitada.",
    "Discard all unsaved changes?":
        "¿Descartar todos los cambios sin guardar?",
    "This step has no animated clip. Switch it on in the Highlight menu, then click Save Changes.":
        "Este paso no tiene clip animado. Actívelo en el menú Resaltado y haga clic en Guardar cambios.",
    "The original recording was not found. It may have been moved or deleted from the source folder.":
        "No se encontró la grabación original. Puede que se haya movido o eliminado de la carpeta de origen.",
    "This recording has no audio, so there is no narration to use.":
        "Esta grabación no tiene audio, así que no hay narración que usar.",
    "Move Up":
        "Subir",
    "Move Down":
        "Bajar",
    "Delete Step":
        "Eliminar paso",
    "Restore Deleted":
        "Restaurar eliminados",
    "Next >":
        "Siguiente >",
    "Play in VLC":
        "Reproducir en VLC",
    "No steps. Use Restore Deleted to bring steps back.":
        "No hay pasos. Use Restaurar eliminados para recuperarlos.",
    ", {n} duplicate(s)":
        ", {n} duplicado(s)",
    "(this step only)":
        "(solo este paso)",
    "That step is already at the top of the list.":
        "Ese paso ya está al principio de la lista.",
    "That step is already at the bottom of the list.":
        "Ese paso ya está al final de la lista.",
    "Restored {n} step(s). Click Save Changes to keep them.":
        "{n} paso(s) restaurado(s). Haga clic en Guardar cambios para conservarlos.",
    "Save your changes before exporting?":
        "¿Guardar los cambios antes de exportar?",
    "The unblurred screenshots may show passwords, keys, or internal addresses. Export them anyway? The file name will include UNREDACTED.":
        "Las capturas sin difuminar pueden mostrar contraseñas, claves o direcciones internas. ¿Exportarlas de todos modos? El nombre del archivo incluirá UNREDACTED.",
    "Exporting {format}...":
        "Exportando {format}...",
    "Saved {name} and chose it as the Word template. Open it in Word to change how exports look.":
        "{name} guardado y elegido como plantilla de Word. Ábralo en Word para cambiar el aspecto de las exportaciones.",
    "Nothing has been exported yet.":
        "Aún no se ha exportado nada.",
    "Blur box added.":
        "Recuadro de difuminado añadido.",
    "Click where the number goes. Press Esc to cancel.":
        "Haga clic donde va el número. Pulse Esc para cancelar.",
    "Click where the label's top-left corner goes. Press Esc to cancel.":
        "Haga clic donde va la esquina superior izquierda de la etiqueta. Pulse Esc para cancelar.",
    "Click an annotation to edit or remove it. Press Esc to cancel.":
        "Haga clic en una anotación para editarla o quitarla. Pulse Esc para cancelar.",
    "Label added.":
        "Etiqueta añadida.",
    "Number to show (0 removes the marker):":
        "Número que se muestra (0 quita el marcador):",
    "Marker removed.":
        "Marcador quitado.",
    "Click ring removed.":
        "Anillo de clic quitado.",
    "Arrow removed.":
        "Flecha quitada.",
    "Original image is missing (deleted or moved).":
        "Falta la imagen original (eliminada o movida).",
    "FFmpeg is required for previews":
        "Se necesita FFmpeg para las vistas previas",
    "Saved. Newer changes are not saved yet: click Save Changes again.":
        "Guardado. Los cambios más recientes aún no se han guardado: vuelva a hacer clic en Guardar cambios.",
    "Transcribing narration with the {model} model. The first time, the model is downloaded, which can take a few minutes...":
        "Transcribiendo la narración con el modelo {model}. La primera vez se descarga el modelo, lo que puede tardar unos minutos...",
    "No speech was found in this recording.":
        "No se encontró voz en esta grabación.",
    "Whole recording:":
        "Toda la grabación:",
    "Blur sensitive info":
        "Difuminar información sensible",
    "Highlight changes":
        "Resaltar cambios",
    "Zoomed inset":
        "Ampliación",
    "Caption":
        "Pie de foto",
    "Document title":
        "Título del documento",
    "Version":
        "Versión",
    "Author":
        "Autor",
    "Export":
        "Exportar",
    "Logo and Template...":
        "Logotipo y plantilla...",
    "Unblurred copy":
        "Copia sin difuminar",
    "Open Exports":
        "Abrir exportaciones",
    "screen stable {start} to {end}":
        "pantalla estable de {start} a {end}",
    "Moved the step from position {old} to {new}. Use Up/Down (or < Prev / Next >) to look at other steps.":
        "Paso movido de la posición {old} a la {new}. Use Arriba/Abajo (o < Anterior / Siguiente >) para ver otros pasos.",
    "Exported {name}":
        "{name} exportado",
    "Logo and Word Template":
        "Logotipo y plantilla de Word",
    "Used for every export. The logo goes at the top of HTML, PDF, and Word documents. A Word template sets the fonts, colors, margins, and page header and footer of Word exports.":
        "Se usa en todas las exportaciones. El logotipo va en la parte superior de los documentos HTML, PDF y Word. Una plantilla de Word define las fuentes, los colores, los márgenes y el encabezado y pie de página de las exportaciones de Word.",
    "Pictures":
        "Imágenes",
    "All files":
        "Todos los archivos",
    "Word documents":
        "Documentos de Word",
    "Create Starter Template...":
        "Crear plantilla inicial...",
    "Saves the standard template. Open it in Word, change its styles and page header, save it, and choose it above.":
        "Guarda la plantilla estándar. Ábrala en Word, cambie sus estilos y el encabezado, guárdela y elíjala arriba.",
    "Drag a rectangle around the area to keep. Press Esc to cancel.":
        "Dibuje un rectángulo alrededor del área que desea conservar. Pulse Esc para cancelar.",
    "Drag a rectangle around the area to blur. Press Esc to cancel.":
        "Dibuje un rectángulo alrededor del área que desea difuminar. Pulse Esc para cancelar.",
    "Number {n} added.":
        "Número {n} añadido.",
    "No text; nothing added.":
        "Sin texto; no se añadió nada.",
    "Saving failed:\n{error}":
        "Error al guardar:\n{error}",
    "Saved {n} step(s) to {folder}":
        "{n} paso(s) guardado(s) en {folder}",
    "Opened {name} in VLC at {time}":
        "{name} abierto en VLC en {time}",
    "{name} has not been processed yet.":
        "{name} aún no se ha procesado.",
    "{n} removed":
        "{n} quitado(s)",
    "cropped to {w}x{h}":
        "recortado a {w}x{h}",
    "Export failed:\n{error}":
        "Error al exportar:\n{error}",
    "{item} cleared.":
        "{item}: borrado.",
    "Un-blurred: {reason}.":
        "Sin difuminar: {reason}.",
    "Blurred again: {reason}.":
        "Difuminado de nuevo: {reason}.",
    "detected text":
        "texto detectado",
    "Crop set to {w}x{h} at {x},{y} for all steps.":
        "Recorte de {w}x{h} en {x},{y} para todos los pasos.",
    "Crop set to {w}x{h} at {x},{y} for this step.":
        "Recorte de {w}x{h} en {x},{y} para este paso.",
    "Marker changed to {n}.":
        "Marcador cambiado a {n}.",
    "Remove this click ring?":
        "¿Quitar este anillo de clic?",
    "Remove this arrow?":
        "¿Quitar esta flecha?",
    "Filled {n} empty caption(s) from {passages} spoken passage(s). Captions you typed were kept. Review them, then Save Changes. Full text: {file}":
        "Se rellenaron {n} pie(s) de foto vacío(s) a partir de {passages} fragmento(s) hablado(s). Se conservaron los que usted escribió. Revíselos y luego Guardar cambios. Texto completo: {file}",
    "Choose a file: {item}":
        "Elegir un archivo: {item}",
    "{item} set for every export.":
        "{item}: definido para todas las exportaciones.",
    "Preview unavailable: {error}":
        "Vista previa no disponible: {error}",
    "System setting":
        "Configuración del sistema",
    "24-hour (14:05)":
        "24 horas (14:05)",
    "12-hour (2:05 PM)":
        "12 horas (2:05 PM)",
    "2026-11-22 (year-month-day)":
        "2026-11-22 (año-mes-día)",
    "11/22/2026 (month/day/year)":
        "11/22/2026 (mes/día/año)",
    "22/11/2026 (day/month/year)":
        "22/11/2026 (día/mes/año)",
    "22.11.2026 (day.month.year)":
        "22.11.2026 (día.mes.año)",
    "< Prev":
        "< Anterior",
}

# French
CATALOGS['fr'] = {
    "High (more shots)":
        "Élevée (plus de captures)",
    "Normal (recommended)":
        "Normale (recommandée)",
    "Low (fewer shots)":
        "Faible (moins de captures)",
    "Custom":
        "Personnalisée",
    "Finished state (before next change)":
        "État final (avant le changement suivant)",
    "Right after each change":
        "Juste après chaque changement",
    "System Theme":
        "Thème du système",
    "Light Theme":
        "Thème clair",
    "Dark Theme":
        "Thème sombre",
    "seconds":
        "secondes",
    "File":
        "Fichier",
    "View":
        "Affichage",
    "Help":
        "Aide",
    "Check for updates":
        "Rechercher des mises à jour",
    "Checking for updates...":
        "Recherche de mises à jour...",
    "✓ Up to date":
        "✓ À jour",
    "Update available: v{v}":
        "Mise à jour disponible : v{v}",
    "Update check failed. Try again":
        "Échec de la recherche de mises à jour. Réessayer",
    "Update checks turned off":
        "Recherche de mises à jour désactivée",
    "Advanced Settings":
        "Paramètres avancés",
    "Output":
        "Sortie",
    "Region":
        "Région",
    "Run":
        "Exécution",
    "Name for this preset:":
        "Nom de ce préréglage :",
    "the system language":
        "la langue du système",
    "Ready":
        "Prêt",
    "Record Screen...":
        "Enregistrer l'écran...",
    "Choose Source Folder...":
        "Choisir le dossier source...",
    "Choose Output Folder...":
        "Choisir le dossier de sortie...",
    "Open Source Folder":
        "Ouvrir le dossier source",
    "Open Output Folder":
        "Ouvrir le dossier de sortie",
    "Archive Selected Recordings...":
        "Archiver les enregistrements sélectionnés...",
    "Archived Recordings...":
        "Enregistrements archivés...",
    "Exit":
        "Quitter",
    "Language":
        "Langue",
    "System Language":
        "Langue du système",
    "Advanced Settings...":
        "Paramètres avancés...",
    "Steps":
        "Étapes",
    "Log":
        "Journal",
    "Keyboard Shortcuts":
        "Raccourcis clavier",
    "Online Documentation":
        "Documentation en ligne",
    "Report a Problem...":
        "Signaler un problème...",
    "Suggest an Idea...":
        "Suggérer une idée...",
    "Project on GitHub":
        "Projet sur GitHub",
    "Release Notes":
        "Notes de version",
    "Check for Updates...":
        "Rechercher des mises à jour...",
    "Check for Updates Automatically":
        "Rechercher les mises à jour automatiquement",
    "Refresh":
        "Actualiser",
    "● Record":
        "● Enregistrer",
    "Recording":
        "Enregistrement",
    "Status":
        "État",
    "Process":
        "Traiter",
    "Archive...":
        "Archiver...",
    "Process All":
        "Tout traiter",
    "Process Selected":
        "Traiter la sélection",
    "Cancel":
        "Annuler",
    "Highlight what changed in each step (red box)":
        "Mettre en évidence ce qui a changé à chaque étape (cadre rouge)",
    "Blur passwords, keys, IP and email addresses":
        "Flouter les mots de passe, clés, adresses IP et e-mail",
    "Remove duplicate screenshots":
        "Supprimer les captures en double",
    "Timing":
        "Minutage",
    "Detection":
        "Détection",
    "Built-in presets cannot be deleted.":
        "Les préréglages intégrés ne peuvent pas être supprimés.",
    "Threshold":
        "Seuil",
    "Merge changes within":
        "Fusionner les changements dans",
    "Min gap":
        "Intervalle minimal",
    "Force a shot after":
        "Forcer une capture après",
    "Lead":
        "Avance",
    "Settle":
        "Stabilisation",
    "Analyze fps":
        "Images analysées par seconde",
    "Analyze width":
        "Largeur d'analyse",
    "Duplicate tolerance":
        "Tolérance des doublons",
    "Choose both a source folder and an output folder.":
        "Choisissez un dossier source et un dossier de sortie.",
    "Done":
        "Terminé",
    "New":
        "Nouveau",
    "Select one or more videos first (Ctrl+click or Shift+click for several).":
        "Sélectionnez d'abord une ou plusieurs vidéos (Ctrl+clic ou Maj+clic pour plusieurs).",
    "This recording is already processed.":
        "Cet enregistrement est déjà traité.",
    "No videos to process. Put recordings in the source folder, then click Refresh.":
        "Aucune vidéo à traiter. Placez des enregistrements dans le dossier source, puis cliquez sur Actualiser.",
    "Queued":
        "En attente",
    "Cancelling...":
        "Annulation...",
    "Finished: {ok} processed, {skipped} skipped, {failed} failed":
        "Terminé : {ok} traités, {skipped} ignorés, {failed} en échec",
    "Recordings":
        "Enregistrements",
    "Image format":
        "Format d'image",
    "Dates":
        "Dates",
    "Times":
        "Heures",
    "Preset '{name}' applied.":
        "Préréglage « {name} » appliqué.",
    "Saved preset '{name}'.":
        "Préréglage « {name} » enregistré.",
    "Delete the preset \"{name}\"?":
        "Supprimer le préréglage « {name} » ?",
    "{app} will use {language} the next time it starts.":
        "{app} utilisera {language} au prochain démarrage.",
    "{name} must be between {low} and {high} (got {value}).":
        "{name} doit être compris entre {low} et {high} (valeur : {value}).",
    "{name} must be {low} or more (got {value}).":
        "{name} doit être supérieur ou égal à {low} (valeur : {value}).",
    "One of the settings is invalid. Check the values and try again.":
        "L'un des paramètres n'est pas valide. Vérifiez les valeurs et réessayez.",
    "Process again with the current settings? The previous screenshots, captions, and exports are kept in a previous-<date> folder next to the new ones.\n\nNo skips the finished ones.":
        "Traiter à nouveau avec les paramètres actuels ? Les captures, légendes et exportations précédentes sont conservées dans un dossier previous-<date> à côté des nouvelles.\n\nNon ignore celles déjà terminées.",
    "The source folder changed. Click Refresh to reload the video list, then try again.":
        "Le dossier source a changé. Cliquez sur Actualiser pour recharger la liste des vidéos, puis réessayez.",
    ", {n} cancelled":
        ", {n} annulés",
    "See the Log tab or screencap.log in the output folder for details.":
        "Consultez l'onglet Journal ou screencap.log dans le dossier de sortie pour plus de détails.",
    "This video has not been processed yet.":
        "Cette vidéo n'a pas encore été traitée.",
    "Unexpected error: {error}\n\nDetails are in the Log tab.":
        "Erreur inattendue : {error}\n\nLes détails se trouvent dans l'onglet Journal.",
    "About {app}":
        "À propos de {app}",
    "Include subfolders":
        "Inclure les sous-dossiers",
    "Settings":
        "Paramètres",
    "Preset":
        "Préréglage",
    "Sensitivity":
        "Sensibilité",
    "Screenshot taken":
        "Capture prise",
    "Captions from narration":
        "Légendes à partir de la narration",
    "Delete Preset":
        "Supprimer le préréglage",
    "Save as Preset...":
        "Enregistrer comme préréglage...",
    "These apply to the next run. To keep them, save them as a preset (Save as Preset in the main window).":
        "Ils s'appliquent à la prochaine exécution. Pour les conserver, enregistrez-les comme préréglage (Enregistrer comme préréglage dans la fenêtre principale).",
    "Merge changes closer than":
        "Fusionner les changements plus proches que",
    "Minimum time between screenshots":
        "Temps minimal entre les captures",
    "Take a screenshot anyway after":
        "Prendre une capture quand même après",
    "Screenshot before the next change":
        "Capture avant le changement suivant",
    "Wait after a change (right-after mode)":
        "Attente après un changement (mode juste après)",
    "Frames checked per second":
        "Images analysées par seconde",
    "0 = every frame":
        "0 = toutes les images",
    "Analysis width":
        "Largeur d'analyse",
    "pixels, 0 = full size":
        "pixels, 0 = taille réelle",
    "Duplicate when it differs by at most":
        "Doublon si la différence est au plus de",
    "percent":
        "pour cent",
    "Also blur":
        "Flouter aussi",
    "Regular expressions, separated by semicolons; for example corp\\.example\\.com;TICKET-\\d+":
        "Expressions régulières séparées par des points-virgules ; par exemple corp\\.example\\.com;TICKET-\\d+",
    "For the date on exported documents and the times the app shows. System setting follows Windows, macOS, or Linux.":
        "Pour la date des documents exportés et les heures affichées par l'application. Paramètre du système suit Windows, macOS ou Linux.",
    "Reprocess recordings that are already done":
        "Retraiter les enregistrements déjà terminés",
    "Dry run: count the steps only, save nothing":
        "Essai : compter les étapes seulement, ne rien enregistrer",
    "Reset to Defaults":
        "Rétablir les valeurs par défaut",
    "Close":
        "Fermer",
    "Clear":
        "Effacer",
    "Deleted preset '{name}'.":
        "Préréglage « {name} » supprimé.",
    "Or untick Captions from narration.":
        "Ou décochez Légendes à partir de la narration.",
    "Source folder does not exist yet: {folder}":
        "Le dossier source n'existe pas encore : {folder}",
    "{n} recording(s) found in {folder}":
        "{n} enregistrement(s) trouvé(s) dans {folder}",
    "No .mp4, .mov, or .mkv files in {folder}":
        "Aucun fichier .mp4, .mov ou .mkv dans {folder}",
    "{n} of the selected recordings are already processed.":
        "{n} des enregistrements sélectionnés sont déjà traités.",
    "Processing":
        "Traitement",
    "Saved {name}. It is not in the list because the Recordings folder changed.":
        "{name} enregistré. Il n'apparaît pas dans la liste car le dossier Enregistrements a changé.",
    "Saved {name}. Click Process Selected to make the screenshots.":
        "{name} enregistré. Cliquez sur Traiter la sélection pour créer les captures.",
    "Processing is still running. Cancel it and exit?":
        "Le traitement est toujours en cours. L'annuler et quitter ?",
    "Browse...":
        "Parcourir...",
    "Open":
        "Ouvrir",
    "Model":
        "Modèle",
    "Model (not installed)":
        "Modèle (non installé)",
    "Replace the preset \"{name}\"?":
        "Remplacer le préréglage « {name} » ?",
    "Could not save the preset:\n{error}":
        "Impossible d'enregistrer le préréglage :\n{error}",
    "Could not open {path}:\n{error}":
        "Impossible d'ouvrir {path} :\n{error}",
    "Cancelled":
        "Annulé",
    "Dry run":
        "Essai",
    "Done (captions failed)":
        "Terminé (échec des légendes)",
    "Version {version}":
        "Version {version}",
    "{name} must be a number (got '{value}').":
        "{name} doit être un nombre (valeur : « {value} »).",
    "Done (skipped)":
        "Terminé (ignoré)",
    "Transcribing":
        "Transcription",
    "Failed":
        "Échec",
    "'{pattern}' in Also blur is not a valid pattern: {error}":
        "« {pattern} » dans Flouter aussi n'est pas un motif valide : {error}",
    "Processing {percent}%":
        "Traitement {percent} %",
    "No microphone":
        "Aucun micro",
    "Whole screen is the whole X11 screen. The small Recording window shows in the recording when it is inside the recorded area; it sits in the bottom-right corner.":
        "Écran entier correspond à tout l'écran X11. La petite fenêtre Enregistrement apparaît dans l'enregistrement si elle est dans la zone enregistrée ; elle se place dans le coin inférieur droit.",
    "To record the computer's sound, FFmpeg needs PulseAudio or PipeWire (pulse) support.":
        "Pour enregistrer le son de l'ordinateur, FFmpeg doit prendre en charge PulseAudio ou PipeWire (pulse).",
    "Whole screen":
        "Écran entier",
    "One window (click it after Start)":
        "Une fenêtre (cliquez dessus après Démarrer)",
    "An area (draw it after Start)":
        "Une zone (dessinez-la après Démarrer)",
    "macOS asks for permission the first time: allow this app (or Terminal) under System Settings > Privacy & Security > Screen Recording, and Input Monitoring for keys. Whole screen is the main display.":
        "macOS demande l'autorisation la première fois : autorisez cette application (ou Terminal) dans Réglages Système > Confidentialité et sécurité > Enregistrement de l'écran, et dans Surveillance de l'entrée pour les touches. Écran entier correspond à l'écran principal.",
    "Whole screen is all monitors. The small Recording window is left out of the recording.":
        "Écran entier correspond à tous les moniteurs. La petite fenêtre Enregistrement est exclue de l'enregistrement.",
    "To record the computer's sound, switch on \"Stereo Mix\" (Sound settings > More sound settings > Recording, right-click > Show Disabled Devices) or install a virtual audio cable, then open this window again.":
        "Pour enregistrer le son de l'ordinateur, activez « Mixage stéréo » (Paramètres du son > Plus de paramètres de son > Enregistrement, clic droit > Afficher les périphériques désactivés) ou installez un câble audio virtuel, puis rouvrez cette fenêtre.",
    "To record the computer's sound, install a loopback driver such as BlackHole and send the sound to it, then open this window again.":
        "Pour enregistrer le son de l'ordinateur, installez un pilote de bouclage comme BlackHole et envoyez-lui le son, puis rouvrez cette fenêtre.",
    "Note keys pressed (Enter, Tab, shortcuts such as Ctrl+S). Typed text is never saved.":
        "Noter les touches pressées (Entrée, Tab, raccourcis comme Ctrl+S). Le texte saisi n'est jamais enregistré.",
    "Record Screen":
        "Enregistrer l'écran",
    "Noting keys pressed is switched off by your administrator.":
        "La notation des touches est désactivée par votre administrateur.",
    "Drag over the area to record. Esc cancels.":
        "Faites glisser sur la zone à enregistrer. Échap annule.",
    "Click the window to record. Esc cancels.":
        "Cliquez sur la fenêtre à enregistrer. Échap annule.",
    "Paused (admin prompt)":
        "En pause (invite administrateur)",
    "Saving...":
        "Enregistrement...",
    "Discarding...":
        "Abandon...",
    "Recording discarded.":
        "Enregistrement abandonné.",
    "Start Recording":
        "Démarrer l'enregistrement",
    "That window could not be found. Choose Whole screen or An area instead.":
        "Cette fenêtre est introuvable. Choisissez plutôt Écran entier ou Une zone.",
    "Starting...":
        "Démarrage...",
    "Stop":
        "Arrêter",
    "Discard":
        "Abandonner",
    "Recording {time}":
        "Enregistrement {time}",
    "Recording did not work.":
        "L'enregistrement n'a pas fonctionné.",
    "Do the task as usual. Each click is noted, so the steps get a red ring where you clicked and a first-draft caption such as Click \"Next\". Stop when you are done.":
        "Effectuez la tâche comme d'habitude. Chaque clic est noté : les étapes reçoivent un cercle rouge à l'endroit du clic et une première ébauche de légende comme Cliquez sur « Suivant ». Arrêtez quand vous avez terminé.",
    "Record":
        "Enregistrer",
    "Make the screenshots when I stop":
        "Créer les captures à l'arrêt",
    "Microphone":
        "Micro",
    "Talk through the steps to turn your words into captions later (Captions From Narration in the Steps tab).":
        "Commentez les étapes pour transformer vos paroles en légendes plus tard (Légendes à partir de la narration dans l'onglet Étapes).",
    "Also record the computer's sound (videos, alerts)":
        "Enregistrer aussi le son de l'ordinateur (vidéos, alertes)",
    "The recording could not be saved.":
        "L'enregistrement n'a pas pu être sauvegardé.",
    "The Recordings folder cannot be used: {error}":
        "Le dossier Enregistrements ne peut pas être utilisé : {error}",
    "FFmpeg did not start recording. It said:":
        "FFmpeg n'a pas démarré l'enregistrement. Message :",
    "Select one or more recordings to archive (Ctrl+click or Shift+click for several).":
        "Sélectionnez un ou plusieurs enregistrements à archiver (Ctrl+clic ou Maj+clic pour plusieurs).",
    "Archived Recordings":
        "Enregistrements archivés",
    "Archive \"{name}\"?":
        "Archiver « {name} » ?",
    "Archive these {n} recordings?":
        "Archiver ces {n} enregistrements ?",
    "Bring it back any time with File > Archived Recordings.":
        "Récupérez-le à tout moment avec Fichier > Enregistrements archivés.",
    "Archived":
        "Archivé",
    "Size":
        "Taille",
    "Restore":
        "Restaurer",
    "Archiving":
        "Archivage",
    "Archived {n} recording(s).":
        "{n} enregistrement(s) archivé(s).",
    "Some recordings were not archived (nothing of theirs was deleted):":
        "Certains enregistrements n'ont pas été archivés (rien n'a été supprimé) :",
    "Restored {n} recording(s).":
        "{n} enregistrement(s) restauré(s).",
    "Shrink videos when archiving (smaller files, slightly lower picture quality)":
        "Réduire les vidéos lors de l'archivage (fichiers plus petits, qualité d'image légèrement inférieure)",
    "Open Folder":
        "Ouvrir le dossier",
    "Delete...":
        "Supprimer...",
    "{n} archive(s), {size}, in {folder}. Restore puts the recording and its screenshots back in your recordings and output folders.":
        "{n} archive(s), {size}, dans {folder}. Restaurer remet l'enregistrement et ses captures dans vos dossiers d'enregistrements et de sortie.",
    "Nothing archived yet. Archive recordings from the File menu or by right-clicking them in the list. They are kept in {folder}.":
        "Rien n'est encore archivé. Archivez des enregistrements depuis le menu Fichier ou par clic droit dans la liste. Ils sont conservés dans {folder}.",
    "Some archives were not restored:":
        "Certaines archives n'ont pas été restaurées :",
    "Delete {n} archive(s) for good?\n\nThe recordings, screenshots, and captions in them cannot be brought back.":
        "Supprimer définitivement {n} archive(s) ?\n\nLes enregistrements, captures et légendes qu'elles contiennent ne pourront pas être récupérés.",
    "{n} failed.":
        "{n} en échec.",
    "The video is re-encoded to take less space.":
        "La vidéo est réencodée pour prendre moins de place.",
    "The recording, its screenshots, captions, and exports are packed into one file in the \"{folder}\" folder in your output folder, and taken off the list.":
        "L'enregistrement, ses captures, légendes et exportations sont regroupés dans un fichier du dossier « {folder} » de votre dossier de sortie et retirés de la liste.",
    "({n} of {total}, {percent}%)":
        "({n} sur {total}, {percent} %)",
    "Logo and Template":
        "Logo et modèle",
    "Click a blur box to switch it off (or back on). Esc cancels.":
        "Cliquez sur un cadre de floutage pour le désactiver (ou le réactiver). Échap annule.",
    "Arrow added.":
        "Flèche ajoutée.",
    "Label text:":
        "Texte de l'étiquette :",
    "Annotations cleared on this step. Click Save Changes to keep it.":
        "Annotations effacées pour cette étape. Cliquez sur Enregistrer les modifications pour conserver.",
    "Save your changes to this recording's steps first?":
        "Enregistrer d'abord les modifications des étapes de cet enregistrement ?",
    "Saving steps...":
        "Enregistrement des étapes...",
    "Select a processed video to edit its steps.":
        "Sélectionnez une vidéo traitée pour modifier ses étapes.",
    "Screenshot":
        "Capture",
    "Original frame":
        "Image d'origine",
    "Crop":
        "Recadrer",
    "Crop All Steps (drag on the picture)":
        "Recadrer toutes les étapes (faites glisser sur l'image)",
    "Crop This Step Only (drag on the picture)":
        "Recadrer cette étape seulement (faites glisser sur l'image)",
    "No Crop on This Step":
        "Pas de recadrage pour cette étape",
    "Clear All Crops":
        "Supprimer tous les recadrages",
    "Blur":
        "Flouter",
    "Add Blur Box (drag on the picture)":
        "Ajouter un cadre de floutage (faites glisser sur l'image)",
    "Un-blur / Re-blur (click a box)":
        "Déflouter / reflouter (cliquez sur un cadre)",
    "Blur This Step":
        "Flouter cette étape",
    "Re-scan All Steps for Sensitive Text":
        "Rechercher à nouveau le texte sensible dans toutes les étapes",
    "Annotate":
        "Annoter",
    "Add Arrow (drag from the start to the tip)":
        "Ajouter une flèche (faites glisser du début à la pointe)",
    "Add Number (click where it goes)":
        "Ajouter un numéro (cliquez à l'emplacement)",
    "Add Text Label (click where it starts)":
        "Ajouter une étiquette (cliquez où elle commence)",
    "Edit or Remove (click an annotation)":
        "Modifier ou supprimer (cliquez sur une annotation)",
    "Clear Annotations on This Step":
        "Effacer les annotations de cette étape",
    "Highlight":
        "Mise en évidence",
    "Red Box on This Step":
        "Cadre rouge pour cette étape",
    "Zoomed Inset on This Step":
        "Zoom en incrustation pour cette étape",
    "Animated Clip of This Step (GIF)":
        "Clip animé de cette étape (GIF)",
    "Captions From Narration":
        "Légendes à partir de la narration",
    "Word":
        "Word",
    "Save Changes":
        "Enregistrer les modifications",
    "Open Image":
        "Ouvrir l'image",
    "Open Animated Clip":
        "Ouvrir le clip animé",
    "Open steps.md":
        "Ouvrir steps.md",
    "Open Exports Folder":
        "Ouvrir le dossier des exportations",
    "Unsaved changes":
        "Modifications non enregistrées",
    "Step {n} of {total} at {time}":
        "Étape {n} sur {total} à {time}",
    "no highlight (first step, nothing changed, or whole screen changed)":
        "pas de mise en évidence (première étape, rien n'a changé ou tout l'écran a changé)",
    "There are no deleted steps to restore.":
        "Aucune étape supprimée à restaurer.",
    "The original recording was not found, so a clip cannot be made. It may have been moved or deleted from the source folder.":
        "L'enregistrement d'origine est introuvable : impossible de créer un clip. Il a peut-être été déplacé ou supprimé du dossier source.",
    "The animated clip is made when you click Save Changes.":
        "Le clip animé est créé lorsque vous cliquez sur Enregistrer les modifications.",
    "Clip removed from this step.":
        "Clip retiré de cette étape.",
    "Logo":
        "Logo",
    "Word template":
        "Modèle Word",
    "Save the starter Word template":
        "Enregistrer le modèle Word de départ",
    "No blur box there.":
        "Aucun cadre de floutage à cet endroit.",
    "Removed the hand-drawn blur box.":
        "Cadre de floutage dessiné à la main supprimé.",
    "Drag from where the arrow starts to what it points at. Press Esc to cancel.":
        "Faites glisser du début de la flèche jusqu'à ce qu'elle désigne. Appuyez sur Échap pour annuler.",
    "Drag a rectangle around the area. Press Esc to cancel.":
        "Tracez un rectangle autour de la zone. Appuyez sur Échap pour annuler.",
    "Cancelled.":
        "Annulé.",
    "Rectangle too small; nothing changed.":
        "Rectangle trop petit ; rien n'a changé.",
    "This step has no annotations.":
        "Cette étape n'a pas d'annotations.",
    "Arrow too short; drag from where it starts to its tip.":
        "Flèche trop courte ; faites glisser du début à la pointe.",
    "Click Save Changes to keep it.":
        "Cliquez sur Enregistrer les modifications pour conserver.",
    "No annotation there.":
        "Aucune annotation à cet endroit.",
    "Label text (clear it to remove the label):":
        "Texte de l'étiquette (effacez-le pour supprimer l'étiquette) :",
    "Label changed.":
        "Étiquette modifiée.",
    "Label removed.":
        "Étiquette supprimée.",
    "Discard all unsaved changes?":
        "Abandonner toutes les modifications non enregistrées ?",
    "This step has no animated clip. Switch it on in the Highlight menu, then click Save Changes.":
        "Cette étape n'a pas de clip animé. Activez-le dans le menu Mise en évidence, puis cliquez sur Enregistrer les modifications.",
    "The original recording was not found. It may have been moved or deleted from the source folder.":
        "L'enregistrement d'origine est introuvable. Il a peut-être été déplacé ou supprimé du dossier source.",
    "This recording has no audio, so there is no narration to use.":
        "Cet enregistrement n'a pas d'audio : aucune narration à utiliser.",
    "Move Up":
        "Monter",
    "Move Down":
        "Descendre",
    "Delete Step":
        "Supprimer l'étape",
    "Restore Deleted":
        "Restaurer les supprimées",
    "Next >":
        "Suivante >",
    "Play in VLC":
        "Lire dans VLC",
    "No steps. Use Restore Deleted to bring steps back.":
        "Aucune étape. Utilisez Restaurer les supprimées pour les récupérer.",
    ", {n} duplicate(s)":
        ", {n} doublon(s)",
    "(this step only)":
        "(cette étape seulement)",
    "That step is already at the top of the list.":
        "Cette étape est déjà en haut de la liste.",
    "That step is already at the bottom of the list.":
        "Cette étape est déjà en bas de la liste.",
    "Restored {n} step(s). Click Save Changes to keep them.":
        "{n} étape(s) restaurée(s). Cliquez sur Enregistrer les modifications pour les conserver.",
    "Save your changes before exporting?":
        "Enregistrer les modifications avant d'exporter ?",
    "The unblurred screenshots may show passwords, keys, or internal addresses. Export them anyway? The file name will include UNREDACTED.":
        "Les captures non floutées peuvent montrer des mots de passe, des clés ou des adresses internes. Les exporter quand même ? Le nom du fichier contiendra UNREDACTED.",
    "Exporting {format}...":
        "Exportation {format}...",
    "Saved {name} and chose it as the Word template. Open it in Word to change how exports look.":
        "{name} enregistré et choisi comme modèle Word. Ouvrez-le dans Word pour changer l'apparence des exportations.",
    "Nothing has been exported yet.":
        "Rien n'a encore été exporté.",
    "Blur box added.":
        "Cadre de floutage ajouté.",
    "Click where the number goes. Press Esc to cancel.":
        "Cliquez à l'emplacement du numéro. Appuyez sur Échap pour annuler.",
    "Click where the label's top-left corner goes. Press Esc to cancel.":
        "Cliquez à l'emplacement du coin supérieur gauche de l'étiquette. Appuyez sur Échap pour annuler.",
    "Click an annotation to edit or remove it. Press Esc to cancel.":
        "Cliquez sur une annotation pour la modifier ou la supprimer. Appuyez sur Échap pour annuler.",
    "Label added.":
        "Étiquette ajoutée.",
    "Number to show (0 removes the marker):":
        "Numéro à afficher (0 supprime le repère) :",
    "Marker removed.":
        "Repère supprimé.",
    "Click ring removed.":
        "Cercle de clic supprimé.",
    "Arrow removed.":
        "Flèche supprimée.",
    "Original image is missing (deleted or moved).":
        "L'image d'origine est manquante (supprimée ou déplacée).",
    "FFmpeg is required for previews":
        "FFmpeg est nécessaire pour les aperçus",
    "Saved. Newer changes are not saved yet: click Save Changes again.":
        "Enregistré. Les modifications plus récentes ne sont pas encore enregistrées : cliquez à nouveau sur Enregistrer les modifications.",
    "Transcribing narration with the {model} model. The first time, the model is downloaded, which can take a few minutes...":
        "Transcription de la narration avec le modèle {model}. La première fois, le modèle est téléchargé, ce qui peut prendre quelques minutes...",
    "No speech was found in this recording.":
        "Aucune parole n'a été trouvée dans cet enregistrement.",
    "Whole recording:":
        "Tout l'enregistrement :",
    "Blur sensitive info":
        "Flouter les informations sensibles",
    "Highlight changes":
        "Mettre en évidence les changements",
    "Zoomed inset":
        "Loupe",
    "Caption":
        "Légende",
    "Document title":
        "Titre du document",
    "Version":
        "Version",
    "Author":
        "Auteur",
    "Export":
        "Exporter",
    "Logo and Template...":
        "Logo et modèle...",
    "Unblurred copy":
        "Copie non floutée",
    "Open Exports":
        "Ouvrir les exportations",
    "screen stable {start} to {end}":
        "écran stable de {start} à {end}",
    "Moved the step from position {old} to {new}. Use Up/Down (or < Prev / Next >) to look at other steps.":
        "Étape déplacée de la position {old} à {new}. Utilisez Haut/Bas (ou < Précédente / Suivante >) pour voir les autres étapes.",
    "Exported {name}":
        "{name} exporté",
    "Logo and Word Template":
        "Logo et modèle Word",
    "Used for every export. The logo goes at the top of HTML, PDF, and Word documents. A Word template sets the fonts, colors, margins, and page header and footer of Word exports.":
        "Utilisé pour toutes les exportations. Le logo apparaît en haut des documents HTML, PDF et Word. Un modèle Word définit les polices, couleurs, marges, en-tête et pied de page des exportations Word.",
    "Pictures":
        "Images",
    "All files":
        "Tous les fichiers",
    "Word documents":
        "Documents Word",
    "Create Starter Template...":
        "Créer un modèle de départ...",
    "Saves the standard template. Open it in Word, change its styles and page header, save it, and choose it above.":
        "Enregistre le modèle standard. Ouvrez-le dans Word, modifiez ses styles et son en-tête, enregistrez-le et choisissez-le ci-dessus.",
    "Drag a rectangle around the area to keep. Press Esc to cancel.":
        "Tracez un rectangle autour de la zone à conserver. Appuyez sur Échap pour annuler.",
    "Drag a rectangle around the area to blur. Press Esc to cancel.":
        "Tracez un rectangle autour de la zone à flouter. Appuyez sur Échap pour annuler.",
    "Number {n} added.":
        "Numéro {n} ajouté.",
    "No text; nothing added.":
        "Aucun texte ; rien n'a été ajouté.",
    "Saving failed:\n{error}":
        "Échec de l'enregistrement :\n{error}",
    "Saved {n} step(s) to {folder}":
        "{n} étape(s) enregistrée(s) dans {folder}",
    "Opened {name} in VLC at {time}":
        "{name} ouvert dans VLC à {time}",
    "{name} has not been processed yet.":
        "{name} n'a pas encore été traité.",
    "{n} removed":
        "{n} supprimée(s)",
    "cropped to {w}x{h}":
        "recadré à {w}x{h}",
    "Export failed:\n{error}":
        "Échec de l'exportation :\n{error}",
    "{item} cleared.":
        "{item} : effacé.",
    "Un-blurred: {reason}.":
        "Défloutée : {reason}.",
    "Blurred again: {reason}.":
        "Floutée à nouveau : {reason}.",
    "detected text":
        "texte détecté",
    "Crop set to {w}x{h} at {x},{y} for all steps.":
        "Recadrage de {w}x{h} à {x},{y} pour toutes les étapes.",
    "Crop set to {w}x{h} at {x},{y} for this step.":
        "Recadrage de {w}x{h} à {x},{y} pour cette étape.",
    "Marker changed to {n}.":
        "Repère changé en {n}.",
    "Remove this click ring?":
        "Supprimer ce cercle de clic ?",
    "Remove this arrow?":
        "Supprimer cette flèche ?",
    "Filled {n} empty caption(s) from {passages} spoken passage(s). Captions you typed were kept. Review them, then Save Changes. Full text: {file}":
        "{n} légende(s) vide(s) remplie(s) à partir de {passages} passage(s) parlé(s). Les légendes que vous aviez saisies sont conservées. Vérifiez-les, puis Enregistrer les modifications. Texte complet : {file}",
    "Choose a file: {item}":
        "Choisir un fichier : {item}",
    "{item} set for every export.":
        "{item} : défini pour toutes les exportations.",
    "Preview unavailable: {error}":
        "Aperçu indisponible : {error}",
    "System setting":
        "Paramètre du système",
    "24-hour (14:05)":
        "24 heures (14:05)",
    "12-hour (2:05 PM)":
        "12 heures (2:05 PM)",
    "2026-11-22 (year-month-day)":
        "2026-11-22 (année-mois-jour)",
    "11/22/2026 (month/day/year)":
        "11/22/2026 (mois/jour/année)",
    "22/11/2026 (day/month/year)":
        "22/11/2026 (jour/mois/année)",
    "22.11.2026 (day.month.year)":
        "22.11.2026 (jour.mois.année)",
    "< Prev":
        "< Précédente",
}

# German
CATALOGS['de'] = {
    "High (more shots)":
        "Hoch (mehr Screenshots)",
    "Normal (recommended)":
        "Normal (empfohlen)",
    "Low (fewer shots)":
        "Niedrig (weniger Screenshots)",
    "Custom":
        "Benutzerdefiniert",
    "Finished state (before next change)":
        "Endzustand (vor der nächsten Änderung)",
    "Right after each change":
        "Direkt nach jeder Änderung",
    "System Theme":
        "Systemdesign",
    "Light Theme":
        "Helles Design",
    "Dark Theme":
        "Dunkles Design",
    "seconds":
        "Sekunden",
    "File":
        "Datei",
    "View":
        "Ansicht",
    "Help":
        "Hilfe",
    "Check for updates":
        "Nach Updates suchen",
    "Checking for updates...":
        "Suche nach Updates...",
    "✓ Up to date":
        "✓ Aktuell",
    "Update available: v{v}":
        "Update verfügbar: v{v}",
    "Update check failed. Try again":
        "Updateprüfung fehlgeschlagen. Erneut versuchen",
    "Update checks turned off":
        "Updateprüfung ausgeschaltet",
    "Advanced Settings":
        "Erweiterte Einstellungen",
    "Output":
        "Ausgabe",
    "Region":
        "Region",
    "Run":
        "Ausführung",
    "Name for this preset:":
        "Name dieser Voreinstellung:",
    "the system language":
        "die Systemsprache",
    "Ready":
        "Bereit",
    "Record Screen...":
        "Bildschirm aufnehmen...",
    "Choose Source Folder...":
        "Quellordner wählen...",
    "Choose Output Folder...":
        "Ausgabeordner wählen...",
    "Open Source Folder":
        "Quellordner öffnen",
    "Open Output Folder":
        "Ausgabeordner öffnen",
    "Archive Selected Recordings...":
        "Ausgewählte Aufnahmen archivieren...",
    "Archived Recordings...":
        "Archivierte Aufnahmen...",
    "Exit":
        "Beenden",
    "Language":
        "Sprache",
    "System Language":
        "Systemsprache",
    "Advanced Settings...":
        "Erweiterte Einstellungen...",
    "Steps":
        "Schritte",
    "Log":
        "Protokoll",
    "Keyboard Shortcuts":
        "Tastenkürzel",
    "Online Documentation":
        "Online-Dokumentation",
    "Report a Problem...":
        "Problem melden...",
    "Suggest an Idea...":
        "Idee vorschlagen...",
    "Project on GitHub":
        "Projekt auf GitHub",
    "Release Notes":
        "Versionshinweise",
    "Check for Updates...":
        "Nach Updates suchen...",
    "Check for Updates Automatically":
        "Automatisch nach Updates suchen",
    "Refresh":
        "Aktualisieren",
    "● Record":
        "● Aufnehmen",
    "Recording":
        "Aufnahme",
    "Status":
        "Status",
    "Process":
        "Verarbeiten",
    "Archive...":
        "Archivieren...",
    "Process All":
        "Alle verarbeiten",
    "Process Selected":
        "Auswahl verarbeiten",
    "Cancel":
        "Abbrechen",
    "Highlight what changed in each step (red box)":
        "Hervorheben, was sich in jedem Schritt geändert hat (roter Rahmen)",
    "Blur passwords, keys, IP and email addresses":
        "Passwörter, Schlüssel, IP- und E-Mail-Adressen unkenntlich machen",
    "Remove duplicate screenshots":
        "Doppelte Screenshots entfernen",
    "Timing":
        "Zeiten",
    "Detection":
        "Erkennung",
    "Built-in presets cannot be deleted.":
        "Integrierte Voreinstellungen können nicht gelöscht werden.",
    "Threshold":
        "Schwellenwert",
    "Merge changes within":
        "Änderungen zusammenfassen innerhalb",
    "Min gap":
        "Mindestabstand",
    "Force a shot after":
        "Screenshot erzwingen nach",
    "Lead":
        "Vorlauf",
    "Settle":
        "Beruhigung",
    "Analyze fps":
        "Analysierte Bilder pro Sekunde",
    "Analyze width":
        "Analysebreite",
    "Duplicate tolerance":
        "Duplikattoleranz",
    "Choose both a source folder and an output folder.":
        "Wählen Sie einen Quell- und einen Ausgabeordner.",
    "Done":
        "Fertig",
    "New":
        "Neu",
    "Select one or more videos first (Ctrl+click or Shift+click for several).":
        "Wählen Sie zuerst ein oder mehrere Videos aus (Strg+Klick oder Umschalt+Klick für mehrere).",
    "This recording is already processed.":
        "Diese Aufnahme ist bereits verarbeitet.",
    "No videos to process. Put recordings in the source folder, then click Refresh.":
        "Keine Videos zu verarbeiten. Legen Sie Aufnahmen in den Quellordner und klicken Sie auf Aktualisieren.",
    "Queued":
        "In Warteschlange",
    "Cancelling...":
        "Wird abgebrochen...",
    "Finished: {ok} processed, {skipped} skipped, {failed} failed":
        "Fertig: {ok} verarbeitet, {skipped} übersprungen, {failed} fehlgeschlagen",
    "Recordings":
        "Aufnahmen",
    "Image format":
        "Bildformat",
    "Dates":
        "Datum",
    "Times":
        "Uhrzeit",
    "Preset '{name}' applied.":
        "Voreinstellung „{name}“ angewendet.",
    "Saved preset '{name}'.":
        "Voreinstellung „{name}“ gespeichert.",
    "Delete the preset \"{name}\"?":
        "Voreinstellung „{name}“ löschen?",
    "{app} will use {language} the next time it starts.":
        "{app} verwendet {language} beim nächsten Start.",
    "{name} must be between {low} and {high} (got {value}).":
        "{name} muss zwischen {low} und {high} liegen (Wert: {value}).",
    "{name} must be {low} or more (got {value}).":
        "{name} muss {low} oder mehr sein (Wert: {value}).",
    "One of the settings is invalid. Check the values and try again.":
        "Eine der Einstellungen ist ungültig. Prüfen Sie die Werte und versuchen Sie es erneut.",
    "Process again with the current settings? The previous screenshots, captions, and exports are kept in a previous-<date> folder next to the new ones.\n\nNo skips the finished ones.":
        "Mit den aktuellen Einstellungen erneut verarbeiten? Die bisherigen Screenshots, Beschriftungen und Exporte bleiben in einem Ordner previous-<Datum> neben den neuen erhalten.\n\nNein überspringt die fertigen.",
    "The source folder changed. Click Refresh to reload the video list, then try again.":
        "Der Quellordner hat sich geändert. Klicken Sie auf Aktualisieren, um die Videoliste neu zu laden, und versuchen Sie es erneut.",
    ", {n} cancelled":
        ", {n} abgebrochen",
    "See the Log tab or screencap.log in the output folder for details.":
        "Details finden Sie im Tab Protokoll oder in screencap.log im Ausgabeordner.",
    "This video has not been processed yet.":
        "Dieses Video wurde noch nicht verarbeitet.",
    "Unexpected error: {error}\n\nDetails are in the Log tab.":
        "Unerwarteter Fehler: {error}\n\nDetails stehen im Tab Protokoll.",
    "About {app}":
        "Über {app}",
    "Include subfolders":
        "Unterordner einbeziehen",
    "Settings":
        "Einstellungen",
    "Preset":
        "Voreinstellung",
    "Sensitivity":
        "Empfindlichkeit",
    "Screenshot taken":
        "Screenshot-Zeitpunkt",
    "Captions from narration":
        "Beschriftungen aus der Sprachaufnahme",
    "Delete Preset":
        "Voreinstellung löschen",
    "Save as Preset...":
        "Als Voreinstellung speichern...",
    "These apply to the next run. To keep them, save them as a preset (Save as Preset in the main window).":
        "Sie gelten für den nächsten Durchlauf. Um sie zu behalten, speichern Sie sie als Voreinstellung (Als Voreinstellung speichern im Hauptfenster).",
    "Merge changes closer than":
        "Änderungen zusammenfassen, die näher liegen als",
    "Minimum time between screenshots":
        "Mindestzeit zwischen Screenshots",
    "Take a screenshot anyway after":
        "Trotzdem einen Screenshot aufnehmen nach",
    "Screenshot before the next change":
        "Screenshot vor der nächsten Änderung",
    "Wait after a change (right-after mode)":
        "Wartezeit nach einer Änderung (Modus direkt danach)",
    "Frames checked per second":
        "Analysierte Bilder pro Sekunde",
    "0 = every frame":
        "0 = jedes Bild",
    "Analysis width":
        "Analysebreite",
    "pixels, 0 = full size":
        "Pixel, 0 = volle Größe",
    "Duplicate when it differs by at most":
        "Duplikat, wenn der Unterschied höchstens",
    "percent":
        "Prozent",
    "Also blur":
        "Außerdem unkenntlich machen",
    "Regular expressions, separated by semicolons; for example corp\\.example\\.com;TICKET-\\d+":
        "Reguläre Ausdrücke, getrennt durch Semikolons; zum Beispiel corp\\.example\\.com;TICKET-\\d+",
    "For the date on exported documents and the times the app shows. System setting follows Windows, macOS, or Linux.":
        "Für das Datum in exportierten Dokumenten und die Uhrzeiten in der App. Systemeinstellung folgt Windows, macOS oder Linux.",
    "Reprocess recordings that are already done":
        "Bereits fertige Aufnahmen erneut verarbeiten",
    "Dry run: count the steps only, save nothing":
        "Probelauf: nur Schritte zählen, nichts speichern",
    "Reset to Defaults":
        "Auf Standard zurücksetzen",
    "Close":
        "Schließen",
    "Clear":
        "Leeren",
    "Deleted preset '{name}'.":
        "Voreinstellung „{name}“ gelöscht.",
    "Or untick Captions from narration.":
        "Oder deaktivieren Sie Beschriftungen aus der Sprachaufnahme.",
    "Source folder does not exist yet: {folder}":
        "Der Quellordner existiert noch nicht: {folder}",
    "{n} recording(s) found in {folder}":
        "{n} Aufnahme(n) in {folder} gefunden",
    "No .mp4, .mov, or .mkv files in {folder}":
        "Keine .mp4-, .mov- oder .mkv-Dateien in {folder}",
    "{n} of the selected recordings are already processed.":
        "{n} der ausgewählten Aufnahmen sind bereits verarbeitet.",
    "Processing":
        "Wird verarbeitet",
    "Saved {name}. It is not in the list because the Recordings folder changed.":
        "{name} gespeichert. Die Datei steht nicht in der Liste, weil sich der Aufnahmeordner geändert hat.",
    "Saved {name}. Click Process Selected to make the screenshots.":
        "{name} gespeichert. Klicken Sie auf Auswahl verarbeiten, um die Screenshots zu erstellen.",
    "Processing is still running. Cancel it and exit?":
        "Die Verarbeitung läuft noch. Abbrechen und beenden?",
    "Browse...":
        "Durchsuchen...",
    "Open":
        "Öffnen",
    "Model":
        "Modell",
    "Model (not installed)":
        "Modell (nicht installiert)",
    "Replace the preset \"{name}\"?":
        "Voreinstellung „{name}“ ersetzen?",
    "Could not save the preset:\n{error}":
        "Die Voreinstellung konnte nicht gespeichert werden:\n{error}",
    "Could not open {path}:\n{error}":
        "{path} konnte nicht geöffnet werden:\n{error}",
    "Cancelled":
        "Abgebrochen",
    "Dry run":
        "Probelauf",
    "Done (captions failed)":
        "Fertig (Beschriftungen fehlgeschlagen)",
    "Version {version}":
        "Version {version}",
    "{name} must be a number (got '{value}').":
        "{name} muss eine Zahl sein (Wert: „{value}“).",
    "Done (skipped)":
        "Fertig (übersprungen)",
    "Transcribing":
        "Wird transkribiert",
    "Failed":
        "Fehlgeschlagen",
    "'{pattern}' in Also blur is not a valid pattern: {error}":
        "„{pattern}“ in Außerdem unkenntlich machen ist kein gültiges Muster: {error}",
    "Processing {percent}%":
        "Verarbeitung {percent} %",
    "No microphone":
        "Kein Mikrofon",
    "Whole screen is the whole X11 screen. The small Recording window shows in the recording when it is inside the recorded area; it sits in the bottom-right corner.":
        "Ganzer Bildschirm ist der gesamte X11-Bildschirm. Das kleine Aufnahmefenster ist in der Aufnahme zu sehen, wenn es im aufgenommenen Bereich liegt; es sitzt unten rechts.",
    "To record the computer's sound, FFmpeg needs PulseAudio or PipeWire (pulse) support.":
        "Um den Ton des Computers aufzunehmen, braucht FFmpeg Unterstützung für PulseAudio oder PipeWire (pulse).",
    "Whole screen":
        "Ganzer Bildschirm",
    "One window (click it after Start)":
        "Ein Fenster (nach dem Start anklicken)",
    "An area (draw it after Start)":
        "Ein Bereich (nach dem Start aufziehen)",
    "macOS asks for permission the first time: allow this app (or Terminal) under System Settings > Privacy & Security > Screen Recording, and Input Monitoring for keys. Whole screen is the main display.":
        "macOS fragt beim ersten Mal nach einer Erlaubnis: Erlauben Sie diese App (oder Terminal) unter Systemeinstellungen > Datenschutz & Sicherheit > Bildschirmaufnahme und für Tasten unter Eingabeüberwachung. Ganzer Bildschirm ist der Hauptbildschirm.",
    "Whole screen is all monitors. The small Recording window is left out of the recording.":
        "Ganzer Bildschirm umfasst alle Monitore. Das kleine Aufnahmefenster ist in der Aufnahme nicht zu sehen.",
    "To record the computer's sound, switch on \"Stereo Mix\" (Sound settings > More sound settings > Recording, right-click > Show Disabled Devices) or install a virtual audio cable, then open this window again.":
        "Um den Ton des Computers aufzunehmen, schalten Sie „Stereomix“ ein (Soundeinstellungen > Weitere Soundeinstellungen > Aufnahme, Rechtsklick > Deaktivierte Geräte anzeigen) oder installieren Sie ein virtuelles Audiokabel und öffnen Sie dieses Fenster erneut.",
    "To record the computer's sound, install a loopback driver such as BlackHole and send the sound to it, then open this window again.":
        "Um den Ton des Computers aufzunehmen, installieren Sie einen Loopback-Treiber wie BlackHole, leiten Sie den Ton dorthin und öffnen Sie dieses Fenster erneut.",
    "Note keys pressed (Enter, Tab, shortcuts such as Ctrl+S). Typed text is never saved.":
        "Gedrückte Tasten notieren (Eingabe, Tab, Kürzel wie Strg+S). Getippter Text wird nie gespeichert.",
    "Record Screen":
        "Bildschirm aufnehmen",
    "Noting keys pressed is switched off by your administrator.":
        "Das Notieren von Tasten wurde von Ihrem Administrator ausgeschaltet.",
    "Drag over the area to record. Esc cancels.":
        "Ziehen Sie über den aufzunehmenden Bereich. Esc bricht ab.",
    "Click the window to record. Esc cancels.":
        "Klicken Sie auf das aufzunehmende Fenster. Esc bricht ab.",
    "Paused (admin prompt)":
        "Pausiert (Administratorabfrage)",
    "Saving...":
        "Wird gespeichert...",
    "Discarding...":
        "Wird verworfen...",
    "Recording discarded.":
        "Aufnahme verworfen.",
    "Start Recording":
        "Aufnahme starten",
    "That window could not be found. Choose Whole screen or An area instead.":
        "Dieses Fenster wurde nicht gefunden. Wählen Sie stattdessen Ganzer Bildschirm oder Ein Bereich.",
    "Starting...":
        "Wird gestartet...",
    "Stop":
        "Stopp",
    "Discard":
        "Verwerfen",
    "Recording {time}":
        "Aufnahme {time}",
    "Recording did not work.":
        "Die Aufnahme hat nicht funktioniert.",
    "Do the task as usual. Each click is noted, so the steps get a red ring where you clicked and a first-draft caption such as Click \"Next\". Stop when you are done.":
        "Erledigen Sie die Aufgabe wie gewohnt. Jeder Klick wird notiert, sodass die Schritte einen roten Ring an der Klickstelle und einen ersten Beschriftungsentwurf wie Klicken Sie auf „Weiter“ erhalten. Stoppen Sie, wenn Sie fertig sind.",
    "Record":
        "Aufnehmen",
    "Make the screenshots when I stop":
        "Screenshots beim Stoppen erstellen",
    "Microphone":
        "Mikrofon",
    "Talk through the steps to turn your words into captions later (Captions From Narration in the Steps tab).":
        "Sprechen Sie die Schritte mit, um Ihre Worte später in Beschriftungen umzuwandeln (Beschriftungen aus der Sprachaufnahme im Tab Schritte).",
    "Also record the computer's sound (videos, alerts)":
        "Auch den Ton des Computers aufnehmen (Videos, Hinweistöne)",
    "The recording could not be saved.":
        "Die Aufnahme konnte nicht gespeichert werden.",
    "The Recordings folder cannot be used: {error}":
        "Der Aufnahmeordner kann nicht verwendet werden: {error}",
    "FFmpeg did not start recording. It said:":
        "FFmpeg hat die Aufnahme nicht gestartet. Meldung:",
    "Select one or more recordings to archive (Ctrl+click or Shift+click for several).":
        "Wählen Sie eine oder mehrere Aufnahmen zum Archivieren aus (Strg+Klick oder Umschalt+Klick für mehrere).",
    "Archived Recordings":
        "Archivierte Aufnahmen",
    "Archive \"{name}\"?":
        "„{name}“ archivieren?",
    "Archive these {n} recordings?":
        "Diese {n} Aufnahmen archivieren?",
    "Bring it back any time with File > Archived Recordings.":
        "Holen Sie sie jederzeit über Datei > Archivierte Aufnahmen zurück.",
    "Archived":
        "Archiviert",
    "Size":
        "Größe",
    "Restore":
        "Wiederherstellen",
    "Archiving":
        "Wird archiviert",
    "Archived {n} recording(s).":
        "{n} Aufnahme(n) archiviert.",
    "Some recordings were not archived (nothing of theirs was deleted):":
        "Einige Aufnahmen wurden nicht archiviert (davon wurde nichts gelöscht):",
    "Restored {n} recording(s).":
        "{n} Aufnahme(n) wiederhergestellt.",
    "Shrink videos when archiving (smaller files, slightly lower picture quality)":
        "Videos beim Archivieren verkleinern (kleinere Dateien, etwas geringere Bildqualität)",
    "Open Folder":
        "Ordner öffnen",
    "Delete...":
        "Löschen...",
    "{n} archive(s), {size}, in {folder}. Restore puts the recording and its screenshots back in your recordings and output folders.":
        "{n} Archiv(e), {size}, in {folder}. Wiederherstellen legt die Aufnahme und ihre Screenshots zurück in Ihren Aufnahme- und Ausgabeordner.",
    "Nothing archived yet. Archive recordings from the File menu or by right-clicking them in the list. They are kept in {folder}.":
        "Noch nichts archiviert. Archivieren Sie Aufnahmen über das Menü Datei oder per Rechtsklick in der Liste. Sie werden in {folder} aufbewahrt.",
    "Some archives were not restored:":
        "Einige Archive wurden nicht wiederhergestellt:",
    "Delete {n} archive(s) for good?\n\nThe recordings, screenshots, and captions in them cannot be brought back.":
        "{n} Archiv(e) endgültig löschen?\n\nDie darin enthaltenen Aufnahmen, Screenshots und Beschriftungen können nicht wiederhergestellt werden.",
    "{n} failed.":
        "{n} fehlgeschlagen.",
    "The video is re-encoded to take less space.":
        "Das Video wird neu kodiert, um weniger Platz zu belegen.",
    "The recording, its screenshots, captions, and exports are packed into one file in the \"{folder}\" folder in your output folder, and taken off the list.":
        "Die Aufnahme, ihre Screenshots, Beschriftungen und Exporte werden in eine Datei im Ordner „{folder}“ in Ihrem Ausgabeordner gepackt und aus der Liste entfernt.",
    "({n} of {total}, {percent}%)":
        "({n} von {total}, {percent} %)",
    "Logo and Template":
        "Logo und Vorlage",
    "Click a blur box to switch it off (or back on). Esc cancels.":
        "Klicken Sie auf einen Unschärferahmen, um ihn aus- (oder wieder ein-)zuschalten. Esc bricht ab.",
    "Arrow added.":
        "Pfeil hinzugefügt.",
    "Label text:":
        "Beschriftungstext:",
    "Annotations cleared on this step. Click Save Changes to keep it.":
        "Anmerkungen in diesem Schritt entfernt. Klicken Sie auf Änderungen speichern, um dies zu behalten.",
    "Save your changes to this recording's steps first?":
        "Zuerst die Änderungen an den Schritten dieser Aufnahme speichern?",
    "Saving steps...":
        "Schritte werden gespeichert...",
    "Select a processed video to edit its steps.":
        "Wählen Sie ein verarbeitetes Video aus, um seine Schritte zu bearbeiten.",
    "Screenshot":
        "Screenshot",
    "Original frame":
        "Originalbild",
    "Crop":
        "Zuschneiden",
    "Crop All Steps (drag on the picture)":
        "Alle Schritte zuschneiden (im Bild ziehen)",
    "Crop This Step Only (drag on the picture)":
        "Nur diesen Schritt zuschneiden (im Bild ziehen)",
    "No Crop on This Step":
        "Kein Zuschnitt in diesem Schritt",
    "Clear All Crops":
        "Alle Zuschnitte entfernen",
    "Blur":
        "Unkenntlich machen",
    "Add Blur Box (drag on the picture)":
        "Unschärferahmen hinzufügen (im Bild ziehen)",
    "Un-blur / Re-blur (click a box)":
        "Unschärfe aus / wieder ein (Rahmen anklicken)",
    "Blur This Step":
        "Diesen Schritt unkenntlich machen",
    "Re-scan All Steps for Sensitive Text":
        "Alle Schritte erneut nach sensiblem Text durchsuchen",
    "Annotate":
        "Anmerken",
    "Add Arrow (drag from the start to the tip)":
        "Pfeil hinzufügen (vom Anfang zur Spitze ziehen)",
    "Add Number (click where it goes)":
        "Nummer hinzufügen (an die Stelle klicken)",
    "Add Text Label (click where it starts)":
        "Textbeschriftung hinzufügen (an den Anfang klicken)",
    "Edit or Remove (click an annotation)":
        "Bearbeiten oder entfernen (Anmerkung anklicken)",
    "Clear Annotations on This Step":
        "Anmerkungen in diesem Schritt entfernen",
    "Highlight":
        "Hervorhebung",
    "Red Box on This Step":
        "Roter Rahmen in diesem Schritt",
    "Zoomed Inset on This Step":
        "Vergrößerter Ausschnitt in diesem Schritt",
    "Animated Clip of This Step (GIF)":
        "Animierter Clip dieses Schritts (GIF)",
    "Captions From Narration":
        "Aus Sprachaufnahme",
    "Word":
        "Word",
    "Save Changes":
        "Änderungen speichern",
    "Open Image":
        "Bild öffnen",
    "Open Animated Clip":
        "Animierten Clip öffnen",
    "Open steps.md":
        "steps.md öffnen",
    "Open Exports Folder":
        "Exportordner öffnen",
    "Unsaved changes":
        "Ungespeicherte Änderungen",
    "Step {n} of {total} at {time}":
        "Schritt {n} von {total} bei {time}",
    "no highlight (first step, nothing changed, or whole screen changed)":
        "keine Hervorhebung (erster Schritt, nichts geändert oder ganzer Bildschirm geändert)",
    "There are no deleted steps to restore.":
        "Es gibt keine gelöschten Schritte zum Wiederherstellen.",
    "The original recording was not found, so a clip cannot be made. It may have been moved or deleted from the source folder.":
        "Die Originalaufnahme wurde nicht gefunden, daher kann kein Clip erstellt werden. Sie wurde möglicherweise verschoben oder aus dem Quellordner gelöscht.",
    "The animated clip is made when you click Save Changes.":
        "Der animierte Clip wird erstellt, wenn Sie auf Änderungen speichern klicken.",
    "Clip removed from this step.":
        "Clip aus diesem Schritt entfernt.",
    "Logo":
        "Logo",
    "Word template":
        "Word-Vorlage",
    "Save the starter Word template":
        "Word-Startvorlage speichern",
    "No blur box there.":
        "Dort ist kein Unschärferahmen.",
    "Removed the hand-drawn blur box.":
        "Von Hand gezeichneter Unschärferahmen entfernt.",
    "Drag from where the arrow starts to what it points at. Press Esc to cancel.":
        "Ziehen Sie vom Anfang des Pfeils zu dem, worauf er zeigt. Drücken Sie Esc zum Abbrechen.",
    "Drag a rectangle around the area. Press Esc to cancel.":
        "Ziehen Sie ein Rechteck um den Bereich. Drücken Sie Esc zum Abbrechen.",
    "Cancelled.":
        "Abgebrochen.",
    "Rectangle too small; nothing changed.":
        "Rechteck zu klein; nichts geändert.",
    "This step has no annotations.":
        "Dieser Schritt hat keine Anmerkungen.",
    "Arrow too short; drag from where it starts to its tip.":
        "Pfeil zu kurz; ziehen Sie vom Anfang bis zur Spitze.",
    "Click Save Changes to keep it.":
        "Klicken Sie auf Änderungen speichern, um dies zu behalten.",
    "No annotation there.":
        "Dort ist keine Anmerkung.",
    "Label text (clear it to remove the label):":
        "Beschriftungstext (leeren, um die Beschriftung zu entfernen):",
    "Label changed.":
        "Beschriftung geändert.",
    "Label removed.":
        "Beschriftung entfernt.",
    "Discard all unsaved changes?":
        "Alle ungespeicherten Änderungen verwerfen?",
    "This step has no animated clip. Switch it on in the Highlight menu, then click Save Changes.":
        "Dieser Schritt hat keinen animierten Clip. Schalten Sie ihn im Menü Hervorhebung ein und klicken Sie auf Änderungen speichern.",
    "The original recording was not found. It may have been moved or deleted from the source folder.":
        "Die Originalaufnahme wurde nicht gefunden. Sie wurde möglicherweise verschoben oder aus dem Quellordner gelöscht.",
    "This recording has no audio, so there is no narration to use.":
        "Diese Aufnahme hat keinen Ton, daher gibt es keine Sprachaufnahme.",
    "Move Up":
        "Nach oben",
    "Move Down":
        "Nach unten",
    "Delete Step":
        "Schritt löschen",
    "Restore Deleted":
        "Gelöschte wiederherstellen",
    "Next >":
        "Weiter >",
    "Play in VLC":
        "In VLC abspielen",
    "No steps. Use Restore Deleted to bring steps back.":
        "Keine Schritte. Mit Gelöschte wiederherstellen holen Sie sie zurück.",
    ", {n} duplicate(s)":
        ", {n} Duplikat(e)",
    "(this step only)":
        "(nur dieser Schritt)",
    "That step is already at the top of the list.":
        "Dieser Schritt steht bereits am Anfang der Liste.",
    "That step is already at the bottom of the list.":
        "Dieser Schritt steht bereits am Ende der Liste.",
    "Restored {n} step(s). Click Save Changes to keep them.":
        "{n} Schritt(e) wiederhergestellt. Klicken Sie auf Änderungen speichern, um sie zu behalten.",
    "Save your changes before exporting?":
        "Änderungen vor dem Export speichern?",
    "The unblurred screenshots may show passwords, keys, or internal addresses. Export them anyway? The file name will include UNREDACTED.":
        "Die nicht unkenntlich gemachten Screenshots können Passwörter, Schlüssel oder interne Adressen zeigen. Trotzdem exportieren? Der Dateiname enthält dann UNREDACTED.",
    "Exporting {format}...":
        "{format} wird exportiert...",
    "Saved {name} and chose it as the Word template. Open it in Word to change how exports look.":
        "{name} gespeichert und als Word-Vorlage gewählt. Öffnen Sie die Datei in Word, um das Aussehen der Exporte zu ändern.",
    "Nothing has been exported yet.":
        "Es wurde noch nichts exportiert.",
    "Blur box added.":
        "Unschärferahmen hinzugefügt.",
    "Click where the number goes. Press Esc to cancel.":
        "Klicken Sie an die Stelle für die Nummer. Drücken Sie Esc zum Abbrechen.",
    "Click where the label's top-left corner goes. Press Esc to cancel.":
        "Klicken Sie an die Stelle für die linke obere Ecke der Beschriftung. Drücken Sie Esc zum Abbrechen.",
    "Click an annotation to edit or remove it. Press Esc to cancel.":
        "Klicken Sie auf eine Anmerkung, um sie zu bearbeiten oder zu entfernen. Drücken Sie Esc zum Abbrechen.",
    "Label added.":
        "Beschriftung hinzugefügt.",
    "Number to show (0 removes the marker):":
        "Anzuzeigende Nummer (0 entfernt die Markierung):",
    "Marker removed.":
        "Markierung entfernt.",
    "Click ring removed.":
        "Klickring entfernt.",
    "Arrow removed.":
        "Pfeil entfernt.",
    "Original image is missing (deleted or moved).":
        "Das Originalbild fehlt (gelöscht oder verschoben).",
    "FFmpeg is required for previews":
        "Für Vorschauen wird FFmpeg benötigt",
    "Saved. Newer changes are not saved yet: click Save Changes again.":
        "Gespeichert. Neuere Änderungen sind noch nicht gespeichert: Klicken Sie erneut auf Änderungen speichern.",
    "Transcribing narration with the {model} model. The first time, the model is downloaded, which can take a few minutes...":
        "Die Sprachaufnahme wird mit dem Modell {model} transkribiert. Beim ersten Mal wird das Modell heruntergeladen, was einige Minuten dauern kann...",
    "No speech was found in this recording.":
        "In dieser Aufnahme wurde keine Sprache gefunden.",
    "Whole recording:":
        "Ganze Aufnahme:",
    "Blur sensitive info":
        "Sensible Daten unkenntlich machen",
    "Highlight changes":
        "Änderungen hervorheben",
    "Zoomed inset":
        "Lupe",
    "Caption":
        "Beschriftung",
    "Document title":
        "Dokumenttitel",
    "Version":
        "Version",
    "Author":
        "Autor",
    "Export":
        "Exportieren",
    "Logo and Template...":
        "Logo und Vorlage...",
    "Unblurred copy":
        "Kopie ohne Unkenntlichmachung",
    "Open Exports":
        "Exporte öffnen",
    "screen stable {start} to {end}":
        "Bildschirm stabil von {start} bis {end}",
    "Moved the step from position {old} to {new}. Use Up/Down (or < Prev / Next >) to look at other steps.":
        "Schritt von Position {old} nach {new} verschoben. Mit Auf/Ab (oder < Zurück / Weiter >) sehen Sie andere Schritte an.",
    "Exported {name}":
        "{name} exportiert",
    "Logo and Word Template":
        "Logo und Word-Vorlage",
    "Used for every export. The logo goes at the top of HTML, PDF, and Word documents. A Word template sets the fonts, colors, margins, and page header and footer of Word exports.":
        "Wird für jeden Export verwendet. Das Logo steht oben in HTML-, PDF- und Word-Dokumenten. Eine Word-Vorlage legt Schriften, Farben, Ränder sowie Kopf- und Fußzeile der Word-Exporte fest.",
    "Pictures":
        "Bilder",
    "All files":
        "Alle Dateien",
    "Word documents":
        "Word-Dokumente",
    "Create Starter Template...":
        "Startvorlage erstellen...",
    "Saves the standard template. Open it in Word, change its styles and page header, save it, and choose it above.":
        "Speichert die Standardvorlage. Öffnen Sie sie in Word, ändern Sie Formatvorlagen und Kopfzeile, speichern Sie sie und wählen Sie sie oben aus.",
    "Drag a rectangle around the area to keep. Press Esc to cancel.":
        "Ziehen Sie ein Rechteck um den Bereich, der bleiben soll. Drücken Sie Esc zum Abbrechen.",
    "Drag a rectangle around the area to blur. Press Esc to cancel.":
        "Ziehen Sie ein Rechteck um den Bereich, der unkenntlich werden soll. Drücken Sie Esc zum Abbrechen.",
    "Number {n} added.":
        "Nummer {n} hinzugefügt.",
    "No text; nothing added.":
        "Kein Text; nichts hinzugefügt.",
    "Saving failed:\n{error}":
        "Speichern fehlgeschlagen:\n{error}",
    "Saved {n} step(s) to {folder}":
        "{n} Schritt(e) in {folder} gespeichert",
    "Opened {name} in VLC at {time}":
        "{name} in VLC bei {time} geöffnet",
    "{name} has not been processed yet.":
        "{name} wurde noch nicht verarbeitet.",
    "{n} removed":
        "{n} entfernt",
    "cropped to {w}x{h}":
        "zugeschnitten auf {w}x{h}",
    "Export failed:\n{error}":
        "Export fehlgeschlagen:\n{error}",
    "{item} cleared.":
        "{item} entfernt.",
    "Un-blurred: {reason}.":
        "Unschärfe aus: {reason}.",
    "Blurred again: {reason}.":
        "Wieder unkenntlich: {reason}.",
    "detected text":
        "erkannter Text",
    "Crop set to {w}x{h} at {x},{y} for all steps.":
        "Zuschnitt {w}x{h} bei {x},{y} für alle Schritte.",
    "Crop set to {w}x{h} at {x},{y} for this step.":
        "Zuschnitt {w}x{h} bei {x},{y} für diesen Schritt.",
    "Marker changed to {n}.":
        "Markierung auf {n} geändert.",
    "Remove this click ring?":
        "Diesen Klickring entfernen?",
    "Remove this arrow?":
        "Diesen Pfeil entfernen?",
    "Filled {n} empty caption(s) from {passages} spoken passage(s). Captions you typed were kept. Review them, then Save Changes. Full text: {file}":
        "{n} leere Beschriftung(en) aus {passages} gesprochenen Passage(n) gefüllt. Von Ihnen eingegebene Beschriftungen blieben erhalten. Prüfen Sie sie und klicken Sie dann auf Änderungen speichern. Volltext: {file}",
    "Choose a file: {item}":
        "Datei wählen: {item}",
    "{item} set for every export.":
        "{item} für alle Exporte festgelegt.",
    "Preview unavailable: {error}":
        "Vorschau nicht verfügbar: {error}",
    "System setting":
        "Systemeinstellung",
    "24-hour (14:05)":
        "24 Stunden (14:05)",
    "12-hour (2:05 PM)":
        "12 Stunden (2:05 PM)",
    "2026-11-22 (year-month-day)":
        "2026-11-22 (Jahr-Monat-Tag)",
    "11/22/2026 (month/day/year)":
        "11/22/2026 (Monat/Tag/Jahr)",
    "22/11/2026 (day/month/year)":
        "22/11/2026 (Tag/Monat/Jahr)",
    "22.11.2026 (day.month.year)":
        "22.11.2026 (Tag.Monat.Jahr)",
    "< Prev":
        "< Zurück",
}

# Portuguese (Brazil)
CATALOGS['pt_BR'] = {
    "High (more shots)":
        "Alta (mais capturas)",
    "Normal (recommended)":
        "Normal (recomendada)",
    "Low (fewer shots)":
        "Baixa (menos capturas)",
    "Custom":
        "Personalizada",
    "Finished state (before next change)":
        "Estado final (antes da próxima mudança)",
    "Right after each change":
        "Logo após cada mudança",
    "System Theme":
        "Tema do sistema",
    "Light Theme":
        "Tema claro",
    "Dark Theme":
        "Tema escuro",
    "seconds":
        "segundos",
    "File":
        "Arquivo",
    "View":
        "Exibir",
    "Help":
        "Ajuda",
    "Check for updates":
        "Verificar atualizações",
    "Checking for updates...":
        "Verificando atualizações...",
    "✓ Up to date":
        "✓ Atualizado",
    "Update available: v{v}":
        "Atualização disponível: v{v}",
    "Update check failed. Try again":
        "Falha ao verificar atualizações. Tentar novamente",
    "Update checks turned off":
        "Verificação de atualizações desativada",
    "Advanced Settings":
        "Configurações avançadas",
    "Output":
        "Saída",
    "Region":
        "Região",
    "Run":
        "Execução",
    "Name for this preset:":
        "Nome desta predefinição:",
    "the system language":
        "o idioma do sistema",
    "Ready":
        "Pronto",
    "Record Screen...":
        "Gravar tela...",
    "Choose Source Folder...":
        "Escolher pasta de origem...",
    "Choose Output Folder...":
        "Escolher pasta de saída...",
    "Open Source Folder":
        "Abrir pasta de origem",
    "Open Output Folder":
        "Abrir pasta de saída",
    "Archive Selected Recordings...":
        "Arquivar gravações selecionadas...",
    "Archived Recordings...":
        "Gravações arquivadas...",
    "Exit":
        "Sair",
    "Language":
        "Idioma",
    "System Language":
        "Idioma do sistema",
    "Advanced Settings...":
        "Configurações avançadas...",
    "Steps":
        "Etapas",
    "Log":
        "Registro",
    "Keyboard Shortcuts":
        "Atalhos de teclado",
    "Online Documentation":
        "Documentação online",
    "Report a Problem...":
        "Relatar um problema...",
    "Suggest an Idea...":
        "Sugerir uma ideia...",
    "Project on GitHub":
        "Projeto no GitHub",
    "Release Notes":
        "Notas da versão",
    "Check for Updates...":
        "Verificar atualizações...",
    "Check for Updates Automatically":
        "Verificar atualizações automaticamente",
    "Refresh":
        "Atualizar",
    "● Record":
        "● Gravar",
    "Recording":
        "Gravação",
    "Status":
        "Status",
    "Process":
        "Processar",
    "Archive...":
        "Arquivar...",
    "Process All":
        "Processar tudo",
    "Process Selected":
        "Processar seleção",
    "Cancel":
        "Cancelar",
    "Highlight what changed in each step (red box)":
        "Destacar o que mudou em cada etapa (caixa vermelha)",
    "Blur passwords, keys, IP and email addresses":
        "Desfocar senhas, chaves, endereços IP e de e-mail",
    "Remove duplicate screenshots":
        "Remover capturas duplicadas",
    "Timing":
        "Tempos",
    "Detection":
        "Detecção",
    "Built-in presets cannot be deleted.":
        "As predefinições integradas não podem ser excluídas.",
    "Threshold":
        "Limite",
    "Merge changes within":
        "Combinar mudanças em",
    "Min gap":
        "Intervalo mínimo",
    "Force a shot after":
        "Forçar captura após",
    "Lead":
        "Antecedência",
    "Settle":
        "Estabilização",
    "Analyze fps":
        "Quadros analisados por segundo",
    "Analyze width":
        "Largura de análise",
    "Duplicate tolerance":
        "Tolerância de duplicatas",
    "Choose both a source folder and an output folder.":
        "Escolha uma pasta de origem e uma de saída.",
    "Done":
        "Concluído",
    "New":
        "Novo",
    "Select one or more videos first (Ctrl+click or Shift+click for several).":
        "Selecione primeiro um ou mais vídeos (Ctrl+clique ou Shift+clique para vários).",
    "This recording is already processed.":
        "Esta gravação já foi processada.",
    "No videos to process. Put recordings in the source folder, then click Refresh.":
        "Nenhum vídeo para processar. Coloque gravações na pasta de origem e clique em Atualizar.",
    "Queued":
        "Na fila",
    "Cancelling...":
        "Cancelando...",
    "Finished: {ok} processed, {skipped} skipped, {failed} failed":
        "Concluído: {ok} processados, {skipped} ignorados, {failed} com falha",
    "Recordings":
        "Gravações",
    "Image format":
        "Formato de imagem",
    "Dates":
        "Datas",
    "Times":
        "Horas",
    "Preset '{name}' applied.":
        "Predefinição \"{name}\" aplicada.",
    "Saved preset '{name}'.":
        "Predefinição \"{name}\" salva.",
    "Delete the preset \"{name}\"?":
        "Excluir a predefinição \"{name}\"?",
    "{app} will use {language} the next time it starts.":
        "{app} usará {language} na próxima vez que for iniciado.",
    "{name} must be between {low} and {high} (got {value}).":
        "{name} deve estar entre {low} e {high} (valor: {value}).",
    "{name} must be {low} or more (got {value}).":
        "{name} deve ser {low} ou mais (valor: {value}).",
    "One of the settings is invalid. Check the values and try again.":
        "Uma das configurações é inválida. Verifique os valores e tente novamente.",
    "Process again with the current settings? The previous screenshots, captions, and exports are kept in a previous-<date> folder next to the new ones.\n\nNo skips the finished ones.":
        "Processar novamente com as configurações atuais? As capturas, legendas e exportações anteriores são mantidas em uma pasta previous-<data> ao lado das novas.\n\nNão ignora as já concluídas.",
    "The source folder changed. Click Refresh to reload the video list, then try again.":
        "A pasta de origem mudou. Clique em Atualizar para recarregar a lista de vídeos e tente novamente.",
    ", {n} cancelled":
        ", {n} cancelados",
    "See the Log tab or screencap.log in the output folder for details.":
        "Veja a guia Registro ou screencap.log na pasta de saída para mais detalhes.",
    "This video has not been processed yet.":
        "Este vídeo ainda não foi processado.",
    "Unexpected error: {error}\n\nDetails are in the Log tab.":
        "Erro inesperado: {error}\n\nOs detalhes estão na guia Registro.",
    "About {app}":
        "Sobre o {app}",
    "Include subfolders":
        "Incluir subpastas",
    "Settings":
        "Configurações",
    "Preset":
        "Predefinição",
    "Sensitivity":
        "Sensibilidade",
    "Screenshot taken":
        "Captura feita",
    "Captions from narration":
        "Legendas a partir da narração",
    "Delete Preset":
        "Excluir predefinição",
    "Save as Preset...":
        "Salvar como predefinição...",
    "These apply to the next run. To keep them, save them as a preset (Save as Preset in the main window).":
        "Valem para a próxima execução. Para mantê-las, salve-as como predefinição (Salvar como predefinição na janela principal).",
    "Merge changes closer than":
        "Combinar mudanças mais próximas que",
    "Minimum time between screenshots":
        "Tempo mínimo entre capturas",
    "Take a screenshot anyway after":
        "Fazer uma captura mesmo assim após",
    "Screenshot before the next change":
        "Captura antes da próxima mudança",
    "Wait after a change (right-after mode)":
        "Espera após uma mudança (modo logo após)",
    "Frames checked per second":
        "Quadros analisados por segundo",
    "0 = every frame":
        "0 = todos os quadros",
    "Analysis width":
        "Largura de análise",
    "pixels, 0 = full size":
        "pixels, 0 = tamanho total",
    "Duplicate when it differs by at most":
        "Duplicata se diferir no máximo em",
    "percent":
        "por cento",
    "Also blur":
        "Desfocar também",
    "Regular expressions, separated by semicolons; for example corp\\.example\\.com;TICKET-\\d+":
        "Expressões regulares separadas por ponto e vírgula; por exemplo corp\\.example\\.com;TICKET-\\d+",
    "For the date on exported documents and the times the app shows. System setting follows Windows, macOS, or Linux.":
        "Para a data dos documentos exportados e os horários que o aplicativo mostra. Configuração do sistema segue o Windows, macOS ou Linux.",
    "Reprocess recordings that are already done":
        "Reprocessar gravações já concluídas",
    "Dry run: count the steps only, save nothing":
        "Simulação: apenas contar as etapas, não salvar nada",
    "Reset to Defaults":
        "Restaurar padrões",
    "Close":
        "Fechar",
    "Clear":
        "Limpar",
    "Deleted preset '{name}'.":
        "Predefinição \"{name}\" excluída.",
    "Or untick Captions from narration.":
        "Ou desmarque Legendas a partir da narração.",
    "Source folder does not exist yet: {folder}":
        "A pasta de origem ainda não existe: {folder}",
    "{n} recording(s) found in {folder}":
        "{n} gravação(ões) encontrada(s) em {folder}",
    "No .mp4, .mov, or .mkv files in {folder}":
        "Nenhum arquivo .mp4, .mov ou .mkv em {folder}",
    "{n} of the selected recordings are already processed.":
        "{n} das gravações selecionadas já foram processadas.",
    "Processing":
        "Processando",
    "Saved {name}. It is not in the list because the Recordings folder changed.":
        "{name} salvo. Ele não aparece na lista porque a pasta Gravações mudou.",
    "Saved {name}. Click Process Selected to make the screenshots.":
        "{name} salvo. Clique em Processar seleção para criar as capturas.",
    "Processing is still running. Cancel it and exit?":
        "O processamento ainda está em andamento. Cancelar e sair?",
    "Browse...":
        "Procurar...",
    "Open":
        "Abrir",
    "Model":
        "Modelo",
    "Model (not installed)":
        "Modelo (não instalado)",
    "Replace the preset \"{name}\"?":
        "Substituir a predefinição \"{name}\"?",
    "Could not save the preset:\n{error}":
        "Não foi possível salvar a predefinição:\n{error}",
    "Could not open {path}:\n{error}":
        "Não foi possível abrir {path}:\n{error}",
    "Cancelled":
        "Cancelado",
    "Dry run":
        "Simulação",
    "Done (captions failed)":
        "Concluído (falha nas legendas)",
    "Version {version}":
        "Versão {version}",
    "{name} must be a number (got '{value}').":
        "{name} deve ser um número (valor: \"{value}\").",
    "Done (skipped)":
        "Concluído (ignorado)",
    "Transcribing":
        "Transcrevendo",
    "Failed":
        "Falhou",
    "'{pattern}' in Also blur is not a valid pattern: {error}":
        "\"{pattern}\" em Desfocar também não é um padrão válido: {error}",
    "Processing {percent}%":
        "Processando {percent}%",
    "No microphone":
        "Sem microfone",
    "Whole screen is the whole X11 screen. The small Recording window shows in the recording when it is inside the recorded area; it sits in the bottom-right corner.":
        "Tela inteira é toda a tela X11. A pequena janela Gravação aparece na gravação quando está dentro da área gravada; ela fica no canto inferior direito.",
    "To record the computer's sound, FFmpeg needs PulseAudio or PipeWire (pulse) support.":
        "Para gravar o som do computador, o FFmpeg precisa de suporte a PulseAudio ou PipeWire (pulse).",
    "Whole screen":
        "Tela inteira",
    "One window (click it after Start)":
        "Uma janela (clique nela após Iniciar)",
    "An area (draw it after Start)":
        "Uma área (desenhe-a após Iniciar)",
    "macOS asks for permission the first time: allow this app (or Terminal) under System Settings > Privacy & Security > Screen Recording, and Input Monitoring for keys. Whole screen is the main display.":
        "O macOS pede permissão na primeira vez: permita este aplicativo (ou o Terminal) em Ajustes do Sistema > Privacidade e Segurança > Gravação de Tela, e em Monitoramento de Entrada para as teclas. Tela inteira é a tela principal.",
    "Whole screen is all monitors. The small Recording window is left out of the recording.":
        "Tela inteira são todos os monitores. A pequena janela Gravação fica fora da gravação.",
    "To record the computer's sound, switch on \"Stereo Mix\" (Sound settings > More sound settings > Recording, right-click > Show Disabled Devices) or install a virtual audio cable, then open this window again.":
        "Para gravar o som do computador, ative \"Mixagem estéreo\" (Configurações de som > Mais configurações de som > Gravação, clique com o botão direito > Mostrar dispositivos desabilitados) ou instale um cabo de áudio virtual e abra esta janela novamente.",
    "To record the computer's sound, install a loopback driver such as BlackHole and send the sound to it, then open this window again.":
        "Para gravar o som do computador, instale um driver de loopback como o BlackHole e envie o som para ele; depois abra esta janela novamente.",
    "Note keys pressed (Enter, Tab, shortcuts such as Ctrl+S). Typed text is never saved.":
        "Anotar as teclas pressionadas (Enter, Tab, atalhos como Ctrl+S). O texto digitado nunca é salvo.",
    "Record Screen":
        "Gravar tela",
    "Noting keys pressed is switched off by your administrator.":
        "A anotação de teclas foi desativada pelo seu administrador.",
    "Drag over the area to record. Esc cancels.":
        "Arraste sobre a área a gravar. Esc cancela.",
    "Click the window to record. Esc cancels.":
        "Clique na janela a gravar. Esc cancela.",
    "Paused (admin prompt)":
        "Pausado (aviso de administrador)",
    "Saving...":
        "Salvando...",
    "Discarding...":
        "Descartando...",
    "Recording discarded.":
        "Gravação descartada.",
    "Start Recording":
        "Iniciar gravação",
    "That window could not be found. Choose Whole screen or An area instead.":
        "Essa janela não foi encontrada. Escolha Tela inteira ou Uma área.",
    "Starting...":
        "Iniciando...",
    "Stop":
        "Parar",
    "Discard":
        "Descartar",
    "Recording {time}":
        "Gravando {time}",
    "Recording did not work.":
        "A gravação não funcionou.",
    "Do the task as usual. Each click is noted, so the steps get a red ring where you clicked and a first-draft caption such as Click \"Next\". Stop when you are done.":
        "Faça a tarefa normalmente. Cada clique é anotado, então as etapas recebem um anel vermelho onde você clicou e um primeiro rascunho de legenda como Clique em \"Avançar\". Pare quando terminar.",
    "Record":
        "Gravar",
    "Make the screenshots when I stop":
        "Criar as capturas ao parar",
    "Microphone":
        "Microfone",
    "Talk through the steps to turn your words into captions later (Captions From Narration in the Steps tab).":
        "Narre as etapas para transformar suas palavras em legendas depois (Legendas a partir da narração na guia Etapas).",
    "Also record the computer's sound (videos, alerts)":
        "Gravar também o som do computador (vídeos, alertas)",
    "The recording could not be saved.":
        "Não foi possível salvar a gravação.",
    "The Recordings folder cannot be used: {error}":
        "A pasta Gravações não pode ser usada: {error}",
    "FFmpeg did not start recording. It said:":
        "O FFmpeg não começou a gravar. Ele disse:",
    "Select one or more recordings to archive (Ctrl+click or Shift+click for several).":
        "Selecione uma ou mais gravações para arquivar (Ctrl+clique ou Shift+clique para várias).",
    "Archived Recordings":
        "Gravações arquivadas",
    "Archive \"{name}\"?":
        "Arquivar \"{name}\"?",
    "Archive these {n} recordings?":
        "Arquivar estas {n} gravações?",
    "Bring it back any time with File > Archived Recordings.":
        "Recupere quando quiser em Arquivo > Gravações arquivadas.",
    "Archived":
        "Arquivada",
    "Size":
        "Tamanho",
    "Restore":
        "Restaurar",
    "Archiving":
        "Arquivando",
    "Archived {n} recording(s).":
        "{n} gravação(ões) arquivada(s).",
    "Some recordings were not archived (nothing of theirs was deleted):":
        "Algumas gravações não foram arquivadas (nada delas foi excluído):",
    "Restored {n} recording(s).":
        "{n} gravação(ões) restaurada(s).",
    "Shrink videos when archiving (smaller files, slightly lower picture quality)":
        "Reduzir os vídeos ao arquivar (arquivos menores, qualidade de imagem um pouco menor)",
    "Open Folder":
        "Abrir pasta",
    "Delete...":
        "Excluir...",
    "{n} archive(s), {size}, in {folder}. Restore puts the recording and its screenshots back in your recordings and output folders.":
        "{n} arquivo(s), {size}, em {folder}. Restaurar devolve a gravação e suas capturas às suas pastas de gravações e de saída.",
    "Nothing archived yet. Archive recordings from the File menu or by right-clicking them in the list. They are kept in {folder}.":
        "Nada arquivado ainda. Arquive gravações pelo menu Arquivo ou clicando com o botão direito nelas na lista. Elas ficam em {folder}.",
    "Some archives were not restored:":
        "Alguns arquivos não foram restaurados:",
    "Delete {n} archive(s) for good?\n\nThe recordings, screenshots, and captions in them cannot be brought back.":
        "Excluir {n} arquivo(s) definitivamente?\n\nAs gravações, capturas e legendas contidas neles não poderão ser recuperadas.",
    "{n} failed.":
        "{n} com falha.",
    "The video is re-encoded to take less space.":
        "O vídeo é recodificado para ocupar menos espaço.",
    "The recording, its screenshots, captions, and exports are packed into one file in the \"{folder}\" folder in your output folder, and taken off the list.":
        "A gravação, suas capturas, legendas e exportações são compactadas em um arquivo na pasta \"{folder}\" da sua pasta de saída e retiradas da lista.",
    "({n} of {total}, {percent}%)":
        "({n} de {total}, {percent}%)",
    "Logo and Template":
        "Logotipo e modelo",
    "Click a blur box to switch it off (or back on). Esc cancels.":
        "Clique em uma caixa de desfoque para desativá-la (ou reativá-la). Esc cancela.",
    "Arrow added.":
        "Seta adicionada.",
    "Label text:":
        "Texto do rótulo:",
    "Annotations cleared on this step. Click Save Changes to keep it.":
        "Anotações removidas nesta etapa. Clique em Salvar alterações para manter.",
    "Save your changes to this recording's steps first?":
        "Salvar primeiro as alterações nas etapas desta gravação?",
    "Saving steps...":
        "Salvando etapas...",
    "Select a processed video to edit its steps.":
        "Selecione um vídeo processado para editar suas etapas.",
    "Screenshot":
        "Captura",
    "Original frame":
        "Quadro original",
    "Crop":
        "Cortar",
    "Crop All Steps (drag on the picture)":
        "Cortar todas as etapas (arraste na imagem)",
    "Crop This Step Only (drag on the picture)":
        "Cortar só esta etapa (arraste na imagem)",
    "No Crop on This Step":
        "Sem corte nesta etapa",
    "Clear All Crops":
        "Remover todos os cortes",
    "Blur":
        "Desfocar",
    "Add Blur Box (drag on the picture)":
        "Adicionar caixa de desfoque (arraste na imagem)",
    "Un-blur / Re-blur (click a box)":
        "Remover / reaplicar desfoque (clique em uma caixa)",
    "Blur This Step":
        "Desfocar esta etapa",
    "Re-scan All Steps for Sensitive Text":
        "Procurar texto sensível novamente em todas as etapas",
    "Annotate":
        "Anotar",
    "Add Arrow (drag from the start to the tip)":
        "Adicionar seta (arraste do início até a ponta)",
    "Add Number (click where it goes)":
        "Adicionar número (clique onde ele fica)",
    "Add Text Label (click where it starts)":
        "Adicionar rótulo de texto (clique onde ele começa)",
    "Edit or Remove (click an annotation)":
        "Editar ou remover (clique em uma anotação)",
    "Clear Annotations on This Step":
        "Limpar anotações desta etapa",
    "Highlight":
        "Destaque",
    "Red Box on This Step":
        "Caixa vermelha nesta etapa",
    "Zoomed Inset on This Step":
        "Ampliação nesta etapa",
    "Animated Clip of This Step (GIF)":
        "Clipe animado desta etapa (GIF)",
    "Captions From Narration":
        "Legendas a partir da narração",
    "Word":
        "Word",
    "Save Changes":
        "Salvar alterações",
    "Open Image":
        "Abrir imagem",
    "Open Animated Clip":
        "Abrir clipe animado",
    "Open steps.md":
        "Abrir steps.md",
    "Open Exports Folder":
        "Abrir pasta de exportações",
    "Unsaved changes":
        "Alterações não salvas",
    "Step {n} of {total} at {time}":
        "Etapa {n} de {total} em {time}",
    "no highlight (first step, nothing changed, or whole screen changed)":
        "sem destaque (primeira etapa, nada mudou ou a tela inteira mudou)",
    "There are no deleted steps to restore.":
        "Não há etapas excluídas para restaurar.",
    "The original recording was not found, so a clip cannot be made. It may have been moved or deleted from the source folder.":
        "A gravação original não foi encontrada, então não é possível criar um clipe. Ela pode ter sido movida ou excluída da pasta de origem.",
    "The animated clip is made when you click Save Changes.":
        "O clipe animado é criado quando você clica em Salvar alterações.",
    "Clip removed from this step.":
        "Clipe removido desta etapa.",
    "Logo":
        "Logotipo",
    "Word template":
        "Modelo do Word",
    "Save the starter Word template":
        "Salvar o modelo inicial do Word",
    "No blur box there.":
        "Não há caixa de desfoque aí.",
    "Removed the hand-drawn blur box.":
        "Caixa de desfoque desenhada à mão removida.",
    "Drag from where the arrow starts to what it points at. Press Esc to cancel.":
        "Arraste de onde a seta começa até o que ela aponta. Pressione Esc para cancelar.",
    "Drag a rectangle around the area. Press Esc to cancel.":
        "Desenhe um retângulo em volta da área. Pressione Esc para cancelar.",
    "Cancelled.":
        "Cancelado.",
    "Rectangle too small; nothing changed.":
        "Retângulo pequeno demais; nada foi alterado.",
    "This step has no annotations.":
        "Esta etapa não tem anotações.",
    "Arrow too short; drag from where it starts to its tip.":
        "Seta curta demais; arraste do início até a ponta.",
    "Click Save Changes to keep it.":
        "Clique em Salvar alterações para manter.",
    "No annotation there.":
        "Não há anotação aí.",
    "Label text (clear it to remove the label):":
        "Texto do rótulo (apague-o para remover o rótulo):",
    "Label changed.":
        "Rótulo alterado.",
    "Label removed.":
        "Rótulo removido.",
    "Discard all unsaved changes?":
        "Descartar todas as alterações não salvas?",
    "This step has no animated clip. Switch it on in the Highlight menu, then click Save Changes.":
        "Esta etapa não tem clipe animado. Ative-o no menu Destaque e clique em Salvar alterações.",
    "The original recording was not found. It may have been moved or deleted from the source folder.":
        "A gravação original não foi encontrada. Ela pode ter sido movida ou excluída da pasta de origem.",
    "This recording has no audio, so there is no narration to use.":
        "Esta gravação não tem áudio, então não há narração para usar.",
    "Move Up":
        "Mover para cima",
    "Move Down":
        "Mover para baixo",
    "Delete Step":
        "Excluir etapa",
    "Restore Deleted":
        "Restaurar excluídas",
    "Next >":
        "Próxima >",
    "Play in VLC":
        "Reproduzir no VLC",
    "No steps. Use Restore Deleted to bring steps back.":
        "Nenhuma etapa. Use Restaurar excluídas para trazê-las de volta.",
    ", {n} duplicate(s)":
        ", {n} duplicata(s)",
    "(this step only)":
        "(só esta etapa)",
    "That step is already at the top of the list.":
        "Essa etapa já está no topo da lista.",
    "That step is already at the bottom of the list.":
        "Essa etapa já está no fim da lista.",
    "Restored {n} step(s). Click Save Changes to keep them.":
        "{n} etapa(s) restaurada(s). Clique em Salvar alterações para mantê-las.",
    "Save your changes before exporting?":
        "Salvar as alterações antes de exportar?",
    "The unblurred screenshots may show passwords, keys, or internal addresses. Export them anyway? The file name will include UNREDACTED.":
        "As capturas sem desfoque podem mostrar senhas, chaves ou endereços internos. Exportar mesmo assim? O nome do arquivo incluirá UNREDACTED.",
    "Exporting {format}...":
        "Exportando {format}...",
    "Saved {name} and chose it as the Word template. Open it in Word to change how exports look.":
        "{name} salvo e escolhido como modelo do Word. Abra-o no Word para mudar a aparência das exportações.",
    "Nothing has been exported yet.":
        "Nada foi exportado ainda.",
    "Blur box added.":
        "Caixa de desfoque adicionada.",
    "Click where the number goes. Press Esc to cancel.":
        "Clique onde o número fica. Pressione Esc para cancelar.",
    "Click where the label's top-left corner goes. Press Esc to cancel.":
        "Clique onde fica o canto superior esquerdo do rótulo. Pressione Esc para cancelar.",
    "Click an annotation to edit or remove it. Press Esc to cancel.":
        "Clique em uma anotação para editá-la ou removê-la. Pressione Esc para cancelar.",
    "Label added.":
        "Rótulo adicionado.",
    "Number to show (0 removes the marker):":
        "Número a mostrar (0 remove o marcador):",
    "Marker removed.":
        "Marcador removido.",
    "Click ring removed.":
        "Anel de clique removido.",
    "Arrow removed.":
        "Seta removida.",
    "Original image is missing (deleted or moved).":
        "A imagem original está faltando (excluída ou movida).",
    "FFmpeg is required for previews":
        "O FFmpeg é necessário para as pré-visualizações",
    "Saved. Newer changes are not saved yet: click Save Changes again.":
        "Salvo. As alterações mais recentes ainda não foram salvas: clique em Salvar alterações novamente.",
    "Transcribing narration with the {model} model. The first time, the model is downloaded, which can take a few minutes...":
        "Transcrevendo a narração com o modelo {model}. Na primeira vez, o modelo é baixado, o que pode levar alguns minutos...",
    "No speech was found in this recording.":
        "Nenhuma fala foi encontrada nesta gravação.",
    "Whole recording:":
        "Gravação inteira:",
    "Blur sensitive info":
        "Desfocar informações sensíveis",
    "Highlight changes":
        "Destacar mudanças",
    "Zoomed inset":
        "Ampliação",
    "Caption":
        "Legenda",
    "Document title":
        "Título do documento",
    "Version":
        "Versão",
    "Author":
        "Autor",
    "Export":
        "Exportar",
    "Logo and Template...":
        "Logotipo e modelo...",
    "Unblurred copy":
        "Cópia sem desfoque",
    "Open Exports":
        "Abrir exportações",
    "screen stable {start} to {end}":
        "tela estável de {start} a {end}",
    "Moved the step from position {old} to {new}. Use Up/Down (or < Prev / Next >) to look at other steps.":
        "Etapa movida da posição {old} para {new}. Use Cima/Baixo (ou < Anterior / Próxima >) para ver outras etapas.",
    "Exported {name}":
        "{name} exportado",
    "Logo and Word Template":
        "Logotipo e modelo do Word",
    "Used for every export. The logo goes at the top of HTML, PDF, and Word documents. A Word template sets the fonts, colors, margins, and page header and footer of Word exports.":
        "Usado em todas as exportações. O logotipo fica no topo dos documentos HTML, PDF e Word. Um modelo do Word define as fontes, cores, margens e o cabeçalho e rodapé das exportações do Word.",
    "Pictures":
        "Imagens",
    "All files":
        "Todos os arquivos",
    "Word documents":
        "Documentos do Word",
    "Create Starter Template...":
        "Criar modelo inicial...",
    "Saves the standard template. Open it in Word, change its styles and page header, save it, and choose it above.":
        "Salva o modelo padrão. Abra-o no Word, altere seus estilos e o cabeçalho, salve-o e escolha-o acima.",
    "Drag a rectangle around the area to keep. Press Esc to cancel.":
        "Desenhe um retângulo em volta da área a manter. Pressione Esc para cancelar.",
    "Drag a rectangle around the area to blur. Press Esc to cancel.":
        "Desenhe um retângulo em volta da área a desfocar. Pressione Esc para cancelar.",
    "Number {n} added.":
        "Número {n} adicionado.",
    "No text; nothing added.":
        "Sem texto; nada foi adicionado.",
    "Saving failed:\n{error}":
        "Falha ao salvar:\n{error}",
    "Saved {n} step(s) to {folder}":
        "{n} etapa(s) salva(s) em {folder}",
    "Opened {name} in VLC at {time}":
        "{name} aberto no VLC em {time}",
    "{name} has not been processed yet.":
        "{name} ainda não foi processado.",
    "{n} removed":
        "{n} removida(s)",
    "cropped to {w}x{h}":
        "cortado para {w}x{h}",
    "Export failed:\n{error}":
        "Falha ao exportar:\n{error}",
    "{item} cleared.":
        "{item}: removido.",
    "Un-blurred: {reason}.":
        "Sem desfoque: {reason}.",
    "Blurred again: {reason}.":
        "Desfocado novamente: {reason}.",
    "detected text":
        "texto detectado",
    "Crop set to {w}x{h} at {x},{y} for all steps.":
        "Corte de {w}x{h} em {x},{y} para todas as etapas.",
    "Crop set to {w}x{h} at {x},{y} for this step.":
        "Corte de {w}x{h} em {x},{y} para esta etapa.",
    "Marker changed to {n}.":
        "Marcador alterado para {n}.",
    "Remove this click ring?":
        "Remover este anel de clique?",
    "Remove this arrow?":
        "Remover esta seta?",
    "Filled {n} empty caption(s) from {passages} spoken passage(s). Captions you typed were kept. Review them, then Save Changes. Full text: {file}":
        "{n} legenda(s) vazia(s) preenchida(s) a partir de {passages} trecho(s) falado(s). As legendas que você digitou foram mantidas. Revise-as e depois Salvar alterações. Texto completo: {file}",
    "Choose a file: {item}":
        "Escolher um arquivo: {item}",
    "{item} set for every export.":
        "{item}: definido para todas as exportações.",
    "Preview unavailable: {error}":
        "Pré-visualização indisponível: {error}",
    "System setting":
        "Configuração do sistema",
    "24-hour (14:05)":
        "24 horas (14:05)",
    "12-hour (2:05 PM)":
        "12 horas (2:05 PM)",
    "2026-11-22 (year-month-day)":
        "2026-11-22 (ano-mês-dia)",
    "11/22/2026 (month/day/year)":
        "11/22/2026 (mês/dia/ano)",
    "22/11/2026 (day/month/year)":
        "22/11/2026 (dia/mês/ano)",
    "22.11.2026 (day.month.year)":
        "22.11.2026 (dia.mês.ano)",
    "< Prev":
        "< Anterior",
}
