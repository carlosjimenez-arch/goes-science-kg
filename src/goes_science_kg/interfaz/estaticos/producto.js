import {
  $,
  api,
  descargar,
  DISCIPLINAS,
  enlaceSeguro,
  esc,
  estado,
  guardar,
  icono,
  numero,
  parametros,
  ROLES,
} from '/app/cliente.js';
import { montarGrafo } from '/app/grafo.js';

const VISTAS = {
  inicio: {
    nombre: 'Inicio',
    grupo: 'General',
    icono: 'spark',
    color: 'indigo',
    sub: 'Cómo funciona el proceso',
  },
  panel: {
    nombre: 'Monitoreo nacional',
    grupo: 'Monitoreo',
    icono: 'panel',
    color: 'navy',
    sub: 'Estado del producto curricular',
  },
  corpus: {
    nombre: 'Corpus',
    grupo: 'M2 · Corpus y Grafo',
    icono: 'corpus',
    color: 'blue',
    sub: 'Fuentes del producto de Ciencias',
  },
  grafo: {
    nombre: 'Grafo 3D',
    grupo: 'M2 · Corpus y Grafo',
    icono: 'graph',
    color: 'indigo',
    sub: 'Relaciones publicadas y trazables',
  },
  revision: {
    nombre: 'Revisión de conocimiento',
    grupo: 'M3 · Validación',
    icono: 'know',
    color: 'teal',
    sub: 'Dictámenes reales por unidad',
  },
  curricularizacion: {
    nombre: 'Curricularización',
    grupo: 'M3 · Validación',
    icono: 'malla',
    color: 'green',
    sub: 'Original, propuesta y evidencia',
  },
  contenido: {
    nombre: 'Templates y Brief',
    grupo: 'M4 · Contenido',
    icono: 'content',
    color: 'purple',
    sub: 'De la propuesta al brief documental',
  },
  admin: {
    nombre: 'Administración',
    grupo: 'Sistema',
    icono: 'admin',
    color: 'rose',
    sub: 'Publicación y operación verificable',
  },
};
const S = {
  ruta: 'inicio',
  resumen: null,
  filtros: { grado: '', disciplina: '', q: '' },
  offset: 0,
  tipoFuente: '',
  soloAlertas: false,
  formato: 'evaluacion',
  seleccion: new Set(),
  briefs: [],
  epoch: 0,
  desmontar: null,
  datosVista: null,
  prevFocus: null,
};
const stat = (n, label, acento = false) =>
  `<div class="stat ${acento ? 'acc' : ''}"><b>${typeof n === 'number' ? numero(n) : esc(n)}</b><span>${esc(label)}</span></div>`;
const ir = (ruta, label, clase = 'btn') =>
  `<button class="${clase}" data-action="go" data-r="${ruta}">${label}</button>`;
const bloque = (titulo, contenido) =>
  `<section class="card"><h3 class="h3">${titulo}</h3>${contenido}</section>`;
const vacio = (texto) => `<div class="empty">${esc(texto)}</div>`;
const aviso = (texto) => `<div class="notice">${esc(texto)}</div>`;
const titulo = (t, sub, accion = '') =>
  `<div class="between section-head"><div><h2 class="h2">${t}</h2><p class="lead">${sub}</p></div>${accion}</div>`;
