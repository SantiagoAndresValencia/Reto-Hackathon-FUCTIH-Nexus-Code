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

  // Transformar: guiar mientras se escribe si la merma, el costo y el precio están dentro de lo ideal
  document.querySelectorAll("[data-transformar]").forEach(function (form) {
    var disp = document.querySelector("[data-disponible]");
    var max = disp ? parseFloat(disp.getAttribute("data-disponible")) : NaN;
    var umbral = parseFloat(form.getAttribute("data-umbral-merma")) || 15;
    var objetivo = parseFloat(form.getAttribute("data-margen-objetivo")) || 30;
    var esAdmin = form.getAttribute("data-admin") === "si";
    var entrada = form.querySelector("#entrada"), salida = form.querySelector("#salida");
    var costo = form.querySelector("#costo_total"), precio = form.querySelector("#precio_venta");
    var ayudaE = document.getElementById("ayuda-entrada"), textoE = ayudaE ? ayudaE.textContent : "";
    var usar = form.querySelector("[data-usar-sugerido]"), sugerido = null;
    function kg(el) { return el && el.value.trim() !== "" ? parseFloat(el.value.replace(",", ".")) : NaN; }
    function cop(el) { return el && el.value.trim() !== "" ? parseFloat(el.value.replace(/[.\s]/g, "").replace(",", ".")) : NaN; }
    function miles(n) { return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
    function pct(n) { return n.toFixed(1).replace(".", ",") + " %"; }
    function guia(nombre, estado, html) {
      var el = form.querySelector('[data-guia="' + nombre + '"]');
      if (!el) return;
      el.hidden = !estado;
      el.className = "guia " + (estado || "");
      el.innerHTML = estado ? "<span>" + html + "</span>" : "";
    }
    function revisar() {
      var e = kg(entrada), s = kg(salida), c = cop(costo), p = cop(precio);
      if (ayudaE) {
        var excede = !isNaN(e) && !isNaN(max) && e > max;
        ayudaE.textContent = excede ? "Supera lo disponible: solo hay " + String(max).replace(".", ",") + " kg." : textoE;
        ayudaE.style.color = excede ? "var(--bloqueado)" : "";
        entrada.setAttribute("aria-invalid", String(excede));
      }

      // Merma: la ven ambos roles, igual que la alerta que se generará
      if (isNaN(e) || isNaN(s) || e <= 0) guia("merma", null);
      else if (s > e) guia("merma", "cuidado", "La salida supera la entrada: escriba la justificación.");
      else {
        var merma = (e - s) / e * 100;
        guia("merma", merma > umbral ? "fuera" : "ok", "Merma <b>" + pct(merma) + "</b> · " + (merma > umbral
          ? "fuera de lo ideal (máximo " + umbral + " %): se generará una alerta."
          : "dentro de lo ideal (máximo " + umbral + " %)."));
      }

      // Costo unitario, margen y precio sugerido: los números solo los ve el administrador
      var unitario = (!isNaN(c) && !isNaN(s) && s > 0) ? c / s : NaN;
      sugerido = isNaN(unitario) ? null : unitario / (1 - objetivo / 100);
      if (!isNaN(c) && s === 0) guia("costo", "fuera", "Con salida de 0 kg no se puede calcular el costo unitario: se generará una alerta.");
      else if (esAdmin && !isNaN(unitario)) guia("costo", "ok", "Costo unitario <b>" + miles(unitario) + " COP/kg</b> (costo total ÷ salida vendible).");
      else guia("costo", null);

      if (isNaN(unitario) || isNaN(p) || p <= 0) {
        guia("precio", esAdmin && sugerido ? "ok" : null,
          "Precio sugerido <b>" + (sugerido ? miles(sugerido) : "") + " COP/kg</b> para ganar " + objetivo + " % sobre la venta.");
      } else if (!esAdmin) {
        guia("precio", p <= unitario ? "fuera" : "ok", p <= unitario
          ? "El precio no cubre el costo por kg: se generará una alerta." : "El precio cubre el costo por kg.");
      } else {
        var m = (p - unitario) / p * 100;
        var bajo = m < objetivo - 0.05;
        guia("precio", p <= unitario ? "fuera" : (bajo ? "cuidado" : "ok"), "Margen <b>" + pct(m) + "</b> · " +
          (p <= unitario ? "el precio no cubre el costo unitario: se generará una alerta."
            : bajo ? "por debajo del objetivo de " + objetivo + " %." : "cumple el objetivo de " + objetivo + " %.") +
          " Precio sugerido <b>" + miles(sugerido) + " COP/kg</b>.");
      }
      if (usar) usar.hidden = !sugerido || (!isNaN(p) && p >= Math.round(sugerido));
    }
    if (usar) usar.addEventListener("click", function () {
      if (!sugerido) return;
      precio.value = Math.round(sugerido);
      revisar();
      precio.focus();
    });
    [entrada, salida, costo, precio].forEach(function (el) { if (el) el.addEventListener("input", revisar); });
    revisar();
  });
})();
