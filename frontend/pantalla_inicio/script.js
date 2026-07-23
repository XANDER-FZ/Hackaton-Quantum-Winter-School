// =======================================
// Pantalla de inicio - Buscaminas Quaktico
// =======================================

document.addEventListener("DOMContentLoaded", () => {
  // =====================================
  // REFERENCIAS DEL MENÚ
  // =====================================

  const startBtn = document.getElementById("start-btn");

  const indicacionesBtn =
    document.getElementById("indicaciones-btn");

  const conceptosBtn =
    document.getElementById("conceptos-btn");


  // =====================================
  // REFERENCIAS DE LOS MODALES
  // =====================================

  const indicacionesModal =
    document.getElementById("indicaciones-modal");

  const conceptosModal =
    document.getElementById("conceptos-modal");

  const modalCloseButtons =
    document.querySelectorAll("[data-close]");


  // =====================================
  // REFERENCIAS DE AUDIO
  // =====================================

  const startSound =
    document.getElementById("start-sound");

  const secSound =
    document.getElementById("sec-sound");


  // =====================================
  // FUNCIONES DE SONIDO
  // =====================================

  /**
   * Reproduce un elemento de audio desde el inicio.
   *
   * La función evita errores si el audio no existe o
   * si el navegador bloquea temporalmente la reproducción.
   */
  function reproducirSonido(audio) {
    if (!(audio instanceof HTMLAudioElement)) {
      console.warn("No se encontró el elemento de audio.");
      return;
    }

    audio.pause();
    audio.currentTime = 0;

    const reproduccion = audio.play();

    if (reproduccion !== undefined) {
      reproduccion.catch((error) => {
        console.warn(
          "El navegador no pudo reproducir el sonido:",
          error,
        );
      });
    }
  }


  function reproducirSonidoSecundario() {
    reproducirSonido(secSound);
  }


  // =====================================
  // NAVEGACIÓN HACIA NICEGUI
  // =====================================

  startBtn?.addEventListener("click", () => {
    // Evita pulsar START varias veces rápidamente.
    startBtn.disabled = true;

    reproducirSonido(startSound);

    /*
     * Se espera medio segundo para escuchar el efecto
     * antes de abrir la ventana del juego.
     */
    window.setTimeout(() => {
      window.location.assign("/juego");
    }, 500);
  });


  // =====================================
  // FUNCIONES DE MODALES
  // =====================================

  function abrirModal(modal) {
    if (!modal) {
      return;
    }

    modal.style.display = "flex";
  }


  function cerrarModal(modal) {
    if (!modal) {
      return;
    }

    modal.style.display = "none";
  }


  // =====================================
  // BOTONES PARA ABRIR MODALES
  // =====================================

  indicacionesBtn?.addEventListener("click", () => {
    reproducirSonidoSecundario();
    abrirModal(indicacionesModal);
  });


  conceptosBtn?.addEventListener("click", () => {
    reproducirSonidoSecundario();
    abrirModal(conceptosModal);
  });


  // =====================================
  // BOTONES PARA CERRAR MODALES
  // =====================================

  modalCloseButtons.forEach((boton) => {
    boton.addEventListener("click", () => {
      reproducirSonidoSecundario();

      const modalId =
        boton.getAttribute("data-close");

      if (!modalId) {
        return;
      }

      const modal =
        document.getElementById(modalId);

      cerrarModal(modal);
    });
  });


  // Cerrar al hacer clic en el fondo oscuro.
  [indicacionesModal, conceptosModal].forEach((modal) => {
    modal?.addEventListener("click", (evento) => {
      if (evento.target === modal) {
        cerrarModal(modal);
      }
    });
  });


  // Cerrar al presionar Escape.
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") {
      cerrarModal(indicacionesModal);
      cerrarModal(conceptosModal);
    }
  });


  // =====================================
  // DATOS DEL CARRUSEL DE CONCEPTOS
  // =====================================

  const conceptos = [
    {
      titulo: "Qubit",
      descripcion:
        "Unidad básica de información cuántica. Puede representar 0, 1 o una combinación antes de medirse.",
    },
    {
      titulo: "Superposición",
      descripcion:
        "Un qubit puede estar en varias posibilidades al mismo tiempo hasta que se realiza una medición.",
    },
    {
      titulo: "Entrelazamiento",
      descripcion:
        "Dos qubits pueden estar conectados de forma que sus resultados estén relacionados.",
    },
    {
      titulo: "Interferencia",
      descripcion:
        "Las probabilidades pueden reforzarse o cancelarse para favorecer ciertos resultados.",
    },
    {
      titulo: "Medición",
      descripcion:
        "La medición convierte un estado cuántico en un resultado clásico, como 0 o 1.",
    },
    {
      titulo: "Compuerta cuántica",
      descripcion:
        "Es una operación que transforma el estado de un qubit. Ejemplos: H, X, Y y Z.",
    },
  ];


  // =====================================
  // REFERENCIAS DEL CARRUSEL
  // =====================================

  let conceptoActual = 0;

  const conceptTitle =
    document.getElementById("conceptTitle");

  const conceptDescription =
    document.getElementById("conceptDescription");

  const conceptCounter =
    document.getElementById("conceptCounter");

  const botonAnterior =
    document.getElementById("prevConcept");

  const botonSiguiente =
    document.getElementById("nextConcept");


  // =====================================
  // ACTUALIZACIÓN DEL CARRUSEL
  // =====================================

  function actualizarConcepto() {
    const concepto = conceptos[conceptoActual];

    if (conceptTitle) {
      conceptTitle.textContent =
        concepto.titulo;
    }

    if (conceptDescription) {
      conceptDescription.textContent =
        concepto.descripcion;
    }

    if (conceptCounter) {
      conceptCounter.textContent =
        `${conceptoActual + 1} / ${conceptos.length}`;
    }
  }


  // Siguiente concepto.
  botonSiguiente?.addEventListener("click", () => {
    reproducirSonidoSecundario();

    conceptoActual =
      (conceptoActual + 1) % conceptos.length;

    actualizarConcepto();
  });


  // Concepto anterior.
  botonAnterior?.addEventListener("click", () => {
    reproducirSonidoSecundario();

    conceptoActual =
      (
        conceptoActual
        - 1
        + conceptos.length
      ) % conceptos.length;

    actualizarConcepto();
  });


  // Mostrar el primer concepto al cargar.
  actualizarConcepto();
});