from collections.abc import Callable, Collection
from dataclasses import dataclass

from nicegui import ui


# ============================================================
# TIPOS DE FUNCIONES RECIBIDAS
# ============================================================

ManejadorCompuerta = Callable[[str], None]
AccionSinParametros = Callable[[], None]


# ============================================================
# INFORMACIÓN VISUAL DE LAS COMPUERTAS
# ============================================================

@dataclass(frozen=True, slots=True)
class CompuertaVisual:
    """Información necesaria para mostrar una compuerta."""

    codigo: str
    simbolo: str
    nombre: str
    descripcion: str
    casillas_requeridas: int


COMPUERTAS: tuple[CompuertaVisual, ...] = (
    CompuertaVisual(
        codigo="H",
        simbolo="H",
        nombre="Hadamard",
        descripcion=(
            "Genera interferencia entre dos casillas."
        ),
        casillas_requeridas=2,
    ),
    CompuertaVisual(
        codigo="X",
        simbolo="X",
        nombre="Pauli-X",
        descripcion=(
            "Intercambia el riesgo entre dos casillas."
        ),
        casillas_requeridas=2,
    ),
    CompuertaVisual(
        codigo="RX",
        simbolo="RX",
        nombre="Rotación-X",
        descripcion=(
            "Busca automáticamente una casilla asociada "
            "para modificar el riesgo."
        ),
        casillas_requeridas=1,
    ),
    CompuertaVisual(
        codigo="RY",
        simbolo="RY",
        nombre="Rotación-Y",
        descripcion=(
            "Busca una rotación que intente reducir "
            "el riesgo de la casilla elegida."
        ),
        casillas_requeridas=1,
    ),
    CompuertaVisual(
        codigo="CNOT",
        simbolo="CX",
        nombre="CNOT",
        descripcion=(
            "Usa dos casillas como control y dos "
            "como objetivo."
        ),
        casillas_requeridas=4,
    ),
)


# ============================================================
# COMPONENTE PRINCIPAL
# ============================================================

def crear_panel_cuantico(
    *,
    compuerta_seleccionada: str | None,
    casillas_seleccionadas: Collection[int],
    puede_usar_compuerta: bool,
    esperando_medicion: bool,
    partida_terminada: bool,
    riesgo_seleccionado: float | None,
    al_seleccionar_compuerta: ManejadorCompuerta,
    al_ejecutar_analisis: AccionSinParametros,
) -> None:
    """
    Construye el panel lateral de herramientas cuánticas.

    Este componente no modifica directamente el motor.
    Solamente muestra el estado y comunica las acciones
    seleccionadas por el usuario.
    """

    with ui.element("aside").classes("panel-cuantico"):

        crear_cabecera_panel(
            puede_usar_compuerta=puede_usar_compuerta,
            esperando_medicion=esperando_medicion,
            partida_terminada=partida_terminada,
        )

        crear_panel_compuertas(
            compuerta_seleccionada=compuerta_seleccionada,
            puede_usar_compuerta=puede_usar_compuerta,
            partida_terminada=partida_terminada,
            al_seleccionar_compuerta=al_seleccionar_compuerta,
        )

        crear_panel_probabilidad(
            riesgo_seleccionado=riesgo_seleccionado,
        )

        crear_panel_operacion(
            compuerta_seleccionada=compuerta_seleccionada,
            casillas_seleccionadas=casillas_seleccionadas,
            esperando_medicion=esperando_medicion,
        )

        crear_boton_ejecutar(
            compuerta_seleccionada=compuerta_seleccionada,
            casillas_seleccionadas=casillas_seleccionadas,
            puede_usar_compuerta=puede_usar_compuerta,
            partida_terminada=partida_terminada,
            al_ejecutar_analisis=al_ejecutar_analisis,
        )


# ============================================================
# CABECERA
# ============================================================

