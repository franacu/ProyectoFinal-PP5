// CRCE — interfaz gráfica. Una sola página: inicio de sesión con Keycloak y una pantalla por perfil.
// No contiene reglas de negocio: muestra lo que la API permite y explica lo que rechaza.
"use strict";

// ── Estado y utilidades ───────────────────────────────────────

const estado = { token: null, usuario: null, perfil: null, config: null, vista: null };

const NOMBRES = {
  reportante: "Reportante institucional", operador: "Operador de coordinación", jefe_unidad: "Jefe de unidad",
  responsable_recursos: "Responsable de recursos", supervisor: "Supervisor regional",
  inundacion: "Inundación", incendio: "Incendio", accidente_vial: "Accidente vial",
  alta: "Alta", media: "Media", baja: "Baja",
  pendiente: "Pendiente", aceptado: "Aceptado", descartado: "Descartado", abierta: "Abierta", cerrada: "Cerrada",
  asignada: "Asignada", en_ejecucion: "En ejecución", finalizada: "Finalizada", cancelada: "Cancelada",
  evacuacion: "Evacuación", rescate: "Rescate", asistencia_sanitaria: "Asistencia sanitaria",
  conduccion: "Conducción", primeros_auxilios: "Primeros auxilios",
  transporte_de_personas: "Transporte de personas", vehiculo_de_rescate: "Vehículo de rescate", ambulancia: "Ambulancia",
  equipo_de_rescate: "Equipo de rescate", equipo_sanitario: "Equipo sanitario",
  operativo: "Operativo", fuera_de_servicio: "Fuera de servicio", habilitada: "Habilitada", en_mantenimiento: "En mantenimiento",
  satisfactorio: "Satisfactorio", no_satisfactorio: "No satisfactorio",
};
const nombre = (v) => NOMBRES[v] ?? String(v ?? "—").replaceAll("_", " ");
// Operaciones del historial: "mision_asignada" → "Misión asignada".
const nombreOperacion = (op) => { const t = op.replaceAll("_", " ").replace(/\bmision\b/, "misión"); return t[0].toUpperCase() + t.slice(1); };
// Los identificadores generados son largos: se muestran sus primeros 8 caracteres.
const corto = (id) => /^[0-9a-f]{8}-[0-9a-f-]{27}$/.test(id) ? id.slice(0, 8) : id;
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fecha = (iso) => iso ? new Date(iso).toLocaleString("es-AR", { dateStyle: "short", timeStyle: "short" }) : "—";
const $ = (sel, raiz = document) => raiz.querySelector(sel);
const opciones = (valores, elegido) => valores.map((v) => `<option value="${v}" ${v === elegido ? "selected" : ""}>${esc(nombre(v))}</option>`).join("");

const TIPOS = ["inundacion", "incendio", "accidente_vial"];
const GRAVEDADES = ["alta", "media", "baja"];
const TIPOS_MISION = ["evacuacion", "rescate", "asistencia_sanitaria"];
const COMPETENCIAS = ["conduccion", "evacuacion", "rescate", "primeros_auxilios"];
const CATEGORIAS_VEHICULO = ["transporte_de_personas", "vehiculo_de_rescate", "ambulancia"];
const CATEGORIAS_EQUIPO = ["equipo_de_rescate", "equipo_sanitario"];
const CONDICIONES = ["habilitada", "en_mantenimiento", "fuera_de_servicio"];

function etiquetaEstado(valor) {
  const tono = { pendiente: "activo", asignada: "activo", en_ejecucion: "activo", abierta: "activo",
    aceptado: "fin", finalizada: "fin", habilitada: "fin",
    descartado: "baja-estado", cancelada: "baja-estado", cerrada: "", en_mantenimiento: "baja-estado", fuera_de_servicio: "baja-estado" }[valor];
  return `<span class="etiqueta ${tono ? "etiqueta--" + tono : ""}">${esc(nombre(valor))}</span>`;
}
const etiquetaGravedad = (g) => `<span class="etiqueta etiqueta--${g}">Gravedad ${esc(nombre(g))}</span>`;

// ── Comunicación con la API ───────────────────────────────────

class ErrorDeApi extends Error {
  constructor(codigo, cuerpo) {
    const detalle = typeof cuerpo?.detail === "string" ? cuerpo.detail
      : Array.isArray(cuerpo?.detail) ? cuerpo.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join("; ")
      : "Error inesperado";
    super(detalle);
    this.codigo = codigo;
    this.tipo = cuerpo?.error ?? (codigo === 422 ? "Datos inválidos" : codigo === 403 ? "Sin permiso" : "");
  }
}

