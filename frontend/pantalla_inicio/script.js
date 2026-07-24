// ============================================================
// BUSCAMINAS QUAKTICO — PANTALLA DE INICIO
// ============================================================
//
// Este archivo controla únicamente:
//
// 1. El botón START.
// 2. Los sonidos de la pantalla inicial.
// 3. Los modales de Indicaciones y Conceptos.
// 4. El carrusel de conceptos básicos.
//
// La lógica del juego se ejecuta en NiceGUI mediante la ruta:
//
// /juego
//
// ============================================================


document.addEventListener("DOMContentLoaded", () => {
  // ==========================================================
  // ELEMENTOS PRINCIPALES
  // ==========================================================

  const startBtn = document.getElementById("start-btn");

  const indicacionesBtn = document.getElementById(
    "indicaciones-btn"
  );

  const conceptosBtn = document.getElementById(
    "conceptos-btn"
  );

  const indicacionesModal = document.getElementById(
    "indicaciones-modal"
  );

  const conceptosModal = document.getElementById(
    "conceptos-modal"
  );

  const modalCloseButtons = document.querySelectorAll(
    "[data-close]"
  );

  const startSound = document.getElementById(
    "start-sound"
  );

  const secSound = document.getElementById(
    "sec-sound"
  );

  const prevConceptBtn = document.getElementById(
    "prevConcept"
  );

  const nextConceptBtn = document.getElementById(
    "nextConcept"
  );

  const conceptTitle = document.getElementById(
    "conceptTitle"
  );

  const conceptDescription = document.getElementById(
    "conceptDescription"
  );

  const conceptCounter = document.getElementById(
    "conceptCounter"
  );


  // ==========================================================
  // REPRODUCCIÓN SEGURA DE AUDIO
  // ==========================================================

  /**
   * Reproduce un elemento de audio sin detener el programa
   * cuando el navegador bloquea la reproducción.
   *
   * @param {HTMLAudioElement | null} audioElement
   */
  function reproducirAudio(audioElement) {
    if (!(audioElement instanceof HTMLAudioElement)) {
      return;
    }

    audioElement.currentTime = 0;

    const reproduccion = audioElement.play();

    if (
      reproduccion
      && typeof reproduccion.catch === "function"
    ) {
      reproduccion.catch((error) => {
        console.warn(
          "No se pudo reproducir el audio:",
          error
        );
      });
    }
  }


  // ==========================================================
  // NAVEGACIÓN HACIA LA PARTIDA
  // ==========================================================

  function iniciarPartida() {
    if (!startBtn) {
      return;
    }

    // Impide que el usuario pulse varias veces el botón.
    startBtn.disabled = true;
    startBtn.setAttribute("aria-busy", "true");

    reproducirAudio(startSound);

    // Dejamos un pequeño tiempo para escuchar el sonido.
    window.setTimeout(() => {
      window.location.assign("/juego");
    }, 500);
  }


  if (startBtn) {
    startBtn.addEventListener(
      "click",
      iniciarPartida
    );
  }


  // ==========================================================
  // FUNCIONES DE LOS MODALES
  // ==========================================================

  /**
   * Abre un modal.
   *
   * @param {HTMLElement | null} modalElement
   */
  function abrirModal(modalElement) {
    if (!modalElement) {
      return;
    }

    reproducirAudio(secSound);

    modalElement.style.display = "flex";
    modalElement.setAttribute(
      "aria-hidden",
      "false"
    );

    document.body.classList.add(
      "modal-abierto"
    );
  }


  /**
   * Cierra un modal.
   *
   * @param {HTMLElement | null} modalElement
   */
  function cerrarModal(modalElement) {
    if (!modalElement) {
      return;
    }

    reproducirAudio(secSound);

    modalElement.style.display = "none";
    modalElement.setAttribute(
      "aria-hidden",
      "true"
    );

    const existeModalVisible = [
      indicacionesModal,
      conceptosModal
    ].some(
      (modal) => (
        modal
        && modal.style.display === "flex"
      )
    );

    if (!existeModalVisible) {
      document.body.classList.remove(
        "modal-abierto"
      );
    }
  }


  if (indicacionesBtn) {
    indicacionesBtn.addEventListener(
      "click",
      () => {
        abrirModal(indicacionesModal);
      }
    );
  }


  if (conceptosBtn) {
    conceptosBtn.addEventListener(
      "click",
      () => {
        abrirModal(conceptosModal);
      }
    );
  }


  modalCloseButtons.forEach((button) => {
    button.addEventListener(
      "click",
      () => {
        const modalId = button.getAttribute(
          "data-close"
        );

        if (!modalId) {
          return;
        }

        const modalElement = document.getElementById(
          modalId
        );

        cerrarModal(modalElement);
      }
    );
  });


  // Cerrar al pulsar directamente sobre el fondo oscuro.
  [
    indicacionesModal,
    conceptosModal
  ].forEach((modal) => {
    if (!modal) {
      return;
    }

    modal.addEventListener(
      "click",
      (event) => {
        if (event.target === modal) {
          cerrarModal(modal);
        }
      }
    );
  });


  // Cerrar el modal mediante la tecla Escape.
  document.addEventListener(
    "keydown",
    (event) => {
      if (event.key !== "Escape") {
        return;
      }

      if (
        conceptosModal
        && conceptosModal.style.display === "flex"
      ) {
        cerrarModal(conceptosModal);
        return;
      }

      if (
        indicacionesModal
        && indicacionesModal.style.display === "flex"
      ) {
        cerrarModal(indicacionesModal);
      }
    }
  );


  // ==========================================================
  // CONCEPTOS BÁSICOS
  // ==========================================================

  const conceptos = [
    {
      titulo: "Qubit",
      descripcion:
        "Es la unidad básica de información cuántica. "
        + "Antes de medirse puede representar una "
        + "combinación de los estados 0 y 1."
    },
    {
      titulo: "Superposición",
      descripcion:
        "Permite que un sistema cuántico mantenga "
        + "varias posibilidades al mismo tiempo "
        + "antes de realizar una medición."
    },
    {
      titulo: "Entrelazamiento",
      descripcion:
        "Relaciona el estado de dos o más qubits. "
        + "La información de uno puede quedar "
        + "vinculada con la de los demás."
    },
    {
      titulo: "Interferencia",
      descripcion:
        "Las amplitudes cuánticas pueden reforzarse "
        + "o cancelarse, modificando las "
        + "probabilidades de los resultados."
    },
    {
      titulo: "Medición",
      descripcion:
        "Convierte el estado cuántico en un resultado "
        + "clásico observable. En el juego, permite "
        + "descubrir si una casilla es segura."
    },
    {
      titulo: "Compuerta cuántica",
      descripcion:
        "Es una operación que transforma un estado "
        + "cuántico. El juego utiliza compuertas como "
        + "H, X, RX, RY y CNOT."
    }
  ];

  let indiceConcepto = 0;


  function actualizarConcepto() {
    if (
      !conceptTitle
      || !conceptDescription
      || !conceptCounter
    ) {
      return;
    }

    const concepto = conceptos[indiceConcepto];

    conceptTitle.textContent = concepto.titulo;

    conceptDescription.textContent =
      concepto.descripcion;

    conceptCounter.textContent =
      `${indiceConcepto + 1} / ${conceptos.length}`;
  }


  function mostrarConceptoSiguiente() {
    indiceConcepto = (
      indiceConcepto + 1
    ) % conceptos.length;

    reproducirAudio(secSound);
    actualizarConcepto();
  }


  function mostrarConceptoAnterior() {
    indiceConcepto = (
      indiceConcepto - 1
      + conceptos.length
    ) % conceptos.length;

    reproducirAudio(secSound);
    actualizarConcepto();
  }


  if (nextConceptBtn) {
    nextConceptBtn.addEventListener(
      "click",
      mostrarConceptoSiguiente
    );
  }


  if (prevConceptBtn) {
    prevConceptBtn.addEventListener(
      "click",
      mostrarConceptoAnterior
    );
  }


  // Mostrar el primer concepto al cargar la página.
  actualizarConcepto();
});