def crear_cabecera_panel(
    *,
    puede_usar_compuerta: bool,
    esperando_medicion: bool,
    partida_terminada: bool,
) -> None:
    """Crea el título y el mensaje superior del panel."""

    if partida_terminada:
        mensaje = "La partida ha terminado."

    elif esperando_medicion:
        mensaje = "Compuerta aplicada. Ahora debes medir."

    elif puede_usar_compuerta:
        mensaje = "Selecciona una herramienta de exploración."

    else:
        mensaje = "Realiza primero la medición inicial segura."

    with ui.row().classes(
        "cabecera-panel-cuantico"
    ):
        ui.icon(
            "psychology"
        ).classes(
            "icono-panel-cuantico"
        )

        with ui.column().classes("gap-0"):
            ui.label(
                "Panel cuántico"
            ).classes(
                "titulo-seccion"
            )

            ui.label(
                mensaje
            ).classes(
                "descripcion-seccion"
            )


# ============================================================
# PANEL DE COMPUERTAS
# ============================================================

def crear_panel_compuertas(
    *,
    compuerta_seleccionada: str | None,
    puede_usar_compuerta: bool,
    partida_terminada: bool,
    al_seleccionar_compuerta: ManejadorCompuerta,
) -> None:
    """Muestra todas las compuertas disponibles."""

    with ui.element("div").classes("bloque-panel"):

        crear_titulo_bloque(
            icono="memory",
            titulo="Compuertas",
        )

        ui.label(
            "Elige una compuerta y luego selecciona "
            "las casillas necesarias."
        ).classes(
            "texto-bloque"
        )

        with ui.column().classes("lista-compuertas"):

            for compuerta in COMPUERTAS:
                crear_boton_compuerta(
                    compuerta=compuerta,
                    esta_seleccionada=(
                        compuerta.codigo
                        == compuerta_seleccionada
                    ),
                    esta_habilitada=(
                        puede_usar_compuerta
                        and not partida_terminada
                    ),
                    al_seleccionar=al_seleccionar_compuerta,
                )


def crear_boton_compuerta(
    *,
    compuerta: CompuertaVisual,
    esta_seleccionada: bool,
    esta_habilitada: bool,
    al_seleccionar: ManejadorCompuerta,
) -> None:
    """Crea el botón de una compuerta individual."""

    clases = "boton-compuerta"

    if esta_seleccionada:
        clases += " boton-compuerta-activa"

    if not esta_habilitada:
        clases += " boton-compuerta-bloqueada"

    boton = ui.button(
        f"{compuerta.simbolo}  {compuerta.nombre}",
        on_click=lambda _evento, codigo=compuerta.codigo:
            al_seleccionar(codigo),
    ).props(
        "unelevated no-caps"
    ).classes(
        clases
    ).tooltip(
        (
            f"{compuerta.descripcion} "
            f"Requiere "
            f"{compuerta.casillas_requeridas} casilla(s)."
        )
    )

    if not esta_habilitada:
        boton.disable()


# ============================================================
# PANEL DE PROBABILIDAD
# ============================================================

def crear_panel_probabilidad(
    *,
    riesgo_seleccionado: float | None,
) -> None:
    """Muestra el riesgo de la casilla activa."""

    if riesgo_seleccionado is None:
        etiqueta = "Sin casilla seleccionada"
        porcentaje = "-- %"
        progreso = 0.0

    else:
        riesgo_normalizado = max(
            0.0,
            min(1.0, float(riesgo_seleccionado)),
        )

        etiqueta = "Riesgo estimado"
        porcentaje = f"{riesgo_normalizado * 100:.1f}%"
        progreso = riesgo_normalizado

    with ui.element("div").classes("bloque-panel"):

        crear_titulo_bloque(
            icono="query_stats",
            titulo="Probabilidad",
        )

        ui.label(
            "Probabilidad actual de que la casilla "
            "seleccionada contenga una mina."
        ).classes(
            "texto-bloque"
        )

        with ui.row().classes("fila-probabilidad"):
            ui.label(
                etiqueta
            ).classes(
                "valor-probabilidad"
            )

            ui.label(
                porcentaje
            ).classes(
                "porcentaje-probabilidad"
            )

        ui.linear_progress(
            value=progreso,
        ).props(
            "rounded"
        ).classes(
            "barra-probabilidad"
        )