const csvBtn = `<button class="btn" data-action="csv">${icono('dl')}Exportar CSV</button>`;
const excelBtn = `<button class="btn pri" data-action="excel">${icono('dl')}Descargar Excel</button>`;
let toastTimer;
function toast(texto) {
  $('toastm').textContent = texto;
  $('toast').classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('toast').classList.remove('show'), 3500);
}
function filtros({ corpus = false } = {}) {
  const grados = S.resumen.grados
    .map(
      (g) =>
        `<option value="${g.grado}" ${String(g.grado) === S.filtros.grado ? 'selected' : ''}>${g.grado}.º grado</option>`,
    )
    .join('');
  return `<form class="filters" id="filtros">${
    corpus
      ? `<select class="input" name="tipo" aria-label="Tipo de fuente"><option value="">Todas las fuentes</option><option value="curriculo" ${S.tipoFuente === 'curriculo' ? 'selected' : ''}>Currículo nacional</option><option value="referencia" ${S.tipoFuente === 'referencia' ? 'selected' : ''}>Referencias</option></select>`
      : `<select class="input" name="grado" aria-label="Grado"><option value="">Todos los grados</option>${grados}</select><select class="input" name="disciplina" aria-label="Disciplina"><option value="">Todas las ciencias</option>${S.resumen.disciplinas.map((d) => `<option value="${esc(d)}" ${S.filtros.disciplina === d ? 'selected' : ''}>${esc(DISCIPLINAS[d] || d)}</option>`).join('')}</select>`
  }
    <div class="search">${icono('search')}<input name="q" aria-label="Buscar" placeholder="${corpus ? 'Buscar una fuente…' : 'Buscar objetivos o unidades…'}" value="${esc(S.filtros.q)}"><button type="submit">Buscar</button></div>
    ${S.filtros.q || S.filtros.grado || S.filtros.disciplina ? '<button type="button" class="btn sm" data-action="limpiar">Limpiar</button>' : ''}</form>`;
}
function paginador(d) {
  return `<div class="pager"><span>${d.total ? numero(d.offset + 1) : 0}–${numero(Math.min(d.offset + d.limite, d.total))} de ${numero(d.total)}</span><div><button class="btn sm" data-action="anterior" ${d.offset === 0 ? 'disabled' : ''}>Anterior</button><button class="btn sm" data-action="siguiente" ${d.offset + d.limite >= d.total ? 'disabled' : ''}>Siguiente</button></div></div>`;
}
function barras(filas, color = 'var(--acc)') {
  const max = Math.max(1, ...filas.map((f) => f[1]));
  return `<div class="bars">${filas.map(([label, n]) => `<div class="bar"><span class="bn" title="${esc(label)}">${esc(label)}</span><div class="btr"><div class="bf" style="width:${(n / max) * 100}%;background:${color}"></div></div><span class="bv">${numero(n)}</span></div>`).join('')}</div>`;
}
function shell() {
  let ultimo = '';
  $('nav').innerHTML = Object.entries(VISTAS)
    .map(([ruta, v]) => {
      const grupo = ultimo !== v.grupo ? `<div class="navgroup">${v.grupo}</div>` : '';
      ultimo = v.grupo;
      return `${grupo}<button class="navitem ${S.ruta === ruta ? 'on' : ''}" data-action="go" data-r="${ruta}" style="--i:var(--${v.color});--i-100:var(--${v.color === 'navy' ? 'navy-50' : v.color + '-100'})" title="${v.nombre}" ${S.ruta === ruta ? 'aria-current="page"' : ''}>${icono(v.icono)}<span class="lbl">${v.nombre}</span></button>`;
    })
    .join('');
  const v = VISTAS[S.ruta];
  document.documentElement.style.setProperty('--acc', `var(--${v.color})`);
  document.documentElement.style.setProperty(
    '--acc-100',
    `var(--${v.color === 'navy' ? 'navy-50' : v.color + '-100'})`,
  );
  $('title').textContent = v.nombre;
  $('crumb').textContent = 'GOES · ' + v.sub;
  $('miniic').innerHTML = icono(v.icono);
  $('vg').textContent = numero(S.resumen.nodos);
  $('vr').textContent = numero(S.resumen.cobertura.unidades);
  $('snapshot').textContent =
    `Ciencias V4 · Snapshot ${S.resumen.snapshot_id} · Revisión automática; aprobación institucional no acreditada`;
  document.title = `${v.nombre} · Ciencias · GOES`;
}
function inicio() {
  const r = S.resumen,
    c = r.cobertura;
  const pasos = [
    [
      'Repositorio',
      'corpus',
      'corpus',
      'blue',
      'Matrices nacionales y referencias primarias con localizadores.',
    ],
    ['Grafo', 'grafo', 'graph', 'indigo', 'Filas, unidades, fuentes, propuestas y sus relaciones tipadas.'],
    ['Revisión', 'revision', 'know', 'teal', 'Cuatro especialistas revisan el mismo texto y sus evidencias.'],
    [
      'Currícula',
      'curricularizacion',
      'malla',
      'green',
      'Compara el insumo original con cada propuesta respaldada.',
    ],
    [
      'Contenido',
      'contenido',
      'content',
      'purple',
      'Compila briefs de aula con evaluación, recursos y seguridad.',
    ],
  ];
  return `<div class="hero-in" style="padding:8px 0 4px"><span class="pill indigo" style="margin-bottom:12px;display:inline-block">Ciencias · El Salvador · V4</span><h2 style="font-weight:900;letter-spacing:-.04em;line-height:1.02;font-size:clamp(1.7rem,1.2rem + 2.4vw,2.8rem);color:var(--navy);margin:0 0 12px">De las fuentes a la clase,<br>en cinco movimientos</h2><p class="lead">Un solo recorrido para explorar las fuentes, comprender el grafo y llevar las propuestas de Ciencias a la planificación de clase. Cada resultado conserva sus evidencias y revisiones.</p></div>
    <div class="stats" style="margin:22px 0">${stat(c.unidades, 'unidades revisadas', true)}${stat(c.filas_respaldadas, 'propuestas de Ciencias')}${stat(r.nodos, 'nodos del grafo')}${stat(r.fuentes, 'fuentes documentadas')}</div>
    <div class="mvflow">${pasos.map((p, i) => `<button class="mvstep" data-action="go" data-r="${p[1]}" style="--mc:var(--${p[3]});text-align:left;border:1px solid var(--hair);font-family:var(--font)"><span class="mvnum">${i + 1}</span><span class="mvic">${icono(p[2])}</span><span class="mvk">${p[0]}</span><span class="mvd">${p[4]}</span><span class="mvgo">Abrir ${icono('arrow')}</span></button>`).join('')}</div>
    <div class="nextbar" style="border-left-color:var(--indigo)"><div class="txt"><b>Explora la entrega de Ciencias</b><span>${numero(c.filas)} filas originales · ${numero(c.filas_fuera_alcance_original)} fuera de alcance preservadas · 2.º a 11.º</span></div>${ir('corpus', 'Comenzar por el corpus ' + icono('arrow'), 'btn pri')}</div>${aviso('El respaldo de agentes es una revisión técnica automática. No equivale a cobertura PISA/ERCE, resultados de aprendizaje ni aprobación institucional.')}`;
}
function panel() {
  const r = S.resumen,
    c = r.cobertura;
  return `${titulo('Monitoreo nacional del currículo', 'Estado real de la entrega de Ciencias. Los conteos describen el producto; no miden aprendizaje.', csvBtn)}
    <div class="stats">${stat(c.unidades, 'unidades con revisión', true)}${stat(c.filas_respaldadas, 'propuestas de Ciencias')}${stat(c.filas, 'filas originales')}${stat(r.alertas_originales, 'filas originales con alerta')}</div>
    <div class="g2">${bloque(
      'Propuestas por grado',
      barras(
        r.grados.map((g) => [`${g.grado}.º grado`, g.propuestas_ciencias]),
        'var(--indigo)',
      ),
    )}${bloque('Composición del grafo', barras(Object.entries(r.tipos_nodo), 'var(--teal)'))}</div>
    <div class="g3 spaced">${bloque('Resultados de aula · LXP', '<span class="pill gray">Sin integración</span><p class="muted">No hay registros conectados de clases, escuelas o evaluaciones. No se muestran cifras simuladas.</p>')}${bloque('Monitoreo territorial', '<span class="pill gray">Sin datos</span><p class="muted">El grafo curricular no contiene métricas por departamento, municipio o centro educativo.</p>')}${bloque('Aprobación institucional', '<span class="pill amber">No acreditada</span><p class="muted">Los dictámenes automáticos están disponibles. No se convierten en una aprobación del MINED.</p>')}</div>
    <div class="card spaced"><h3 class="h3">Balance por grado</h3><div class="table-wrap"><table class="atable"><thead><tr><th>Grado</th><th>Unidades</th><th>Filas originales</th><th>Propuestas de Ciencias</th><th>Alertas del original</th></tr></thead><tbody>${r.grados.map((g) => `<tr><td>${g.grado}.º</td><td>${g.unidades}</td><td>${g.filas}</td><td>${g.propuestas_ciencias}</td><td>${g.alertas_originales}</td></tr>`).join('')}</tbody></table></div></div>`;
}
async function corpus() {
  const d = await api('/documentos' + parametros({ q: S.filtros.q, tipo: S.tipoFuente }));
  S.datosVista = d;
  return `${titulo('Corpus', 'Matrices y referencias utilizadas por el producto. Los originales conservan su identidad y procedencia.')}${filtros({ corpus: true })}
    <div class="between"><p class="muted">${numero(d.total)} fuentes documentadas en la selección</p><span class="pill blue">Fuentes del snapshot V4</span></div>
    <div class="list">${d.documentos.map((x) => `<article class="li"><span class="tile">${icono('corpus')}</span><div><div class="ti">${esc(x.titulo)}</div><div class="sub">${x.tipo === 'curriculo' ? 'Currículo nacional' : 'Referencia'} · ${esc(x.version_documental || 'Edición en expediente')} · citada en ${x.usos} unidades</div><div class="clip-id">SHA ${esc(x.sha256 || 'No registrado en esta proyección')}</div>${x.licencia ? `<div class="mini">${esc(x.licencia)}</div>` : ''}</div><div class="rt">${enlaceSeguro(x.url, 'Fuente oficial')}</div></article>`).join('') || vacio('No hay fuentes con estos filtros.')}</div>
    ${aviso('Este corpus es el que respalda la publicación seleccionada. Incorporar otro archivo requiere ingesta y verificación antes de que pueda respaldar el grafo.')}`;
}
async function grafo() {
  const d = await api('/grafo' + parametros(S.filtros, { limite: 260 }));
  S.datosVista = d;
  return `${titulo('Grafo 3D de conocimiento', 'Explora las relaciones reales del producto: cada enlace conserva su tipo y su sentido documental.')}${filtros()}
    <div class="stats">${stat(S.resumen.nodos, 'nodos del snapshot', true)}${stat(S.resumen.aristas, 'relaciones del snapshot')}${stat(d.nodos.length, 'nodos visibles')}${stat(d.aristas.length, 'relaciones visibles')}</div>
    ${d.nodos.length ? `<div class="graph-stage"><canvas id="canvas-grafo" aria-label="Proyección tridimensional del subgrafo; alternativa accesible en la tabla inferior"></canvas><div class="graph-hover" id="graph-hover">Arrastra para rotar · selecciona un nodo</div><div class="graph-tools"><button class="btn sm" id="rotacion" aria-pressed="true">Pausar giro</button></div><div class="graph-legend"><span><i style="background:#3565fc"></i>Fila curricular</span><span><i style="background:#1c1e4d"></i>Unidad</span><span><i style="background:#0fae76"></i>Propuesta</span><span><i style="background:#0ea5a3"></i>Revisión</span><span><i style="background:#e0890b"></i>Fuente</span></div></div>` : vacio('No hay nodos con estos filtros.')}
    <p class="muted spaced">${d.recortado ? `Subgrafo de ${d.nodos.length} nodos sobre ${numero(d.total_nodos_filtrados)} relacionados con el filtro.` : 'Todos los nodos de la selección están visibles.'} La posición 3D es visual; las aristas no representan automáticamente prerrequisitos.</p>
    <details class="card spaced"><summary>Ver nodos en tabla accesible · ${d.nodos.length}</summary><div class="table-wrap"><table class="atable"><thead><tr><th>Nodo</th><th>Tipo</th><th>Conexiones</th><th></th></tr></thead><tbody>${d.nodos.map((n) => `<tr><td class="objetivo">${esc(n.etiqueta)}</td><td>${esc(n.tipo)}</td><td>${n.conexiones}</td><td><button class="btn sm" data-action="nodo" data-id="${esc(n.id)}">Detalle</button></td></tr>`).join('')}</tbody></table></div></details>`;
}
function dots(revisiones) {
  return `<div class="dots">${Object.entries(ROLES)
    .map(([rol, nombre]) => {
      const d = revisiones.find((x) => x.rol === rol),
        valores = d?.lectura ? Object.values(d.lectura.criterios) : [];
      const ok = d && !d.error && valores.length && valores.every((v) => v === 'si');
      return `<span class="role-dot ${ok ? '' : d ? 'fail' : 'unknown'}" title="${nombre}: ${ok ? 'criterios satisfechos' : d ? 'revisar dictamen' : 'sin dictamen'}">${nombre[0]}</span>`;
    })
    .join('')}</div>`;
}
async function revision() {
  const d = await api('/revision' + parametros(S.filtros));
  S.datosVista = d;
  const columnas = [
    ['respaldado_automaticamente', 'Respaldo automático', 'green'],
    ['abstencion', 'Abstención', 'amber'],
    ['no_respaldado', 'Sin respaldo', 'red'],
  ];
  return `${titulo('Revisión de conocimiento', 'Dictámenes reales por unidad: ciencia, currículo, psicopedagogía y revisión adversarial.')}${filtros()}
    <div class="review-board">${columnas
      .map(([key, label, color]) => {
        const unidades = d.unidades.filter((u) => u.estado === key);
        return `<section class="review-column"><div class="between"><h3>${label}</h3><span class="pill ${color}">${unidades.length}</span></div>${unidades.map((u) => `<button class="review-item" data-action="unidad" data-id="${u.id}"><span class="mini">${u.grado}.º · ${esc(u.asignatura_malla)}</span><strong>${esc(u.unidad)}</strong><span class="mini">${u.filas} filas · ${u.rondas} ronda${u.rondas === 1 ? '' : 's'}</span>${dots(u.dictamenes)}</button>`).join('') || vacio('No hay unidades en este estado.')}</section>`;
      })
      .join('')}</div>
    ${aviso('Se muestran los resultados seleccionados y sus rondas reales. El expediente completo conserva los protocolos anteriores. Los especialistas que comparten proveedor no son estadísticamente independientes.')}`;
}
function tablaFilas(d, { checks = false } = {}) {
  return `<div class="table-wrap"><table class="atable"><thead><tr>${checks ? '<th>Elegir</th>' : ''}<th>Grado</th><th>Asignatura y unidad</th><th>Objetivo original</th><th>Propuesta</th><th></th></tr></thead><tbody>${d.filas.map((f) => `<tr>${checks ? `<td><input type="checkbox" class="seleccionar-fila" data-id="${esc(f.id)}" aria-label="Elegir ${esc(f.objetivo_original)}" ${S.seleccion.has(f.id) ? 'checked' : ''} ${f.fuera_alcance || !f.objetivo_propuesto ? 'disabled' : ''}></td>` : ''}<td>${f.grado}.º</td><td>${esc(f.asignatura)}<div class="mini">${esc(f.unidad)}</div></td><td class="objetivo">${esc(f.objetivo_original)}${f.alerta_original ? '<div class="spaced"><span class="pill amber">Alerta del original</span></div>' : ''}</td><td class="objetivo">${f.fuera_alcance ? '<span class="pill gray">Fuera de Ciencias</span>' : esc(f.objetivo_propuesto || 'Sin propuesta respaldada')}</td><td><button class="btn sm" data-action="fila" data-id="${esc(f.id)}">Comparar</button></td></tr>`).join('')}</tbody></table></div>${!d.filas.length ? vacio('No hay filas con estos filtros.') : ''}${paginador(d)}`;
}
async function curricularizacion() {
  const d = await api(
    '/filas' + parametros(S.filtros, { offset: S.offset, limite: 25, solo_alertas: S.soloAlertas }),
  );
  S.datosVista = d;
  return `${titulo('Curricularización', 'Compara cada fila original con su propuesta: objetivos, indicadores, evaluación y didáctica.', excelBtn)}${filtros()}
    <div class="between"><div class="tabs"><button data-action="alertas" data-value="false" class="${!S.soloAlertas ? 'on' : ''}">Toda la malla</button><button data-action="alertas" data-value="true" class="${S.soloAlertas ? 'on' : ''}">Alertas del original · ${S.resumen.alertas_originales}</button></div>${csvBtn}</div>
    <section class="card spaced">${tablaFilas(d)}</section>${aviso('El orden es el de las filas del insumo. No se convierte en un calendario de 160 días: el grafo no contiene una carga lectiva oficial validada. Las propuestas corregidas conservan la alerta del original.')}`;
}
async function contenido() {
  const d = await api('/filas' + parametros(S.filtros, { offset: S.offset, limite: 20 }));
  S.datosVista = d;
  return `${titulo('Templates y Brief', 'Organiza propuestas respaldadas en un brief trazable para preparar clases.')}
    <h3 class="h3">1 · Formato de organización</h3><div class="template-options"><label class="template-option"><input name="formato" type="radio" value="evaluacion" ${S.formato === 'evaluacion' ? 'checked' : ''}><b>Diseño por evidencias</b><p>Objetivo, indicador, producto y criterio de evaluación; didáctica, andamiaje, contexto y seguridad.</p></label><label class="template-option"><input name="formato" type="radio" value="cinco_fases" ${S.formato === 'cinco_fases' ? 'checked' : ''}><b>Cinco fases del insumo</b><p>Añade las fases originales: aproximar, explorar, explicar, indagar y reforzar. Las ausencias se indican.</p></label></div>
    <h3 class="h3 spaced">2 · Selecciona objetivos de Ciencias</h3>${filtros()}<div class="between"><p class="muted" id="seleccion-label">${S.seleccion.size} objetivos elegidos · máximo 20</p><button class="btn pri" data-action="briefs" id="compilar-briefs" ${!S.seleccion.size ? 'disabled' : ''}>${icono('content')}Compilar briefs</button></div><section class="card spaced">${tablaFilas(d, { checks: true })}</section>
    <div id="briefs-resultados">${resultadosBriefs()}</div>${aviso('El brief se compila a partir del texto ya respaldado. No genera otra clase con IA ni consume Vertex; conserva las condiciones de recursos y los límites de la propuesta.')}`;
}
function resultadosBriefs() {
  return S.briefs.length
    ? `<h3 class="h3 spaced">3 · Briefs compilados · ${S.briefs.length}</h3><div class="grid">${S.briefs.map((b, i) => `<section class="card"><div class="between"><strong>${esc(b.titulo)}</strong><button class="btn sm" data-action="brief-descarga" data-i="${i}">${icono('dl')}Markdown</button></div><details class="spaced"><summary>Leer brief documental</summary><pre class="source-text">${esc(b.markdown)}</pre></details></section>`).join('')}</div>`
    : '';
}
async function admin() {
  const d = await api('/administracion');
  S.datosVista = d;
  const a = d.actividad_vertex;
  return `${titulo('Administración', 'Estado de publicación, permisos de la aplicación y actividad registrada.')}
    <div class="stats">${stat('Lectura', 'modo de la aplicación', true)}${stat(Object.keys(d.archivos_snapshot).length, 'archivos del snapshot')}${stat(a ? a.llamadas : 'No disponible', 'invocaciones registradas')}${stat(4, 'roles de revisión')}</div>
    <div class="g2">${bloque('Identidad y permisos', '<span class="pill gray">Consulta local</span><p>No hay proveedor de identidad conectado. Esta sesión no acredita un usuario GOES ni permite gestionar usuarios o aprobar el currículo institucionalmente.</p><div class="checks"><span class="pill green">Lectura</span><span class="pill gray">Sin generación de modelos</span></div>')}
    ${bloque('Integridad de la publicación', `<p>Las consultas comparten un único snapshot verificado. Si sus archivos cambian, la API se invalida hasta reiniciar el servicio.</p><div class="clip-id">${esc(d.snapshot_id)}</div><p><a href="/docs" target="_blank" rel="noopener">Abrir contrato OpenAPI ↗</a></p>`)}</div>
    <div class="card spaced"><h3 class="h3">Actividad de Vertex · campaña curricular V4</h3>${a ? `<p class="muted">${a.llamadas} invocaciones registradas · USD ${a.reserva_usd.toFixed(6)} de reserva conservadora. El importe facturado no está disponible. Consultar esta pantalla no consume modelos.</p><div class="table-wrap"><table class="atable"><thead><tr><th>Modelo</th><th>Rol</th><th>Estado</th><th>Invocaciones</th></tr></thead><tbody>${a.detalle.map((x) => `<tr><td>${esc(x.modelo)}</td><td>${esc(ROLES[x.rol] || x.rol)}</td><td>${esc(x.estado)}</td><td>${x.llamadas}</td></tr>`).join('')}</tbody></table></div>` : vacio('No hay un ledger disponible para consultar. No se supone un gasto de cero.')}</div>
    <details class="card spaced"><summary>Huellas de los archivos publicados</summary>${Object.entries(
      d.archivos_snapshot,
    )
      .map(([n, h]) => `<p><b>${esc(n)}</b><br><span class="clip-id">${esc(h)}</span></p>`)
      .join('')}</details>`;
}
const RENDER = { inicio, panel, corpus, grafo, revision, curricularizacion, contenido, admin };
async function render() {
  const epoch = ++S.epoch;
  S.desmontar?.();
  S.desmontar = null;
  shell();
  $('view').setAttribute('aria-busy', 'true');
  $('view').classList.add('loading');
  try {
    const html = await RENDER[S.ruta]();
    if (epoch !== S.epoch) return;
    $('view').innerHTML = html;
    $('view').classList.add('vin');
    if (S.ruta === 'grafo' && $('canvas-grafo'))
      S.desmontar = montarGrafo($('canvas-grafo'), S.datosVista, abrirNodo);
  } catch (e) {
    if (epoch !== S.epoch) return;
    $('view').innerHTML =
      `<section class="card error-card"><h2 class="h2">No se pudo cargar esta vista</h2><p>${esc(e.message)}</p><button class="btn" data-action="reintentar">Reintentar consulta</button></section>`;
  } finally {
    if (epoch === S.epoch) {
      $('view').setAttribute('aria-busy', 'false');
      $('view').classList.remove('loading');
    }
  }
}
function navegar(ruta) {
  if (!VISTAS[ruta]) return;
  cerrarModal();
  $('side').classList.remove('open');
  S.offset = 0;
  S.soloAlertas = false;
  if (location.hash.slice(1) === ruta) {
    S.ruta = ruta;
    render();
  } else location.hash = ruta;
  $('scroll-view').scrollTop = 0;
}
let modalEpoch = 0;
function abrirModal(titulo, contenido) {
  S.prevFocus = document.activeElement;
  $('modal-title').textContent = titulo;
  $('modal-body').innerHTML = contenido;
  $('overlay').hidden = false;
  document.body.classList.add('body-detail-open');
  $('overlay').querySelector('button').focus();
}
function cerrarModal() {
  modalEpoch++;
  $('overlay').hidden = true;
  document.body.classList.remove('body-detail-open');
  if (S.prevFocus?.isConnected) S.prevFocus.focus();
  else $('view').focus();
}
function tablaDictamenes(revision) {
  return `<div class="table-wrap"><table class="atable"><thead><tr><th>Especialista</th><th>Criterios y decisión</th><th>Modelo</th></tr></thead><tbody>${revision.dictamenes
    .map(
      (d) =>
        `<tr><td>${esc(ROLES[d.rol] || d.rol)}</td><td>${
          d.lectura
            ? Object.entries(d.lectura.criterios)
                .map(([k, v]) => `<div class="mini">${esc(k.replaceAll('_', ' '))}: <b>${esc(v)}</b></div>`)
                .join('')
            : esc(d.error || 'Sin lectura')
        }<div class="mini">${esc((d.lectura?.hallazgos || []).join(' · '))}</div></td><td class="mini">${esc(d.modelo)}</td></tr>`,
    )
    .join('')}</tbody></table></div>`;
}
async function abrirFila(id) {
  const turno = ++modalEpoch;
  abrirModal('Comparación curricular', aviso('Cargando el expediente…'));
  try {
    const d = await api('/filas/' + encodeURIComponent(id));
    if (turno !== modalEpoch) return;
    const p = d.propuesta,
      o = d.original;
    $('modal-title').textContent = `${d.asignatura} · ${d.grado}.º · ${d.unidad}`;
    $('modal-body').innerHTML =
      `${estado(d.estado_revision)}<p class="mini">Original: ${esc(d.hoja)} · fila ${d.fila}</p>
      ${d.alerta_original ? `<div class="notice amber"><b>Alerta científica del original</b><br>${esc(d.alerta_original)}<br>El respaldo de la propuesta corregida no elimina esta alerta.</div>` : ''}
      <div class="diff-grid"><div><h3>Objetivo original</h3><p>${esc(d.objetivo_original)}</p></div><div><h3>${d.fuera_alcance ? 'Fuera de Ciencias' : 'Objetivo propuesto'}</h3><p>${esc(d.objetivo_propuesto || 'No hay propuesta respaldada')}</p></div></div>
      ${p ? ['indicador_observable', 'producto_evaluable', 'criterio_evaluacion', 'orientacion_didactica', 'andamiaje', 'contexto_salvador', 'seguridad', 'justificacion'].map((k) => `<h3>${esc({ contexto_salvador: 'Contexto salvadoreño propuesto' }[k] || k.replaceAll('_', ' '))}</h3><p>${esc(p[k])}</p>`).join('') + `<h3>Recursos condicionales</h3><p>${esc(p.recursos_condicionales.join(' · '))}</p>` : ''}
      <details><summary>Cinco fases originales</summary>${Object.entries(o.fases)
        .map(
          ([k, f]) =>
            `<h3>${esc(k)}</h3><p>${esc(f.presente_en_hoja ? f.texto : 'Ausente en el insumo')}</p>`,
        )
        .join('')}</details>
      <details><summary>Revisiones de la unidad · ${d.revisiones.rondas} rondas</summary>${tablaDictamenes(d.revisiones)}</details>
      <details><summary>Fuentes y fragmentos citados</summary>${d.fragmentos.map((f) => `<div class="notice"><b>${esc(f.id)}</b><p>${esc(f.literal)}</p><div class="clip-id">${esc(f.evidencia_id)}</div></div>`).join('')}${d.evidencias.map((e) => `<details><summary>${esc(e.fuente.documento)}</summary><p class="clip-id">${esc(e.fuente.sha256 || 'SHA en el expediente original')}</p>${enlaceSeguro(e.fuente.url, 'Documento oficial')}<pre class="source-text">${esc(e.texto)}</pre></details>`).join('')}</details>
      ${aviso(d.limite)}<p class="clip-id">Fila ${esc(d.id)}<br>Snapshot ${esc(d.snapshot_id)}</p>`;
  } catch (e) {
    if (turno === modalEpoch) $('modal-body').innerHTML = aviso(e.message);
  }
}
async function abrirUnidad(id) {
  const u = S.resumen.unidades.find((u) => u.id === id);
  if (!u) return;
  const turno = ++modalEpoch;
  abrirModal(`${u.asignatura_malla} · ${u.grado}.º · ${u.unidad}`, aviso('Cargando unidad…'));
  try {
    const d = await api('/filas' + parametros({ grado: u.grado, q: u.unidad, limite: 200 }));
    if (turno !== modalEpoch) return;
    const filas = d.filas.filter((f) => f.preparacion_id === id),
      rev = S.datosVista?.unidades?.find((x) => x.id === id);
    $('modal-body').innerHTML =
      `${estado(u.estado)}<p class="muted">${u.filas} filas originales · ${u.rondas} rondas en el protocolo seleccionado</p>${rev ? tablaDictamenes(rev) : ''}<div class="list spaced">${filas.map((f) => `<button class="review-item" data-action="fila" data-id="${esc(f.id)}"><strong>${esc(f.objetivo_original)}</strong><span class="mini">Comparar original y propuesta →</span></button>`).join('')}</div>${aviso(S.resumen.limite)}`;
  } catch (e) {
    if (turno === modalEpoch) $('modal-body').innerHTML = aviso(e.message);
  }
}
async function abrirNodo(id) {
  const turno = ++modalEpoch;
  abrirModal('Nodo del grafo', aviso('Cargando nodo…'));
  try {
    const d = await api('/nodos/' + encodeURIComponent(id));
    if (turno !== modalEpoch) return;
    if (d.fila) {
      await abrirFila(id);
      return;
    }
    $('modal-title').textContent = d.nodo.etiqueta;
    $('modal-body').innerHTML =
      `<span class="pill indigo">${esc(d.nodo.tipo)}</span><p class="clip-id">${esc(d.nodo.id)}</p><h3>Relaciones · ${d.relaciones.length}</h3>${d.relaciones.map((a) => `<div class="notice"><b>${esc(a.tipo)}</b><div class="clip-id">${esc(a.origen)} → ${esc(a.destino)}</div></div>`).join('')}<details><summary>Propiedades publicadas</summary><pre class="source-text">${esc(JSON.stringify(d.nodo.props, null, 2))}</pre></details>`;
  } catch (e) {
    if (turno === modalEpoch) $('modal-body').innerHTML = aviso(e.message);
  }
}
async function accion(e) {
  const target = e.target.closest('[data-action]');
  if (!target) return;
  const a = target.dataset.action;
  try {
    if (a === 'saltar') {
      e.preventDefault();
      $('view').focus();
    } else if (a === 'go') navegar(target.dataset.r);
    else if (a === 'collapse') {
      const on = $('app').classList.toggle('collapsed');
      target.setAttribute('aria-expanded', String(!on));
    } else if (a === 'menu') $('side').classList.toggle('open');
    else if (a === 'profile') {
      const on = $('pmenu').classList.toggle('show');
      target.setAttribute('aria-expanded', String(on));
    } else if (a === 'dark') {
      const dark = document.documentElement.classList.toggle('dark');
      try {
        localStorage.setItem('ciencias-tema', dark ? 'oscuro' : 'claro');
      } catch {}
      $('pmenu').classList.remove('show');
    } else if (a === 'closemodal') cerrarModal();
    else if (a === 'fila') await abrirFila(target.dataset.id);
    else if (a === 'unidad') await abrirUnidad(target.dataset.id);
    else if (a === 'nodo') await abrirNodo(target.dataset.id);
    else if (a === 'limpiar') {
      S.filtros = { grado: '', disciplina: '', q: '' };
      S.offset = 0;
      S.tipoFuente = '';
      await render();
    } else if (a === 'alertas') {
      S.soloAlertas = target.dataset.value === 'true';
      S.offset = 0;
      await render();
    } else if (a === 'anterior' || a === 'siguiente') {
      S.offset = Math.max(0, S.offset + (a === 'siguiente' ? S.datosVista.limite : -S.datosVista.limite));
      await render();
      $('scroll-view').scrollTop = 0;
    } else if (a === 'reintentar') await render();
    else if (a === 'csv' || a === 'excel') {
      target.disabled = true;
      try {
        await descargar(
          a === 'csv' ? '/api/v4/exportaciones/mejoras.csv' : '/api/v4/interfaz/exportaciones/matriz.xlsx',
          a === 'csv' ? 'ciencias-v4.csv' : 'ciencias-v4.xlsx',
        );
        toast('Exportación descargada');
      } finally {
        target.disabled = false;
      }
    } else if (a === 'briefs') {
      target.disabled = true;
      target.textContent = 'Compilando…';
      try {
        const d = await api('/briefs', {
          method: 'POST',
          body: JSON.stringify({ filas_ids: [...S.seleccion], formato: S.formato }),
        });
        S.briefs = d.briefs;
        $('briefs-resultados').innerHTML = resultadosBriefs();
        $('briefs-resultados').scrollIntoView({ behavior: 'smooth' });
        toast(`${d.briefs.length} briefs compilados · 0 llamadas a modelos`);
      } finally {
        target.disabled = !S.seleccion.size;
        target.innerHTML = icono('content') + 'Compilar briefs';
      }
    } else if (a === 'brief-descarga') {
      const b = S.briefs[Number(target.dataset.i)];
      if (b) guardar(b.markdown, `ciencias-${b.fila_id.slice(-12)}.md`, 'text/markdown;charset=utf-8');
    }
  } catch (error) {
    toast(error.message);
  }
}
document.addEventListener('click', accion);
document.addEventListener('submit', (e) => {
  if (e.target.id !== 'filtros') return;
  e.preventDefault();
  const f = new FormData(e.target);
  S.filtros.q = String(f.get('q') || '');
  S.offset = 0;
  render();
});
document.addEventListener('change', (e) => {
  if (e.target.closest('#filtros') && e.target.tagName === 'SELECT') {
    if (e.target.name === 'tipo') S.tipoFuente = e.target.value;
    else S.filtros[e.target.name] = e.target.value;
    S.offset = 0;
    render();
  } else if (e.target.name === 'formato') {
    S.formato = e.target.value;
    S.briefs = [];
    $('briefs-resultados').innerHTML = '';
  } else if (e.target.matches('.seleccionar-fila')) {
    const id = e.target.dataset.id;
    if (e.target.checked && S.seleccion.size >= 20) {
      e.target.checked = false;
      toast('Elige como máximo 20 objetivos por lote.');
      return;
    }
    if (e.target.checked) S.seleccion.add(id);
    else S.seleccion.delete(id);
    $('seleccion-label').textContent = `${S.seleccion.size} objetivos elegidos · máximo 20`;
    $('compilar-briefs').disabled = !S.seleccion.size;
  }
});
document.addEventListener('keydown', (e) => {
  if ($('overlay').hidden) return;
  if (e.key === 'Escape') cerrarModal();
  if (e.key === 'Tab') {
    const f = [...$('overlay').querySelectorAll('button,a[href],input,summary')].filter(
      (el) => el.getClientRects().length && !el.disabled,
    );
    if (!f.length) return;
    const first = f[0],
      last = f.at(-1);
    if (e.shiftKey && document.activeElement === first) {
      last.focus();
      e.preventDefault();
    } else if (!e.shiftKey && document.activeElement === last) {
      first.focus();
      e.preventDefault();
    }
  }
});
$('overlay').addEventListener('click', (e) => {
  if (e.target === $('overlay')) cerrarModal();
});
window.addEventListener('hashchange', () => {
  const ruta = location.hash.slice(1);
  S.ruta = VISTAS[ruta] ? ruta : 'inicio';
  S.offset = 0;
  render();
});
window.addEventListener('pagehide', () => S.desmontar?.());
async function iniciar() {
  try {
    try {
      if (localStorage.getItem('ciencias-tema') === 'oscuro') document.documentElement.classList.add('dark');
    } catch {}
    S.resumen = await api('/resumen');
    const r = location.hash.slice(1);
    S.ruta = VISTAS[r] ? r : 'inicio';
    await render();
  } catch (e) {
    $('view').innerHTML =
      `<section class="card error-card"><h2 class="h2">Producto de Ciencias no disponible</h2><p>${esc(e.message)}</p><p class="muted">La aplicación necesita el snapshot y sus fuentes verificadas. Consulta el procedimiento de restauración institucional.</p><a class="btn" href="/docs">Consultar API</a></section>`;
    $('snapshot').textContent = 'Sin publicación verificada · no se muestran datos de demostración';
  }
}
iniciar();
