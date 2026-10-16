// Kaoka · interacciones. Todo funciona sin JavaScript; esto solo mejora la experiencia.
(function () {
  "use strict";

  // Menú lateral en celular
  document.querySelectorAll("[data-menu]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      var lateral = boton.closest(".lateral");
      var abierto = lateral.classList.toggle("abierta");
      boton.setAttribute("aria-expanded", String(abierto));
    });
  });

  // Pipeline: cada nodo muestra el detalle de su fase
  document.querySelectorAll("[data-pipeline]").forEach(function (pipeline) {
    var nodos = Array.prototype.slice.call(pipeline.querySelectorAll("[data-fase]"));
    if (!nodos.length) return;

    function activar(nodo, enfocar) {
      nodos.forEach(function (n) {
        var activo = n === nodo;
        n.setAttribute("aria-pressed", String(activo));
        var panel = document.getElementById(n.getAttribute("aria-controls"));
        if (panel) panel.classList.toggle("activa", activo);
      });
      if (enfocar) {
        var panel = document.getElementById(nodo.getAttribute("aria-controls"));
        if (panel) panel.focus({ preventScroll: true });
      }
      try { sessionStorage.setItem("kaoka:" + location.pathname, nodo.getAttribute("aria-controls")); } catch (e) {}
    }

    nodos.forEach(function (nodo, i) {
      nodo.addEventListener("click", function () { activar(nodo, false); });
      nodo.addEventListener("keydown", function (ev) {
        var destino = null;
        if (ev.key === "ArrowRight" || ev.key === "ArrowDown") destino = nodos[(i + 1) % nodos.length];
        if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") destino = nodos[(i - 1 + nodos.length) % nodos.length];
        if (ev.key === "Home") destino = nodos[0];
        if (ev.key === "End") destino = nodos[nodos.length - 1];
        if (destino) { ev.preventDefault(); destino.focus(); activar(destino, false); }
      });
    });

    var guardado = null;
    try { guardado = sessionStorage.getItem("kaoka:" + location.pathname); } catch (e) {}
    var inicial = nodos.filter(function (n) { return n.getAttribute("aria-controls") === guardado; })[0]
      || pipeline.querySelector("[data-inicial]") || nodos[0];
    // Si viene un error del servidor, mostrar la fase que se estaba editando
    activar(inicial, false);
    requestAnimationFrame(function () { pipeline.setAttribute("data-listo", ""); });
  });

  // Alertas: abrir y cerrar con movimiento suave
  document.querySelectorAll(".alerta-item").forEach(function (det) {
    var resumen = det.querySelector("summary");
    var cuerpo = det.querySelector(".alerta-cuerpo");
    if (!resumen || !cuerpo || !cuerpo.animate) return;
    resumen.addEventListener("click", function (ev) {
      if (!det.open) return; // al abrir, la animación CSS ya se encarga
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      ev.preventDefault();
      var anim = cuerpo.animate(
        [{ opacity: 1, transform: "none", filter: "blur(0)" }, { opacity: 0, transform: "translateY(-4px)", filter: "blur(3px)" }],
        { duration: 160, easing: "cubic-bezier(.32,.72,0,1)" }
      );
      anim.onfinish = function () { det.open = false; };
    });
  });

  // Filtros de la lista: aplicar al cambiar
  document.querySelectorAll("[data-auto-filtro] select").forEach(function (sel) {
    sel.addEventListener("change", function () { sel.form.requestSubmit ? sel.form.requestSubmit() : sel.form.submit(); });
  });

  // Usuarios de demostración: llenar el formulario
  document.querySelectorAll("[data-demo]").forEach(function (b) {
    b.addEventListener("click", function () {
      var u = document.getElementById("usuario"), c = document.getElementById("clave");
      if (!u || !c) return;
      u.value = b.getAttribute("data-demo");
      c.value = b.getAttribute("data-clave");
      c.form.querySelector("[type=submit]").focus();
    });
  });

  // Cambio de estado: el motivo es obligatorio antes de enviar
  document.querySelectorAll("[data-estado-form]").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      var motivo = form.querySelector("[name=motivo]");
      if (motivo && !motivo.value.trim()) {
        ev.preventDefault();
        motivo.setAttribute("aria-invalid", "true");
        motivo.focus();
        var ayuda = document.getElementById(motivo.getAttribute("aria-describedby"));
        if (ayuda) { ayuda.textContent = "Escriba el motivo antes de liberar o bloquear."; ayuda.style.color = "var(--bloqueado)"; }
      }
    });
  });

  // Transformar: avisar mientras se escribe si la entrada supera lo disponible o la merma pasa de 15 %
  document.querySelectorAll("[data-transformar]").forEach(function (form) {
    var disp = document.querySelector("[data-disponible]");
    var max = disp ? parseFloat(disp.getAttribute("data-disponible")) : NaN;
    var entrada = form.querySelector("#entrada"), salida = form.querySelector("#salida");
    var ayudaE = document.getElementById("ayuda-entrada"), ayudaS = form.querySelector("[data-merma-ayuda]");
    var textoE = ayudaE ? ayudaE.textContent : "", textoS = ayudaS ? ayudaS.textContent : "";
    function num(el) { return parseFloat(String(el.value).replace(",", ".")); }
    function revisar() {
      var e = num(entrada), s = num(salida);
      if (ayudaE) {
        var excede = !isNaN(e) && !isNaN(max) && e > max;
        ayudaE.textContent = excede ? "Supera lo disponible: solo hay " + String(max).replace(".", ",") + " kg." : textoE;
        ayudaE.style.color = excede ? "var(--bloqueado)" : "";
        entrada.setAttribute("aria-invalid", String(excede));
      }
      if (ayudaS) {
        if (!isNaN(e) && !isNaN(s) && e > 0 && s <= e) {
          var merma = (e - s) / e * 100;
          ayudaS.textContent = "Merma estimada: " + merma.toFixed(1) + " %" + (merma > 15 ? " · generará una alerta (> 15 %)." : ".");
          ayudaS.style.color = merma > 15 ? "var(--pendiente)" : "";
        } else if (!isNaN(e) && !isNaN(s) && s > e) {
          ayudaS.textContent = "La salida supera la entrada: escriba la justificación.";
          ayudaS.style.color = "var(--pendiente)";
        } else { ayudaS.textContent = textoS; ayudaS.style.color = ""; }
      }
    }
    [entrada, salida].forEach(function (el) { if (el) el.addEventListener("input", revisar); });
    revisar();
  });
})();
