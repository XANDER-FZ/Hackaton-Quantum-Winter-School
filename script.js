// =======================================
// Buscaminas Quaktico - script.js
// =======================================
// Este archivo controla SOLO:
// 1. Abrir y cerrar modales.
// 2. Cambiar de pantalla del menú a la zona de juego.
// 3. Volver de la zona de juego al menú.
// 4. Marcar visualmente qué compuerta fue seleccionada.
// 5. Cambiar el texto explicativo según la compuerta elegida.
// NO incluye lógica real de minas ni computación cuántica (eso lo implementarán tus compañeros).
// =======================================

// ---------------------------------------
// Referencias a elementos principales
// ---------------------------------------

// Pantallas
const mainMenuScreen = document.getElementById("main-menu");
const gameScreen = document.getElementById("game-screen");

// Botones de navegación
const startBtn = document.getElementById("start-btn");
const backBtn = document.getElementById("back-btn");

// Botones que abren modales
const indicacionesBtn = document.getElementById("indicaciones-btn");
const conceptosBtn = document.getElementById("conceptos-btn");

// Modales
const indicacionesModal = document.getElementById("indicaciones-modal");
const conceptosModal = document.getElementById("conceptos-modal");

// Botones de cierre de modales (X y botones Cerrar con data-close)
const modalCloseButtons = document.querySelectorAll("[data-close]");

// Botones de compuertas cuánticas
const gateButtons = document.querySelectorAll(".gate-btn");

// Texto dinámico donde se muestra la explicación de la compuerta seleccionada
const gateDescription = document.getElementById("gate-description");

// ---------------------------------------
// Diccionario de textos por compuerta
// ---------------------------------------
// Aquí definimos los mensajes que se mostrarán
// cuando el usuario selecciona una compuerta.
// Tus compañeros pueden extender o cambiar estos textos
// si quieren conexiones más profundas con la lógica del juego.

const GATE_TEXTS = {
  H: "Superposición: explora posibilidades.",
  X: "Cambio de estado: alterna entre 0 y 1.",
  Y: "Cambio y fase: combina transformación e interferencia.",
  Z: "Fase: modifica la interferencia.",
  Medir: "Colapso: revela un resultado clásico."
};

// ---------------------------------------
// Funciones auxiliares de pantallas
// ---------------------------------------

/**
 * Cambia la pantalla visible entre menú principal y zona de juego.
 * Solo manipula clases CSS para mostrar/ocultar secciones.
 */
function showGameScreen() {
  mainMenuScreen.classList.remove("active-screen");
  gameScreen.classList.add("active-screen");
}

/**
 * Vuelve desde la zona de juego al menú principal.
 */
function showMainMenu() {
  gameScreen.classList.remove("active-screen");
  mainMenuScreen.classList.add("active-screen");
}

// ---------------------------------------
// Funciones auxiliares de modales
// ---------------------------------------

/**
 * Abre un modal específico añadiendo "flex" a su display
 * (el CSS usa display: none por defecto).
 * @param {HTMLElement} modalElement
 */
function openModal(modalElement) {
  if (!modalElement) return;
  modalElement.style.display = "flex";
}

/**
 * Cierra un modal específico restaurando display: none.
 * @param {HTMLElement} modalElement
 */
function closeModal(modalElement) {
  if (!modalElement) return;
  modalElement.style.display = "none";
}

// ---------------------------------------
// Funciones auxiliares de compuertas
// ---------------------------------------

/**
 * Marca visualmente la compuerta seleccionada
 * y actualiza el texto explicativo.
 * @param {string} gateName - nombre de la compuerta (H, X, Y, Z, Medir)
 */
function selectGate(gateName) {
  // Quitar la clase "selected" de todas las compuertas
  gateButtons.forEach((btn) => {
    btn.classList.remove("selected");
  });

  // Buscar el botón que corresponde a la compuerta seleccionada
  const selectedButton = Array.from(gateButtons).find(
    (btn) => btn.dataset.gate === gateName
  );

  if (selectedButton) {
    // Agregar clase "selected" para cambiar su estilo (CSS)
    selectedButton.classList.add("selected");
  }

  // Actualizar el texto en la zona de explicación
  const newText = GATE_TEXTS[gateName] || "Compuerta no definida.";
  gateDescription.textContent = newText;
}

// ---------------------------------------
// Asignación de eventos
// ---------------------------------------

// Botón START pasa del menú a la zona de juego
startBtn.addEventListener("click", () => {
  showGameScreen();
});

// Botón Volver regresa al menú
backBtn.addEventListener("click", () => {
  showMainMenu();
});

// Botón Indicaciones abre su modal
indicacionesBtn.addEventListener("click", () => {
  openModal(indicacionesModal);
});

// Botón Conceptos básicos abre su modal
conceptosBtn.addEventListener("click", () => {
  openModal(conceptosModal);
});

// Botones que cierran modales (X y Cerrar)
// Utilizamos data-close para identificar qué modal cerrar
modalCloseButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const modalId = button.getAttribute("data-close");
    const modalElement = document.getElementById(modalId);
    closeModal(modalElement);
  });
});

// Cerrar modales si se hace clic en el fondo (overlay) fuera de la caja
[indicacionesModal, conceptosModal].forEach((overlay) => {
  overlay.addEventListener("click", (event) => {
    // Si el usuario hace clic directamente en la capa oscura (overlay),
    // y no dentro del modal, cerramos.
    if (event.target === overlay) {
      closeModal(overlay);
    }
  });
});

// Selección de compuertas cuánticas
gateButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const gateName = button.dataset.gate;
    selectGate(gateName);
  });
});

// ---------------------------------------
// Punto de extensión para tus compañeros
// ---------------------------------------
// Tus compañeros pueden usar estos elementos y eventos para conectar la lógica real:
// - Las celdas del tablero (.cell) se pueden convertir en botones interactivos,
//   leyendo su posición con índices.
// - Pueden escuchar el gateName seleccionado desde selectGate()
//   (por ejemplo, guardando la compuerta activa en una variable global).
// - Pueden actualizar los indicadores "Intentos" y "Riesgo"
//   modificando el DOM de attempts-counter y risk-indicator.
// - En lugar de solo mostrar una maqueta, pueden regenerar el tablero dinámicamente
//   con JavaScript, asignando minas y estados cuánticos por casilla.