async function api(metodo, ruta, cuerpo) {
  const respuesta = await fetch(ruta, {
    method: metodo,
    headers: { Authorization: `Bearer ${estado.token}`, ...(cuerpo ? { "Content-Type": "application/json" } : {}) },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const datos = respuesta.status === 204 ? null : await respuesta.json().catch(() => null);
  if (respuesta.status === 401) { cerrarSesion("La sesión venció. Volvé a ingresar."); throw new ErrorDeApi(401, datos); }
  if (!respuesta.ok) throw new ErrorDeApi(respuesta.status, datos);
  return datos;
}

function mostrarMensaje(tipo, texto, motivo = "") {
  const caja = $("#mensaje");
  caja.className = `mensaje mensaje--${tipo}`;
  caja.innerHTML = `${esc(texto)}${motivo ? `<span class="mensaje__motivo">${esc(motivo)}</span>` : ""}`;
  caja.hidden = false;
  caja.scrollIntoView({ block: "nearest" });
}

/** Ejecuta una operación, informa el resultado y vuelve a dibujar la vista actual. */
async function operar(descripcionExito, accion) {
  try {
    await accion();
    await dibujarVista();
    mostrarMensaje("ok", descripcionExito);
  } catch (error) {
    if (!(error instanceof ErrorDeApi)) throw error;
    mostrarMensaje("error", `No se pudo completar: ${error.message}`,
      [error.tipo, error.codigo && `código ${error.codigo}`].filter(Boolean).join(" · "));
  }
}

// ── Sesión ────────────────────────────────────────────────────

function datosDelToken(token) {
  const parte = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(decodeURIComponent(escape(atob(parte))));
}

async function iniciarSesion(usuario, clave) {
  const { keycloak_url, realm, client_id } = estado.config;
  const respuesta = await fetch(`${keycloak_url}/realms/${realm}/protocol/openid-connect/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id, grant_type: "password", username: usuario, password: clave }),
  });
  if (!respuesta.ok) throw new Error(respuesta.status === 401 ? "Usuario o contraseña incorrectos." : "Keycloak no respondió. ¿Está encendido?");
  const { access_token } = await respuesta.json();
  const datos = datosDelToken(access_token);
  const perfil = (datos.realm_access?.roles ?? []).find((r) => r in VISTAS);
  if (!perfil) throw new Error("El usuario no tiene ninguno de los cinco perfiles.");
  Object.assign(estado, { token: access_token, usuario: datos.preferred_username, perfil });
  sessionStorage.setItem("crce-token", access_token);
}

function cerrarSesion(motivo) {
  Object.assign(estado, { token: null, usuario: null, perfil: null, vista: null });
  sessionStorage.removeItem("crce-token");
  $("#pantalla-app").hidden = true;
  $("#pantalla-ingreso").hidden = false;
  const error = $("#error-ingreso");
  error.textContent = motivo ?? "";
  error.hidden = !motivo;
}

function abrirAplicacion() {
  $("#pantalla-ingreso").hidden = true;
  $("#pantalla-app").hidden = false;
  $("#nombre-usuario").textContent = estado.usuario;
  $("#perfil-usuario").textContent = nombre(estado.perfil);
  const menu = $("#menu");
  menu.innerHTML = VISTAS[estado.perfil].map(([titulo], i) => `<button type="button" data-i="${i}">${esc(titulo)}</button>`).join("");
  menu.onclick = (e) => { if (e.target.dataset.i !== undefined) irA(VISTAS[estado.perfil][e.target.dataset.i][1]); };
  irA(VISTAS[estado.perfil][0][1]);
}

async function irA(vista, ...argumentos) {
  estado.vista = { vista, argumentos };
  $("#mensaje").hidden = true;
  marcarMenu(vista);
  await dibujarVista();
}

function marcarMenu(vista) {
  for (const boton of $("#menu").children) {
    if (VISTAS[estado.perfil][boton.dataset.i][1] === vista) boton.setAttribute("aria-current", "page");
    else boton.removeAttribute("aria-current");
  }
}

async function dibujarVista() {
  const { vista, argumentos } = estado.vista;
  const contenedor = $("#vista");
  try {
    contenedor.innerHTML = await vista(...argumentos);
    contenedor.querySelectorAll("form[data-accion]").forEach((f) => f.addEventListener("submit", enviarFormulario));
    contenedor.querySelectorAll("[data-ir]").forEach((b) => b.addEventListener("click", () => irA(VISTA_POR_NOMBRE[b.dataset.ir], b.dataset.id)));
    mostrarCantidadSoloEnEvacuacion(contenedor);
  } catch (error) {
    if (!(error instanceof ErrorDeApi)) throw error;
    contenedor.innerHTML = "";
    mostrarMensaje("error", `No se pudo cargar: ${error.message}`, error.tipo);
  }
}

// La cantidad de personas solo tiene sentido en una evacuación: el campo aparece solo para ese tipo.
function mostrarCantidadSoloEnEvacuacion(contenedor) {
  const form = contenedor.querySelector('form[data-accion="crearMision"]');
  if (!form) return;
  const tipo = form.querySelector('select[name="tipo"]');
  const campo = form.querySelector(".solo-evacuacion");
  const actualizar = () => {
    campo.hidden = tipo.value !== "evacuacion";
    if (campo.hidden) campo.querySelector("input").value = "";
  };
  tipo.addEventListener("change", actualizar);
  actualizar();
}

// Cada formulario declara su acción en data-accion; los datos salen de sus campos.
function enviarFormulario(evento) {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form));
  datos.competencias = new FormData(form).getAll("competencias");
  const accion = ACCIONES[form.dataset.accion];
  operar(accion.exito, () => accion.hacer(form.dataset, datos, form));
}

// ── Fragmentos reutilizables ──────────────────────────────────

const vacio = (texto) => `<p class="vacio">${esc(texto)}</p>`;

function bloqueHistorial(registros) {
  if (!registros.length) return vacio("Sin registros.");
  return `<ol class="historial">${registros.map((r) => {
    const detalle = Object.entries(r.detalle).map(([k, v]) => `${k.replaceAll("_", " ")}: ${nombre(corto(v))}`).join(" · ");
    return `<li><time>${fecha(r.fecha_hora)}</time><strong>${esc(nombreOperacion(r.operacion))}</strong> por ${esc(r.actor_id)}
      ${r.recursos.length ? `<span class="dato">· ${esc(r.recursos.map(corto).join(", "))}</span>` : ""}
      ${detalle ? `<span class="dato">· ${esc(detalle)}</span>` : ""}</li>`;
  }).join("")}</ol>`;
}

function cabezaAviso(a) {
  return `<div class="tarjeta__cabeza">
      <span class="tarjeta__titulo">${esc(nombre(a.tipo))} · ${esc(a.ubicacion.direccion)}, ${esc(a.ubicacion.localidad)}</span>
      ${etiquetaEstado(a.estado)} ${etiquetaGravedad(a.gravedad_estimada)}
      <span class="dato">Registrado ${fecha(a.registrado_en)} por ${esc(a.reportante_id)}</span>
    </div>
    <p>${esc(a.descripcion)}</p>
    ${a.notas.length ? `<p class="dato"><strong>Notas:</strong></p><ul>${a.notas.map((n) => `<li>${esc(n.texto)} <span class="dato">(${fecha(n.fecha_hora)})</span></li>`).join("")}</ul>` : ""}
    ${a.descarte ? `<p class="dato"><strong>Descartado por ${esc(a.descarte.operador_id)}:</strong> ${esc(a.descarte.justificacion)}</p>` : ""}`;
}

// ── Reportante (§2.1) ─────────────────────────────────────────

async function vistaMisAvisos() {
  const avisos = await api("GET", "/avisos");
  const tarjetas = await Promise.all(avisos.reverse().map(async (a) => {
    let emergencia = "";
    if (a.estado === "aceptado") {
      const e = await api("GET", `/avisos/${a.id}/emergencia`);
      emergencia = `<p><strong>Emergencia originada:</strong> ${esc(nombre(e.tipo))} · ${etiquetaGravedad(e.gravedad)} ${etiquetaEstado(e.estado)}</p>`;
    }
    const nota = a.estado === "pendiente" ? `<form class="acciones" data-accion="nota" data-id="${a.id}">
        <label>Agregar una nota <input name="texto" required placeholder="Información nueva sobre la situación"></label>
        <button class="boton">Agregar nota</button></form>` : "";
    return `<article class="tarjeta">${cabezaAviso(a)}${emergencia}${nota}</article>`;
  }));
  return `<h2>Mis avisos</h2><p class="intro">Solo ves los avisos que registraste. Mientras estén pendientes podés agregarles notas.</p>
    <div class="lista">${tarjetas.join("") || vacio("Todavía no registraste avisos.")}</div>`;
}

async function vistaNuevoAviso() {
  return `<h2>Nuevo aviso</h2><p class="intro">Informá la situación. Un operador la va a evaluar.</p>
    <form class="formulario" data-accion="nuevoAviso">
      <div class="fila"><label>Dirección <input name="direccion" required></label><label>Localidad <input name="localidad" required value="Ushuaia"></label></div>
      <div class="fila"><label>Tipo de situación <select name="tipo">${opciones(TIPOS)}</select></label>
        <label>Gravedad estimada <select name="gravedad">${opciones(GRAVEDADES, "media")}</select></label></div>
      <label>Descripción <textarea name="descripcion" required></textarea></label>
      <div><button class="boton boton--principal">Registrar aviso</button></div>
    </form>`;
}

// ── Operador (§2.2) ───────────────────────────────────────────

async function vistaPendientes() {
  const avisos = await api("GET", "/avisos?estado=pendiente");
  return `<h2>Avisos pendientes</h2><p class="intro">Aceptá el aviso confirmando o corrigiendo tipo y gravedad, o descartalo con una justificación.</p>
    <div class="lista">${avisos.map((a) => `<article class="tarjeta">${cabezaAviso(a)}
      <div class="acciones">
        <form data-accion="aceptar" data-id="${a.id}">
          <label>Tipo <select name="tipo">${opciones(TIPOS, a.tipo)}</select></label>
          <label>Gravedad <select name="gravedad">${opciones(GRAVEDADES, a.gravedad_estimada)}</select></label>
          <button class="boton boton--principal">Aceptar</button>
        </form>
        <form data-accion="descartar" data-id="${a.id}">
          <label>Justificación <input name="justificacion" placeholder="Motivo del descarte"></label>
          <button class="boton boton--peligro">Descartar</button>
        </form>
      </div></article>`).join("") || vacio("No hay avisos pendientes.")}</div>`;
}

async function vistaEmergencias() {
  const supervisor = estado.perfil === "supervisor";
  const emergencias = await api("GET", supervisor ? "/emergencias/todas" : "/emergencias");
  const filas = emergencias.map((e, i) => `<div class="triage triage--${e.gravedad}">
      <span class="triage__orden" title="Orden de atención">${e.estado === "abierta" && !supervisor ? i + 1 : ""}</span>
      <div><div class="tarjeta__cabeza"><span class="tarjeta__titulo">${esc(nombre(e.tipo))} · ${esc(e.ubicacion.direccion)}</span>
        ${etiquetaGravedad(e.gravedad)} ${etiquetaEstado(e.estado)}</div>
        <span class="dato">Aceptada ${fecha(e.creada_en)} · ${e.misiones.length} misión(es): ${esc(e.misiones.map((m) => nombre(m.estado)).join(", ") || "ninguna")}</span></div>
      <button class="boton" data-ir="detalleEmergencia" data-id="${e.id}">Abrir</button>
    </div>`).join("");
  const intro = supervisor ? "Todas las emergencias, abiertas y cerradas." : "Emergencias abiertas en orden de atención: gravedad Alta, Media y Baja; a igual gravedad, la más antigua primero.";
  return `<h2>Emergencias</h2><p class="intro">${intro}</p><div class="lista">${filas || vacio("No hay emergencias.")}</div>`;
}

async function vistaDetalleEmergencia(id) {
  const e = await api("GET", `/emergencias/${id}`);
  const operador = estado.perfil === "operador";
  const abierta = e.estado === "abierta";
  const unidades = operador && abierta ? await api("GET", "/unidades") : [];
  const libres = unidades.filter((u) => !u.mision_comprometida_id);
  const elegirUnidad = `<select name="unidad_id">${libres.map((u) => `<option value="${u.id}">${esc(u.id)} · ${esc(nombre(u.vehiculo.categoria))}${u.condicion !== "habilitada" ? " (" + esc(nombre(u.condicion)) + ")" : ""}</option>`).join("")}</select>`;

  const misiones = e.misiones.map((m) => {
    let acciones = "";
    if (operador && abierta && m.estado === "pendiente") acciones = `<form data-accion="asignar" data-id="${m.id}" data-emergencia="${e.id}">${elegirUnidad}<button class="boton boton--principal boton--chico">Asignar</button></form>`;
    if (operador && abierta && m.estado === "asignada") acciones = `<form data-accion="reasignar" data-id="${m.id}" data-emergencia="${e.id}">${elegirUnidad}<button class="boton boton--chico">Reasignar</button></form>`;
    if (operador && abierta && ["pendiente", "asignada"].includes(m.estado)) acciones += `<form data-accion="cancelar" data-id="${m.id}" data-emergencia="${e.id}"><button class="boton boton--peligro boton--chico">Cancelar</button></form>`;
    return `<tr><td><strong>${esc(nombre(m.tipo))}</strong>${m.cantidad_personas ? ` · ${m.cantidad_personas} personas` : ""}<br><span class="dato">${esc(m.objetivo)}</span></td>
      <td>${etiquetaEstado(m.estado)}</td><td class="id">${esc(m.unidad_id ?? "—")}</td>
      <td>${m.resultado ? `${esc(nombre(m.resultado.resultado))}: ${esc(m.resultado.tareas)}` : m.novedades.map((n) => esc(n.texto)).join("<br>") || "—"}</td>
      <td><div class="acciones">${acciones}</div></td></tr>`;
  }).join("");

  const crear = operador && abierta ? `<form class="formulario seccion" data-accion="crearMision" data-emergencia="${e.id}">
      <h3>Nueva misión</h3>
      <div class="fila"><label>Tipo <select name="tipo">${opciones(TIPOS_MISION)}</select></label>
        <label class="solo-evacuacion">Personas a evacuar <input name="cantidad_personas" type="number" min="1"></label></div>
      <label>Objetivo <input name="objetivo" required></label>
      <div><button class="boton boton--principal">Crear misión</button></div></form>` : "";
  const cerrar = estado.perfil === "supervisor" && abierta ? `<form class="acciones" data-accion="cerrar" data-emergencia="${e.id}">
      <button class="boton boton--principal">Cerrar emergencia</button>
      <span class="dato">Requiere todas las misiones concluidas y al menos una satisfactoria.</span></form>` : "";

  return `<button class="boton volver" data-ir="emergencias">← Volver a emergencias</button>
    <h2>${esc(nombre(e.tipo))} · ${esc(e.ubicacion.direccion)}, ${esc(e.ubicacion.localidad)}</h2>
    <p>${etiquetaGravedad(e.gravedad)} ${etiquetaEstado(e.estado)} <span class="dato">Aceptada ${fecha(e.creada_en)} · aviso de ${esc(e.reportante_id)}</span></p>
    ${cerrar}
    <section class="seccion"><h3>Misiones</h3>
      ${e.misiones.length ? `<table class="tabla"><thead><tr><th>Misión</th><th>Estado</th><th>Unidad</th><th>Novedades / resultado</th><th></th></tr></thead><tbody>${misiones}</tbody></table>` : vacio("Todavía no hay misiones.")}
    </section>
    ${crear}
    <section class="seccion"><h3>Historial</h3>${bloqueHistorial(e.registros)}</section>`;
}

// ── Jefe de unidad (§2.3) ─────────────────────────────────────

async function vistaMisMisiones() {
  const misiones = await api("GET", "/misiones/mias");
  const tarjetas = misiones.reverse().map((m) => {
    const ruta = `data-id="${m.id}" data-emergencia="${m.emergencia_id}"`;
    let acciones = "";
    if (m.estado === "asignada") acciones = `<form data-accion="iniciar" ${ruta}><button class="boton boton--principal">Iniciar misión</button></form>
      <form data-accion="rechazar" ${ruta}><label>Justificación <input name="justificacion"></label><button class="boton boton--peligro">Rechazar</button></form>`;
    if (m.estado === "en_ejecucion") acciones = `<form data-accion="novedad" ${ruta}><label>Novedad <input name="texto" required></label><button class="boton">Registrar</button></form>
      <form data-accion="finalizar" ${ruta}><label>Resultado <select name="resultado">${opciones(["satisfactorio", "no_satisfactorio"])}</select></label>
        <label>Tareas realizadas <input name="tareas" required></label><button class="boton boton--principal">Finalizar</button></form>`;
    return `<article class="tarjeta"><div class="tarjeta__cabeza">
        <span class="tarjeta__titulo">${esc(nombre(m.tipo))}${m.cantidad_personas ? ` · ${m.cantidad_personas} personas` : ""}</span> ${etiquetaEstado(m.estado)}
        <span class="dato">${esc(nombre(m.tipo_situacion))} en ${esc(m.ubicacion.direccion)}, ${esc(m.ubicacion.localidad)} · unidad ${esc(m.unidad_id)}</span></div>
      <p><strong>Objetivo:</strong> ${esc(m.objetivo)}</p>
      ${m.novedades.length ? `<ul>${m.novedades.map((n) => `<li>${esc(n.texto)} <span class="dato">(${fecha(n.fecha_hora)})</span></li>`).join("")}</ul>` : ""}
      ${m.resultado ? `<p><strong>Resultado:</strong> ${esc(nombre(m.resultado.resultado))} · ${esc(m.resultado.tareas)}</p>` : ""}
      <div class="acciones">${acciones}</div></article>`;
  });
  return `<h2>Misiones de mi unidad</h2><p class="intro">Iniciá las misiones asignadas o rechazalas con una justificación antes de empezar. Durante la ejecución registrá novedades y al terminar, el resultado.</p>
    <div class="lista">${tarjetas.join("") || vacio("Tu unidad no tiene misiones asignadas.")}</div>`;
}

// ── Recursos (§2.4) y consultas de unidades ───────────────────

async function vistaUnidades() {
  const responsable = estado.perfil === "responsable_recursos";
  const unidades = await api("GET", "/unidades");
  const tarjetas = unidades.map((u) => {
    const libre = !u.mision_comprometida_id;
    const gestion = responsable ? `<details class="gestion"><summary>Administrar unidad</summary><div class="acciones">
        <form data-accion="condicion" data-id="${u.id}"><label>Condición <select name="condicion">${opciones(CONDICIONES, u.condicion)}</select></label><button class="boton boton--chico">Cambiar</button></form>
        <form data-accion="vehiculoCondicion" data-id="${u.id}"><label>Vehículo <select name="condicion">${opciones(["operativo", "fuera_de_servicio"], u.vehiculo.condicion)}</select></label><button class="boton boton--chico">Cambiar</button></form>
        <form data-accion="incorporar" data-id="${u.id}"><label>Id <input name="pid" required size="8"></label><label>Nombre <input name="pnombre" required size="10"></label>
          <label>Competencia <select name="competencia">${opciones(COMPETENCIAS)}</select></label><button class="boton boton--chico">Incorporar persona</button></form>
      </div></details>` : "";
    const quitar = (p) => responsable && p.id !== u.jefe_id ? ` <form style="display:inline" data-accion="retirar" data-id="${u.id}" data-persona="${p.id}"><button class="boton boton--peligro boton--chico" title="Retirar">Retirar</button></form>` : "";
    const equipo = (e) => `${esc(nombre(e.categoria))} ${esc(e.id)} (${esc(nombre(e.condicion))})${responsable ? ` <form style="display:inline" data-accion="equipoCondicion" data-id="${u.id}" data-equipo="${e.id}" data-condicion="${e.condicion === "operativo" ? "fuera_de_servicio" : "operativo"}"><button class="boton boton--chico">${e.condicion === "operativo" ? "Dar de baja" : "Habilitar"}</button></form>` : ""}`;
    return `<article class="tarjeta"><div class="tarjeta__cabeza"><span class="tarjeta__titulo">${esc(u.id)}</span>
        ${etiquetaEstado(u.condicion)} <span class="etiqueta ${libre ? "" : "etiqueta--activo"}">${libre ? "Disponible" : "Comprometida con la misión " + esc(corto(u.mision_comprometida_id))}</span>
        <span class="dato">Base ${esc(u.base_id)} · jefe ${esc(u.jefe_id)}</span></div>
      <p class="dato"><strong>Vehículo:</strong> ${esc(nombre(u.vehiculo.categoria))} ${esc(u.vehiculo.id)} (${esc(nombre(u.vehiculo.condicion))})${u.vehiculo.capacidad_evacuados ? ` · capacidad ${u.vehiculo.capacidad_evacuados}` : ""}</p>
      <p class="dato"><strong>Dotación:</strong></p><ul class="dotacion">${u.personal.map((p) => `<li>${esc(p.nombre)} (${esc(p.id)}) · ${esc(p.competencias.map(nombre).join(", "))}${p.id === u.jefe_id ? " · <strong>jefe</strong>" : ""}${quitar(p)}</li>`).join("")}</ul>
      <p class="dato"><strong>Equipamiento:</strong> ${u.equipamiento.map(equipo).join(" · ") || "ninguno"}</p>
      ${gestion}
      <details><summary class="dato">Historial de la unidad</summary>${bloqueHistorial(u.registros)}</details></article>`;
  });
  const intro = responsable ? "Una unidad comprometida con una misión no puede modificarse hasta que se libere." : "Composición, condición y disponibilidad de cada unidad.";
  return `<h2>Unidades</h2><p class="intro">${intro}</p><div class="lista">${tarjetas.join("") || vacio("No hay unidades.")}</div>`;
}

async function vistaNuevaUnidad() {
  const bases = await api("GET", "/bases");
  const persona = (n) => `<div class="fila"><label>Id <input name="p${n}_id"></label><label>Nombre <input name="p${n}_nombre"></label>
      <label>Competencia <select name="p${n}_comp">${opciones(COMPETENCIAS)}</select></label></div>`;
  return `<h2>Nueva unidad</h2><p class="intro">Una persona, un vehículo o un equipo no pueden integrar dos unidades a la vez.</p>
    <form class="formulario" data-accion="nuevaUnidad">
      <div class="fila"><label>Id de la unidad <input name="id" required></label><label>Base <select name="base_id">${bases.map((b) => `<option value="${b.id}">${esc(b.nombre)}</option>`).join("")}</select></label></div>
      <fieldset><legend>Jefe</legend><div class="fila"><label>Id (usuario) <input name="jefe_id" required></label><label>Nombre <input name="jefe_nombre" required></label></div>
        <div class="casillas">${COMPETENCIAS.map((c) => `<label><input type="checkbox" name="competencias" value="${c}"> ${nombre(c)}</label>`).join("")}</div></fieldset>
      <fieldset><legend>Resto de la dotación (opcional)</legend>${persona(1)}${persona(2)}</fieldset>
      <fieldset><legend>Vehículo</legend><div class="fila"><label>Id <input name="vehiculo_id" required></label>
        <label>Categoría <select name="vehiculo_categoria">${opciones(CATEGORIAS_VEHICULO)}</select></label>
        <label>Capacidad <input name="capacidad" type="number" min="1" placeholder="Solo transporte"></label></div></fieldset>
      <fieldset><legend>Equipo (opcional)</legend><div class="fila"><label>Id <input name="equipo_id"></label>
        <label>Categoría <select name="equipo_categoria">${opciones(CATEGORIAS_EQUIPO)}</select></label></div></fieldset>
      <div><button class="boton boton--principal">Registrar unidad</button></div>
    </form>`;
}

async function vistaBases() {
  const bases = await api("GET", "/bases");
  return `<h2>Bases operativas</h2>
    <table class="tabla"><thead><tr><th>Id</th><th>Nombre</th><th>Ubicación</th></tr></thead>
      <tbody>${bases.map((b) => `<tr><td>${esc(b.id)}</td><td>${esc(b.nombre)}</td><td>${esc(b.ubicacion.direccion)}, ${esc(b.ubicacion.localidad)}</td></tr>`).join("")}</tbody></table>
    <form class="formulario seccion" data-accion="nuevaBase"><h3>Nueva base</h3>
      <div class="fila"><label>Id <input name="id" required></label><label>Nombre <input name="nombre" required></label></div>
      <div class="fila"><label>Dirección <input name="direccion" required></label><label>Localidad <input name="localidad" required value="Ushuaia"></label></div>
      <div><button class="boton boton--principal">Registrar base</button></div></form>`;
}

// ── Supervisor (§2.5) ─────────────────────────────────────────

async function vistaTodosLosAvisos() {
  const avisos = await api("GET", "/avisos");
  return `<h2>Avisos</h2><p class="intro">Todos los avisos con su evaluación e historial.</p>
    <div class="lista">${avisos.reverse().map((a) => `<article class="tarjeta">${cabezaAviso(a)}
      <details><summary class="dato">Historial del aviso</summary>${bloqueHistorial(a.registros)}</details></article>`).join("") || vacio("No hay avisos.")}</div>`;
}

// ── Acciones de los formularios ───────────────────────────────

const rutaMision = (d) => `/emergencias/${d.emergencia}/misiones/${d.id}`;
const ACCIONES = {
  nuevoAviso: { exito: "Aviso registrado. Queda pendiente de evaluación.", hacer: async (_, f) => {
    await api("POST", "/avisos", { ubicacion: { direccion: f.direccion, localidad: f.localidad }, tipo: f.tipo, gravedad_estimada: f.gravedad, descripcion: f.descripcion });
    estado.vista = { vista: vistaMisAvisos, argumentos: [] };
    marcarMenu(vistaMisAvisos);
  } },
  nota: { exito: "Nota agregada.", hacer: (d, f) => api("POST", `/avisos/${d.id}/notas`, { texto: f.texto }) },
  aceptar: { exito: "Aviso aceptado: se originó la emergencia.", hacer: (d, f) => api("POST", `/avisos/${d.id}/aceptacion`, { tipo: f.tipo, gravedad: f.gravedad }) },
  descartar: { exito: "Aviso descartado.", hacer: (d, f) => api("POST", `/avisos/${d.id}/descarte`, { justificacion: f.justificacion }) },
  crearMision: { exito: "Misión creada.", hacer: (d, f) => api("POST", `/emergencias/${d.emergencia}/misiones`,
    { tipo: f.tipo, objetivo: f.objetivo, cantidad_personas: f.cantidad_personas ? Number(f.cantidad_personas) : null }) },
  asignar: { exito: "Unidad asignada.", hacer: (d, f) => api("POST", `${rutaMision(d)}/asignacion`, { unidad_id: f.unidad_id }) },
  reasignar: { exito: "Misión reasignada.", hacer: (d, f) => api("PUT", `${rutaMision(d)}/asignacion`, { unidad_id: f.unidad_id }) },
  cancelar: { exito: "Misión cancelada.", hacer: (d) => api("POST", `${rutaMision(d)}/cancelacion`) },
  cerrar: { exito: "Emergencia cerrada.", hacer: (d) => api("POST", `/emergencias/${d.emergencia}/cierre`) },
  iniciar: { exito: "Misión iniciada.", hacer: (d) => api("POST", `${rutaMision(d)}/inicio`) },
  rechazar: { exito: "Misión rechazada: vuelve a quedar pendiente.", hacer: (d, f) => api("POST", `${rutaMision(d)}/rechazo`, { justificacion: f.justificacion }) },
  novedad: { exito: "Novedad registrada.", hacer: (d, f) => api("POST", `${rutaMision(d)}/novedades`, { texto: f.texto }) },
  finalizar: { exito: "Misión finalizada.", hacer: (d, f) => api("POST", `${rutaMision(d)}/finalizacion`, { resultado: f.resultado, tareas: f.tareas }) },
  condicion: { exito: "Condición de servicio actualizada.", hacer: (d, f) => api("PUT", `/unidades/${d.id}/condicion`, { condicion: f.condicion }) },
  vehiculoCondicion: { exito: "Condición del vehículo actualizada.", hacer: (d, f) => api("PUT", `/unidades/${d.id}/vehiculo/condicion`, { condicion: f.condicion }) },
  equipoCondicion: { exito: "Condición del equipo actualizada.", hacer: (d) => api("PUT", `/unidades/${d.id}/equipamiento/${d.equipo}/condicion`, { condicion: d.condicion }) },
  incorporar: { exito: "Persona incorporada.", hacer: (d, f) => api("POST", `/unidades/${d.id}/personal`, { id: f.pid, nombre: f.pnombre, competencias: [f.competencia] }) },
  retirar: { exito: "Persona retirada.", hacer: (d) => api("DELETE", `/unidades/${d.id}/personal/${d.persona}`) },
  nuevaBase: { exito: "Base registrada.", hacer: (_, f) => api("POST", "/bases", { id: f.id, nombre: f.nombre, ubicacion: { direccion: f.direccion, localidad: f.localidad } }) },
  nuevaUnidad: { exito: "Unidad registrada.", hacer: (_, f) => {
    const personal = [1, 2].filter((n) => f[`p${n}_id`]).map((n) => ({ id: f[`p${n}_id`], nombre: f[`p${n}_nombre`] || f[`p${n}_id`], competencias: [f[`p${n}_comp`]] }));
    return api("POST", "/unidades", {
      id: f.id, base_id: f.base_id, personal,
      jefe: { id: f.jefe_id, nombre: f.jefe_nombre, competencias: f.competencias },
      vehiculo: { id: f.vehiculo_id, categoria: f.vehiculo_categoria, capacidad_evacuados: f.capacidad ? Number(f.capacidad) : null },
      equipamiento: f.equipo_id ? [{ id: f.equipo_id, categoria: f.equipo_categoria }] : [],
    });
  } },
};

// ── Menú de cada perfil ───────────────────────────────────────

const VISTAS = {
  reportante: [["Mis avisos", vistaMisAvisos], ["Nuevo aviso", vistaNuevoAviso]],
  operador: [["Avisos pendientes", vistaPendientes], ["Emergencias", vistaEmergencias], ["Unidades", vistaUnidades]],
  jefe_unidad: [["Misiones de mi unidad", vistaMisMisiones]],
  responsable_recursos: [["Unidades", vistaUnidades], ["Nueva unidad", vistaNuevaUnidad], ["Bases", vistaBases]],
  supervisor: [["Emergencias", vistaEmergencias], ["Avisos", vistaTodosLosAvisos], ["Unidades", vistaUnidades]],
};
const VISTA_POR_NOMBRE = { emergencias: vistaEmergencias, detalleEmergencia: vistaDetalleEmergencia };

// ── Arranque ──────────────────────────────────────────────────

async function arrancar() {
  estado.config = await (await fetch("/configuracion")).json();
  $("#form-ingreso").addEventListener("submit", async (e) => {
    e.preventDefault();
    const datos = new FormData(e.target);
    try {
      await iniciarSesion(datos.get("usuario"), datos.get("clave"));
      e.target.reset();
      abrirAplicacion();
    } catch (error) {
      const caja = $("#error-ingreso");
      caja.textContent = error.message;
      caja.hidden = false;
    }
  });
  $("#boton-salir").addEventListener("click", () => cerrarSesion());
  const guardado = sessionStorage.getItem("crce-token");
  if (guardado && datosDelToken(guardado).exp * 1000 > Date.now()) {
    const datos = datosDelToken(guardado);
    Object.assign(estado, { token: guardado, usuario: datos.preferred_username,
      perfil: (datos.realm_access?.roles ?? []).find((r) => r in VISTAS) });
    abrirAplicacion();
  } else {
    cerrarSesion();
  }
}

arrancar();