# ============================================================
# RESUMEN DE LA OPERACIÓN
# ============================================================

def crear_panel_operacion(
    *,
    compuerta_seleccionada: str | None,
    casillas_seleccionadas: Collection[int],
    esperando_medicion: bool,
) -> None:
    """Muestra la operación que se está preparando."""

    compuerta = buscar_compuerta(
        compuerta_seleccionada
    )

    if esperando_medicion:
        titulo_operacion = "Operación aplicada"
        detalle = (
            "Selecciona una casilla del tablero "
            "para realizar la medición."
        )
        icono = "done_all"

    elif compuerta is None:
        titulo_operacion = "Sin operación"
        detalle = (
            "Selecciona una compuerta para "
            "preparar el análisis."
        )
        icono = "device_hub"

    else:
        cantidad_actual = len(
            casillas_seleccionadas
        )

        cantidad_necesaria = (
            compuerta.casillas_requeridas
        )

        titulo_operacion = (
            f"{compuerta.simbolo} — "
            f"{compuerta.nombre}"
        )

        detalle = (
            f"Casillas seleccionadas: "
            f"{cantidad_actual}/"
            f"{cantidad_necesaria}"
        )

        icono = "account_tree"

    with ui.element("div").classes("bloque-panel"):

        crear_titulo_bloque(
            icono="account_tree",
            titulo="Operación",
        )

        with ui.element("div").classes(
            "circuito-provisional"
        ):
            ui.icon(
                icono
            ).classes(
                "icono-circuito"
            )

            ui.label(
                titulo_operacion
            ).classes(
                "texto-circuito"
            )

            ui.label(
                detalle
            ).classes(
                "detalle-circuito"
            )


# ============================================================
# BOTÓN EJECUTAR
# ============================================================

def crear_boton_ejecutar(
    *,
    compuerta_seleccionada: str | None,
    casillas_seleccionadas: Collection[int],
    puede_usar_compuerta: bool,
    partida_terminada: bool,
    al_ejecutar_analisis: AccionSinParametros,
) -> None:
    """Crea y configura el botón Ejecutar análisis."""

    compuerta = buscar_compuerta(
        compuerta_seleccionada
    )

    seleccion_completa = (
        compuerta is not None
        and len(casillas_seleccionadas)
        == compuerta.casillas_requeridas
    )

    boton_habilitado = (
        seleccion_completa
        and puede_usar_compuerta
        and not partida_terminada
    )

    boton = ui.button(
        "EJECUTAR ANÁLISIS",
        icon="play_arrow",
        on_click=al_ejecutar_analisis,
    ).props(
        "unelevated no-caps"
    ).classes(
        "boton-ejecutar"
    )

    if not boton_habilitado:
        boton.disable()


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def buscar_compuerta(
    codigo: str | None,
) -> CompuertaVisual | None:
    """Busca la configuración visual de una compuerta."""

    if codigo is None:
        return None

    codigo_normalizado = codigo.strip().upper()

    for compuerta in COMPUERTAS:
        if compuerta.codigo == codigo_normalizado:
            return compuerta

    return None


def crear_titulo_bloque(
    *,
    icono: str,
    titulo: str,
) -> None:
    """Crea el encabezado reutilizable de un bloque."""

    with ui.row().classes("titulo-bloque"):

        ui.icon(
            icono
        ).classes(
            "icono-bloque"
        )

        ui.label(
            titulo
        ).classes(
            "nombre-bloque"
        )