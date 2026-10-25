import {
  $,
  api,
  apiMateriales,
  textoMateriales,
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
  progresion: {
    nombre: 'Progresión 2.º–11.º',
    grupo: 'M2 · Corpus y Grafo',
    icono: 'layers',
    color: 'teal',
    sub: 'Cómo se introducen y refuerzan los conceptos',
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
  materiales: {
    nombre: 'Materiales docentes',
    grupo: 'M4 · Contenido',
    icono: 'clip',
    color: 'purple',
    sub: 'Biblioteca para preparar clases',
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
  briefEpoch: 0,
  epoch: 0,
  desmontar: null,
  datosVista: null,
  prevFocus: null,
  progVista: 'original',
  progPatron: '',
  matTipo: 'paquete_objetivo',
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
function filtros({ corpus = false, disciplina = true } = {}) {
  const grados = S.resumen.grados
    .map(
      (g) =>
        `<option value="${g.grado}" ${String(g.grado) === S.filtros.grado ? 'selected' : ''}>${g.grado}.º grado</option>`,
    )
    .join('');
  return `<form class="filters" id="filtros">${
    corpus
      ? `<select class="input" name="tipo" aria-label="Tipo de fuente"><option value="">Todas las fuentes</option><option value="curriculo" ${S.tipoFuente === 'curriculo' ? 'selected' : ''}>Currículo nacional</option><option value="referencia" ${S.tipoFuente === 'referencia' ? 'selected' : ''}>Referencias</option></select>`
      : `<select class="input" name="grado" aria-label="Grado"><option value="">Todos los grados</option>${grados}</select>${disciplina ? `<select class="input" name="disciplina" aria-label="Disciplina"><option value="">Todas las ciencias</option>${S.resumen.disciplinas.map((d) => `<option value="${esc(d)}" ${S.filtros.disciplina === d ? 'selected' : ''}>${esc(DISCIPLINAS[d] || d)}</option>`).join('')}</select>` : ''}`
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
  $('crumb').textContent = 'GOEs · ' + v.sub;
  $('miniic').innerHTML = icono(v.icono);
  $('vg').textContent = numero(S.resumen.nodos);
  $('vr').textContent = numero(S.resumen.cobertura.unidades);
  $('snapshot').textContent =
    `Ciencias V4 · Snapshot ${S.resumen.snapshot_id} · Revisión automática; aprobación institucional no acreditada`;
  document.title = `${v.nombre} · Ciencias · GOEs`;
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
  return { datos: d, html: `${titulo('Corpus', 'Matrices y referencias utilizadas por el producto. Los originales conservan su identidad y procedencia.')}${filtros({ corpus: true })}
    <div class="between"><p class="muted">${numero(d.total)} fuentes documentadas en la selección</p><span class="pill blue">Fuentes del snapshot V4</span></div>
    <div class="list">${d.documentos.map((x) => `<article class="li"><span class="tile">${icono('corpus')}</span><div><div class="ti">${esc(x.titulo)}</div><div class="sub">${x.tipo === 'curriculo' ? 'Currículo nacional' : 'Referencia'} · ${esc(x.version_documental || 'Edición en expediente')} · citada en ${x.usos} unidades</div><div class="clip-id">SHA ${esc(x.sha256 || 'No registrado en esta proyección')}</div>${x.licencia ? `<div class="mini">${esc(x.licencia)}</div>` : ''}</div><div class="rt">${enlaceSeguro(x.url, 'Fuente oficial')}</div></article>`).join('') || vacio('No hay fuentes con estos filtros.')}</div>
    ${aviso('Este corpus es el que respalda la publicación seleccionada. Incorporar otro archivo requiere ingesta y verificación antes de que pueda respaldar el grafo.')}` };
}
async function grafo() {
  const d = await api('/grafo' + parametros(S.filtros, { limite: 260 }));
  return { datos: d, html: `${titulo('Grafo 3D de conocimiento', 'Explora las relaciones reales del producto: cada enlace conserva su tipo y su sentido documental.')}${filtros()}
    <div class="stats">${stat(S.resumen.nodos, 'nodos del snapshot', true)}${stat(S.resumen.aristas, 'relaciones del snapshot')}${stat(d.nodos.length, 'nodos visibles')}${stat(d.aristas.length, 'relaciones visibles')}</div>
    ${d.nodos.length ? `<div class="graph-stage"><canvas id="canvas-grafo" aria-label="Proyección tridimensional del subgrafo; alternativa accesible en la tabla inferior"></canvas><div class="graph-hover" id="graph-hover">Arrastra para rotar · selecciona un nodo</div><div class="graph-tools"><button class="btn sm" id="rotacion" aria-pressed="true">Pausar giro</button></div><div class="graph-legend"><span><i style="background:#3565fc"></i>Fila curricular</span><span><i style="background:#1c1e4d"></i>Unidad</span><span><i style="background:#0fae76"></i>Propuesta</span><span><i style="background:#0ea5a3"></i>Revisión</span><span><i style="background:#e0890b"></i>Fuente</span></div></div>` : vacio('No hay nodos con estos filtros.')}
    <p class="muted spaced">${d.recortado ? `Subgrafo de ${d.nodos.length} nodos sobre ${numero(d.total_nodos_filtrados)} relacionados con el filtro.` : 'Todos los nodos de la selección están visibles.'} La posición 3D es visual; las aristas no representan automáticamente prerrequisitos.</p>
    <details class="card spaced"><summary>Ver nodos en tabla accesible · ${d.nodos.length}</summary><div class="table-wrap"><table class="atable"><thead><tr><th>Nodo</th><th>Tipo</th><th>Conexiones</th><th></th></tr></thead><tbody>${d.nodos.map((n) => `<tr><td class="objetivo">${esc(n.etiqueta)}</td><td>${esc(n.tipo)}</td><td>${n.conexiones}</td><td><button class="btn sm" data-action="nodo" data-id="${esc(n.id)}">Detalle</button></td></tr>`).join('')}</tbody></table></div></details>` };
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
  const columnas = [
    ['respaldado_automaticamente', 'Respaldo automático', 'green'],
    ['abstencion', 'Abstención', 'amber'],
    ['no_respaldado', 'Sin respaldo', 'red'],
  ];
  return { datos: d, html: `${titulo('Revisión de conocimiento', 'Dictámenes reales por unidad: ciencia, currículo, psicopedagogía y revisión adversarial.')}${filtros()}
    <div class="review-board">${columnas
      .map(([key, label, color]) => {
        const unidades = d.unidades.filter((u) => u.estado === key);
        return `<section class="review-column"><div class="between"><h3>${label}</h3><span class="pill ${color}">${unidades.length}</span></div>${unidades.map((u) => `<button class="review-item" data-action="unidad" data-id="${u.id}"><span class="mini">${u.grado}.º · ${esc(u.asignatura_malla)}</span><strong>${esc(u.unidad)}</strong><span class="mini">${u.filas} filas · ${u.rondas} ronda${u.rondas === 1 ? '' : 's'}</span>${dots(u.dictamenes)}</button>`).join('') || vacio('No hay unidades en este estado.')}</section>`;
      })
      .join('')}</div>
    ${aviso('Se muestran los resultados seleccionados y sus rondas reales. El expediente completo conserva los protocolos anteriores. Los especialistas que comparten proveedor no son estadísticamente independientes.')}` };
}
function tablaFilas(d, { checks = false } = {}) {
  return `<div class="table-wrap"><table class="atable"><thead><tr>${checks ? '<th>Elegir</th>' : ''}<th>Grado</th><th>Asignatura y unidad</th><th>Objetivo original</th><th>Propuesta</th><th></th></tr></thead><tbody>${d.filas.map((f) => `<tr>${checks ? `<td><input type="checkbox" class="seleccionar-fila" data-id="${esc(f.id)}" aria-label="Elegir ${esc(f.objetivo_original)}" ${S.seleccion.has(f.id) ? 'checked' : ''} ${f.fuera_alcance || !f.objetivo_propuesto ? 'disabled' : ''}></td>` : ''}<td>${f.grado}.º</td><td>${esc(f.asignatura)}<div class="mini">${esc(f.unidad)}</div></td><td class="objetivo">${esc(f.objetivo_original)}${f.alerta_original ? '<div class="spaced"><span class="pill amber">Alerta del original</span></div>' : ''}</td><td class="objetivo">${f.fuera_alcance ? '<span class="pill gray">Fuera de Ciencias</span>' : esc(f.objetivo_propuesto || 'Sin propuesta respaldada')}</td><td><button class="btn sm" data-action="fila" data-id="${esc(f.id)}">Comparar</button></td></tr>`).join('')}</tbody></table></div>${!d.filas.length ? vacio('No hay filas con estos filtros.') : ''}${paginador(d)}`;
}
async function curricularizacion() {
  const d = await api(
    '/filas' + parametros(S.filtros, { offset: S.offset, limite: 25, solo_alertas: S.soloAlertas }),
  );
  return { datos: d, html: `${titulo('Curricularización', 'Compara cada fila original con su propuesta: objetivos, indicadores, evaluación y didáctica.', excelBtn)}${filtros()}
    <div class="between"><div class="tabs"><button data-action="alertas" data-value="false" class="${!S.soloAlertas ? 'on' : ''}">Toda la malla</button><button data-action="alertas" data-value="true" class="${S.soloAlertas ? 'on' : ''}">Alertas del original · ${S.resumen.alertas_originales}</button></div>${csvBtn}</div>
    <section class="card spaced">${tablaFilas(d)}</section>${aviso('El orden es el de las filas del insumo. No se convierte en un calendario de 160 días: el grafo no contiene una carga lectiva oficial validada. Las propuestas corregidas conservan la alerta del original.')}` };
}
async function contenido() {
  const d = await api('/filas' + parametros(S.filtros, { offset: S.offset, limite: 20 }));
  return { datos: d, html: `${titulo('Templates y Brief', 'Organiza propuestas respaldadas en un brief trazable para preparar clases.')}
    <h3 class="h3">1 · Formato de organización</h3><div class="template-options"><label class="template-option"><input name="formato" type="radio" value="evaluacion" ${S.formato === 'evaluacion' ? 'checked' : ''}><b>Diseño por evidencias</b><p>Objetivo, indicador, producto y criterio de evaluación; didáctica, andamiaje, contexto y seguridad.</p></label><label class="template-option"><input name="formato" type="radio" value="cinco_fases" ${S.formato === 'cinco_fases' ? 'checked' : ''}><b>Cinco fases del insumo</b><p>Añade las fases originales: aproximar, explorar, explicar, indagar y reforzar. Las ausencias se indican.</p></label></div>
    <h3 class="h3 spaced">2 · Selecciona objetivos de Ciencias</h3>${filtros()}<div class="between"><p class="muted" id="seleccion-label">${S.seleccion.size} objetivos elegidos · máximo 20</p><button class="btn pri" data-action="briefs" id="compilar-briefs" ${!S.seleccion.size ? 'disabled' : ''}>${icono('content')}Compilar briefs</button></div><section class="card spaced">${tablaFilas(d, { checks: true })}</section>
    <div id="briefs-resultados">${resultadosBriefs()}</div>${aviso('El brief se compila a partir del texto ya respaldado. No genera otra clase con IA ni consume Vertex; conserva las condiciones de recursos y los límites de la propuesta.')}` };
}
function resultadosBriefs() {
  return S.briefs.length
    ? `<h3 class="h3 spaced">3 · Briefs compilados · ${S.briefs.length}</h3><div class="grid">${S.briefs.map((b, i) => `<section class="card"><div class="between"><strong>${esc(b.titulo)}</strong><button class="btn sm" data-action="brief-descarga" data-i="${i}">${icono('dl')}Markdown</button></div><details class="spaced"><summary>Leer brief documental</summary><pre class="source-text">${esc(b.markdown)}</pre></details></section>`).join('')}</div>`
    : '';
}
async function admin() {
  const d = await api('/administracion');
  const a = d.actividad_vertex?.estado === "sin_datos" ? null : d.actividad_vertex;
  return { datos: d, html: `${titulo('Administración', 'Estado de publicación, permisos de la aplicación y actividad registrada.')}
    <div class="stats">${stat('Lectura', 'modo de la aplicación', true)}${stat(Object.keys(d.archivos_snapshot).length, 'archivos del snapshot')}${stat(a ? a.llamadas : 'No disponible', 'invocaciones registradas')}${stat(4, 'roles de revisión')}</div>
    <div class="g2">${bloque('Identidad y permisos', '<span class="pill gray">Consulta local</span><p>No hay proveedor de identidad conectado. Esta sesión no acredita un usuario GOEs ni permite gestionar usuarios o aprobar el currículo institucionalmente.</p><div class="checks"><span class="pill green">Lectura</span><span class="pill gray">Sin generación de modelos</span></div>')}
    ${bloque('Integridad de la publicación', `<p>Las consultas comparten un único snapshot verificado. Si sus archivos cambian, la API se invalida hasta reiniciar el servicio.</p><div class="clip-id">${esc(d.snapshot_id)}</div><p><a href="/docs" target="_blank" rel="noopener">Abrir contrato OpenAPI ↗</a></p>`)}</div>
    <div class="card spaced"><h3 class="h3">Actividad de Vertex · campaña curricular V4</h3>${a ? `<p class="muted">${a.llamadas} invocaciones registradas · USD ${a.reserva_usd.toFixed(6)} de reserva conservadora. El importe facturado no está disponible. Consultar esta pantalla no consume modelos.</p><div class="table-wrap"><table class="atable"><thead><tr><th>Modelo</th><th>Rol</th><th>Estado</th><th>Invocaciones</th></tr></thead><tbody>${a.detalle.map((x) => `<tr><td>${esc(x.modelo)}</td><td>${esc(ROLES[x.rol] || x.rol)}</td><td>${esc(x.estado)}</td><td>${x.llamadas}</td></tr>`).join('')}</tbody></table></div>` : vacio('No hay un ledger disponible para consultar. No se supone un gasto de cero.')}</div>
    <details class="card spaced"><summary>Huellas de los archivos publicados</summary>${Object.entries(
      d.archivos_snapshot,
    )
      .map(([n, h]) => `<p><b>${esc(n)}</b><br><span class="clip-id">${esc(h)}</span></p>`)
      .join('')}</details>` };
}
const GRADOS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
const PATRONES = {
  aislado: ['Aislado', 'Aparece en un solo grado', 'gray'],
  concentrado: ['Concentrado', 'Dos grados, seguidos o con uno intermedio', 'blue'],
  espiral: ['Espiral', 'Tres o más grados con huecos de un grado como máximo', 'green'],
  intermitente: ['Intermitente', 'Vuelve tras dos o más grados sin tratarse', 'amber'],
};
const CLASES_TARDIAS = {
  prioritaria: ['Prioritaria', 'red'],
  revisar: ['Revisar', 'amber'],
  introduccion_cualitativa: ['Introducción cualitativa', 'gray'],
};
const pct = (a, b) => (b && a != null ? `${Math.round((a / b) * 100)} %` : '—');
const patronDe = (p) => PATRONES[p] || [String(p || '—'), '', 'gray'];
function franja(c) {
  return `<div class="gstrip" role="img" aria-label="Presente en ${esc(c.grados.map((g) => g + '.º').join(', '))}">${GRADOS.map((g) => {
    const n = c.filas_por_grado[String(g)] || 0;
    const m = !n && (c.grados_mencion || []).includes(g);
    return `<i class="${n ? 'on' : m ? 'men' : ''}" title="${g}.º · ${n ? `${numero(n)} fila${n === 1 ? '' : 's'} donde se trabaja` : m ? 'sólo mencionado' : 'ausente'}"></i>`;
  }).join('')}</div>`;
}
async function progresion() {
  const base = { vista: S.progVista };
  const [r, l] = await Promise.all([
    api('/progresion' + parametros(base)),
    api(
      '/progresion/conceptos' +
        parametros(base, { disciplina: S.filtros.disciplina, patron: S.progPatron, q: S.filtros.q }),
    ),
  ]);
  const conceptos = S.filtros.grado ? l.conceptos.filter((c) => c.grados.includes(Number(S.filtros.grado))) : l.conceptos;
  const p = r.patrones,
    total = r.conceptos_presentes,
    pr = r.prerrequisitos,
    a = r.acuerdo_v3,
    clases = pr.tardias_por_clase || {};
  const visibles = conceptos.slice(0, 150);
  return { datos: r, html: `${titulo('Progresión de 2.º a 11.º', 'Cómo se introduce cada concepto en la malla y en qué grados se vuelve a trabajar. Abre un concepto para ver sus filas.')}
    <div class="between"><div class="tabs"><button data-action="prog-vista" data-value="original" class="${S.progVista === 'original' ? 'on' : ''}">Malla original</button><button data-action="prog-vista" data-value="propuesta" class="${S.progVista === 'propuesta' ? 'on' : ''}">Con propuestas</button></div><span class="pill teal">${numero(r.filas_etiquetadas)} filas etiquetadas</span></div>
    <div class="stats spaced">${stat(total, 'conceptos presentes', true)}${stat(r.grados_promedio_por_concepto.toLocaleString('es-SV', { maximumFractionDigits: 1 }), 'grados por concepto (promedio)')}${stat(pct(p.espiral, total), 'en espiral')}${stat(pct(pr.ordenadas, pr.aristas_evaluables), 'prerrequisitos en orden')}</div>
    <div class="g2">${bloque('Patrón de refuerzo', barras(Object.entries(PATRONES).map(([k, v]) => [v[0], p[k]]), 'var(--teal)') + `<p class="mini">${Object.values(PATRONES).map((v) => `<b>${v[0]}</b>: ${v[1]}`).join(' · ')}</p><p class="mini">Contando también las menciones léxicas: ${Object.entries(PATRONES).map(([k, v]) => `${v[0].toLowerCase()} ${numero(r.patrones_con_menciones[k] || 0)}`).join(' · ')}.</p><p class="mini">Aislados de 2.º–9.º que no se retoman: <b>${numero(r.aislados_por_tramo['2_9_sin_retomar'] || 0)}</b> · aislados que se introducen en 10.º–11.º: <b>${numero(r.aislados_por_tramo['10_11'] || 0)}</b></p>`)}
    ${bloque('Orden de prerrequisitos', `${barras([['En orden', pr.ordenadas], ['En el mismo grado', pr.simultaneas], ['Posterior', pr.total_tardias]], 'var(--indigo)')}<div class="checks">${Object.entries(CLASES_TARDIAS).map(([k, [n, c]]) => `<span class="pill ${c}">${n} · ${clases[k] || 0}</span>`).join('')}</div><p class="mini">Se evalúan ${numero(pr.aristas_evaluables)} prerrequisitos del grafo histórico; el prerrequisito cuenta desde su primera etiqueta o mención (${pct(pr.ordenadas, pr.aristas_evaluables)} en orden; ${r.prerrequisitos_solo_etiquetas ? pct(r.prerrequisitos_solo_etiquetas.ordenadas, r.prerrequisitos_solo_etiquetas.aristas_evaluables) : '—'} contando sólo etiquetas). Una introducción cualitativa temprana puede ser intencional.</p>${r.verificacion ? `<div class="notice amber"><b>Verificación independiente de la clase prioritaria</b><br>${Object.entries(r.verificacion.conteo).map(([k, n]) => `${esc(k)}: ${numero(n)}`).join(' · ')}. Son hipótesis para revisión experta, no hallazgos confirmados.</div>` : ''}`)}</div>
    <div class="card spaced"><h3 class="h3">Introducción y refuerzo por grado</h3><div class="table-wrap"><table class="atable"><thead><tr><th>Grado</th><th>Filas</th><th>Conceptos</th><th>Nuevos</th><th>Retomados</th><th>Prácticas</th><th>Filas que anotan «Razonar» (TIMSS)</th></tr></thead><tbody>${r.grados.map((g) => `<tr><td>${numero(g.grado)}.º</td><td>${numero(g.filas)}</td><td>${numero(g.conceptos)}</td><td>${numero(g.introducidos)}</td><td>${numero(g.reforzados)}</td><td>${numero(g.practicas.length)}</td><td>${numero(g.filas_con_razonar)} · ${pct(g.filas_con_razonar, g.filas)}</td></tr>`).join('')}</tbody></table></div><p class="mini">La anotación TIMSS de la malla nombra varios dominios en casi todas las filas; no discrimina el nivel cognitivo y no se usa para medir profundización.</p></div>
    <div class="card spaced"><h3 class="h3">Entrada a bachillerato</h3><div class="table-wrap"><table class="atable"><thead><tr><th>Disciplina</th><th>Conceptos en 10.º–11.º</th><th>Con antecedente en 2.º–9.º</th><th>Nuevos en bachillerato</th><th>Conceptos de 2.º–9.º que continúan</th></tr></thead><tbody>${Object.entries(r.transicion_bachillerato).map(([k, t]) => `<tr><td>${esc(DISCIPLINAS[k] || k)}</td><td>${numero(t.conceptos_en_bachillerato)}</td><td>${numero(t.con_antecedente_2_9)}</td><td>${numero(t.nuevos_en_bachillerato.length)}</td><td>${numero(t.continuados_en_bachillerato)} de ${numero(t.conceptos_2_9)}</td></tr>`).join('')}</tbody></table></div></div>
    <details class="card spaced"><summary>Prerrequisitos que aparecen después del concepto que los necesita · ${numero(pr.total_tardias)}</summary><div class="table-wrap"><table class="atable"><thead><tr><th>Clase</th><th>Concepto</th><th>Prerrequisito</th><th>Desfase</th></tr></thead><tbody>${pr.tardias.map((t) => `<tr><td><span class="pill ${CLASES_TARDIAS[t.clase]?.[1] || 'gray'}">${esc(CLASES_TARDIAS[t.clase]?.[0] || t.clase)}</span></td><td><button class="linkish" data-action="concepto" data-id="${esc(t.concepto)}">${esc(t.nombre_concepto)}</button> · ${numero(t.grado_concepto)}.º</td><td>${t.prerrequisito_solo_mencion ? `${esc(t.nombre_prerrequisito)} <span class="mini">(sólo mencionado)</span>` : `<button class="linkish" data-action="concepto" data-id="${esc(t.prerrequisito)}">${esc(t.nombre_prerrequisito)}</button>`} · ${numero(t.grado_prerrequisito)}.º</td><td>${numero(t.desfase)} grado${t.desfase === 1 ? '' : 's'}</td></tr>`).join('')}</tbody></table></div></details>
    <h3 class="h3 spaced">Trayectorias por concepto</h3>${filtros()}
    <div class="tabs spaced"><button data-action="prog-patron" data-value="" class="${!S.progPatron ? 'on' : ''}">Todos</button>${Object.entries(PATRONES).map(([k, v]) => `<button data-action="prog-patron" data-value="${k}" class="${S.progPatron === k ? 'on' : ''}">${v[0]} · ${p[k]}</button>`).join('')}</div>
    <section class="card spaced"><div class="table-wrap"><table class="atable"><thead><tr><th>Concepto</th><th>Disciplina</th><th><div class="gstrip gstrip-head">${GRADOS.map((g) => `<span>${g}</span>`).join('')}</div></th><th>Patrón</th><th>Mayor hueco</th></tr></thead><tbody>${visibles.map((c) => `<tr><td><button class="linkish" data-action="concepto" data-id="${esc(c.id)}">${esc(c.nombre)}</button><div class="mini">${esc(c.nivel || 'nivel no declarado')}</div></td><td>${esc((c.asignaturas || [c.asignatura]).map((a) => DISCIPLINAS[a] || a).join(' · ') || '—')}</td><td>${franja(c)}</td><td><span class="pill ${patronDe(c.patron)[2]}">${esc(patronDe(c.patron)[0])}</span></td><td>${c.max_hueco ? numero(c.max_hueco) + (c.max_hueco === 1 ? ' grado' : ' grados') : '—'}</td></tr>`).join('')}</tbody></table></div>${!conceptos.length ? vacio('No hay conceptos con estos filtros.') : conceptos.length > visibles.length ? `<p class="mini">Se muestran ${visibles.length} de ${numero(conceptos.length)}; filtra por disciplina, grado o texto.</p>` : ''}</section>
    ${aviso(`Etiquetado de conceptos con ${numero(a.pares_evaluados)} filas comparables con la pasada V3: concepto principal coincidente ${pct(a.principal_coincide, 1)}, F1 ${a.f1_vs_v3}. ${r.limite}`)}` };
}
async function abrirConcepto(id) {
  const turno = ++modalEpoch;
  abrirModal('Trayectoria del concepto', aviso('Cargando trayectoria…'));
  try {
    const d = await api('/progresion/conceptos/' + encodeURIComponent(id) + parametros({ vista: S.progVista }));
    if (turno !== modalEpoch) return;
    const c = d.concepto;
    $('modal-title').textContent = c.nombre;
    $('modal-body').innerHTML =
      `<span class="pill ${patronDe(c.patron)[2]}">${esc(patronDe(c.patron)[0])}</span> <span class="pill gray">${esc((c.asignaturas || [c.asignatura]).map((a) => DISCIPLINAS[a] || a).join(' · '))}</span><div class="gstrip gstrip-head">${GRADOS.map((g) => `<span>${g}.º</span>`).join('')}</div>${franja(c)}
      <p class="mini">Primera aparición ${numero(c.primera)}.º · última ${numero(c.ultima)}.º · mayor hueco ${numero(c.max_hueco)} grado${c.max_hueco === 1 ? '' : 's'}${c.construido_en.length ? ` · se construye sobre él en ${esc(c.construido_en.map((g) => g + '.º').join(', '))}` : ''}</p>
      ${c.agrupa.length > 1 ? `<p class="mini">Agrupa conceptos equivalentes: ${c.agrupa.map(esc).join(', ')}</p>` : ''}
      ${Object.entries(c.filas).map(([g, filas]) => `<h3>${esc(g)}.º grado · ${numero(filas.length)} fila${filas.length === 1 ? '' : 's'}</h3><div class="list">${filas.map((f) => `<button class="review-item" data-action="fila" data-id="${esc(f.fila_id)}"><span class="mini">${esc(f.asignatura_malla)} · ${esc(f.unidad)}</span><strong>${esc(f.objetivo_propuesto || f.procedimental)}</strong>${f.objetivo_propuesto && f.objetivo_propuesto !== f.procedimental ? `<span class="mini">Original: ${esc(f.procedimental)}</span>` : ''}<span class="mini">Comparar original y propuesta →</span></button>`).join('')}</div>`).join('')}
      <p class="clip-id">${esc(c.id)}</p>`;
  } catch (e) {
    if (turno === modalEpoch) $('modal-body').innerHTML = aviso(e.message);
  }
}
const TIPOS_MATERIAL = {
  paquete_objetivo: ['Preparación por objetivo', 'V4'],
  paquete_unidad: ['Preparación por unidad', 'V4'],
  unidad_experimental: ['Unidad experimental', 'V4'],
  paquete_historico: ['Paquete histórico', 'V3'],
  actividad: ['Actividad', 'historico'],
  experimento: ['Experimento', 'historico'],
  dificultad: ['Dificultad frecuente', 'historico'],
  microtema: ['Microtema de refuerzo', 'historico'],
};
async function materiales() {
  const [tipoNombre, version] = TIPOS_MATERIAL[S.matTipo];
  const [salud, d] = await Promise.all([
    apiMateriales('/salud'),
    apiMateriales(
      parametros({ version, tipo: S.matTipo, grado: S.filtros.grado, q: S.filtros.q, limite: 25, offset: S.offset }),
    ),
  ]);
  return { datos: d, html: `${titulo('Materiales docentes', 'Biblioteca verificada para preparar clases a partir de las propuestas y del material histórico revisado.')}
    <div class="stats">${stat(salud.materiales, 'registros en la biblioteca', true)}${stat(salud.por_tipo.paquete_objetivo || 0, 'preparaciones por objetivo')}${stat(salud.por_tipo.paquete_unidad || 0, 'preparaciones por unidad')}${stat(0, 'llamadas a modelos por consulta')}</div>
    <div class="tabs tabs-wrap spaced">${Object.entries(TIPOS_MATERIAL).map(([k, [n]]) => `<button data-action="mat-tipo" data-value="${k}" class="${S.matTipo === k ? 'on' : ''}">${n} · ${numero(salud.por_tipo[k] || 0)}</button>`).join('')}</div>
    ${filtros({ disciplina: false })}
    <section class="card spaced"><div class="table-wrap"><table class="atable"><thead><tr><th>Material</th><th>Grados</th><th>Estado</th><th></th></tr></thead><tbody>${d.materiales.map((m) => `<tr><td class="objetivo">${esc(m.titulo)}<div class="mini">${esc(tipoNombre)} · ${esc(m.asignatura)}${m.unidad ? ' · ' + esc(m.unidad) : ''}</div></td><td>${esc(m.grados.map((g) => g + '.º').join(', ')) || '—'}</td><td><span class="pill ${/revisad|respaldad/.test(m.estado) ? 'green' : /pendiente/.test(m.estado) ? 'amber' : 'gray'}">${esc(m.estado.replaceAll('_', ' '))}</span></td><td><button class="btn sm" data-action="material" data-id="${esc(m.id)}">Abrir</button></td></tr>`).join('')}</tbody></table></div>${!d.materiales.length ? vacio('No hay materiales con estos filtros.') : ''}${paginador(d)}</section>
    ${aviso('Las preparaciones reutilizan propuestas con revisión automática de su unidad; no son guiones cronometrados nuevos ni acreditan aprobación institucional o eficacia en aula. El material histórico conserva su estado original, incluidos los pendientes.')}<p class="clip-id">Biblioteca ${esc(salud.biblioteca_id)} · snapshot ${esc(salud.snapshot_id)}</p>` };
}
async function abrirMaterial(id) {
  const turno = ++modalEpoch;
  abrirModal('Material docente', aviso('Cargando material…'));
  try {
    const [d, md] = await Promise.all([
      apiMateriales('/detalle/' + encodeURIComponent(id)),
      textoMateriales('/descarga/' + encodeURIComponent(id) + '?formato=md'),
    ]);
    if (turno !== modalEpoch) return;
    const m = d.material;
    $('modal-title').textContent = m.titulo;
    $('modal-body').innerHTML =
      `<span class="pill purple">${esc(TIPOS_MATERIAL[m.tipo]?.[0] || m.tipo)}</span> <span class="pill gray">${esc(m.estado.replaceAll('_', ' '))}</span>
      <div class="checks spaced"><button class="btn sm" data-action="mat-descarga" data-id="${esc(m.id)}" data-formato="md">${icono('dl')}Markdown</button><button class="btn sm" data-action="mat-descarga" data-id="${esc(m.id)}" data-formato="json">${icono('dl')}JSON</button>${m.fila_id ? `<button class="btn sm" data-action="fila" data-id="${esc(m.fila_id)}">Ver la fila curricular</button>` : ''}</div>
      <pre class="source-text">${esc(md)}</pre><p class="clip-id">${esc(m.id)} · SHA ${esc(m.sha256)}</p>`;
  } catch (e) {
    if (turno === modalEpoch) $('modal-body').innerHTML = aviso(e.message);
  }
}
const RENDER = { inicio, panel, corpus, grafo, progresion, revision, curricularizacion, contenido, materiales, admin };
async function render() {
  const epoch = ++S.epoch;
  S.briefEpoch++;
  S.datosVista = null;
  S.desmontar?.();
  S.desmontar = null;
  shell();
  $('view').setAttribute('aria-busy', 'true');
  $('view').classList.add('loading');
  try {
    const vista = await RENDER[S.ruta]();
    if (epoch !== S.epoch) return;
    S.datosVista = typeof vista === 'string' ? null : vista.datos;
    $('view').innerHTML = typeof vista === 'string' ? vista : vista.html;
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
  S.briefEpoch++;
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
    else if (a === 'concepto') await abrirConcepto(target.dataset.id);
    else if (a === 'material') await abrirMaterial(target.dataset.id);
    else if (a === 'mat-descarga') {
      const formato = target.dataset.formato === 'json' ? 'json' : 'md';
      await descargar(
        '/api/v4/materiales/descarga/' + encodeURIComponent(target.dataset.id) + '?formato=' + formato,
        `material-${target.dataset.id.slice(-12).replace(/[^a-zA-Z0-9_-]/g, '_')}.${formato}`,
      );
      toast('Material descargado · 0 llamadas a modelos');
    } else if (a === 'prog-vista' || a === 'prog-patron' || a === 'mat-tipo') {
      if (a === 'prog-vista') S.progVista = target.dataset.value === 'propuesta' ? 'propuesta' : 'original';
      else if (a === 'prog-patron') S.progPatron = target.dataset.value in PATRONES ? target.dataset.value : '';
      else if (target.dataset.value in TIPOS_MATERIAL) S.matTipo = target.dataset.value;
      S.offset = 0;
      await render();
    }
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
      if (!Number.isInteger(S.datosVista?.limite)) return;
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
      if (S.ruta !== 'contenido' || !S.seleccion.size) return;
      const turno = ++S.briefEpoch,
        vista = S.epoch,
        formato = S.formato,
        filas = [...S.seleccion];
      const vigente = () => turno === S.briefEpoch && vista === S.epoch &&
        S.ruta === 'contenido' && formato === S.formato && filas.length === S.seleccion.size &&
        filas.every((id) => S.seleccion.has(id));
      target.disabled = true;
      target.textContent = 'Compilando…';
      try {
        const d = await api('/briefs', {
          method: 'POST',
          body: JSON.stringify({ filas_ids: filas, formato }),
        });
        if (!vigente()) return;
        S.briefs = d.briefs;
        $('briefs-resultados').innerHTML = resultadosBriefs();
        $('briefs-resultados').scrollIntoView({ behavior: 'smooth' });
        toast(`${d.briefs.length} briefs compilados · 0 llamadas a modelos`);
      } catch (error) {
        if (vigente()) throw error;
      } finally {
        if (vigente()) {
          target.disabled = !S.seleccion.size;
          target.innerHTML = icono('content') + 'Compilar briefs';
        }
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
function invalidarBriefs() {
  S.briefEpoch++;
  S.briefs = [];
  $('briefs-resultados').innerHTML = '';
  $('compilar-briefs').disabled = !S.seleccion.size;
  $('compilar-briefs').innerHTML = icono('content') + 'Compilar briefs';
}
document.addEventListener('change', (e) => {
  if (e.target.closest('#filtros') && e.target.tagName === 'SELECT') {
    if (e.target.name === 'tipo') S.tipoFuente = e.target.value;
    else S.filtros[e.target.name] = e.target.value;
    S.offset = 0;
    render();
  } else if (e.target.name === 'formato') {
    S.formato = e.target.value;
    invalidarBriefs();
  } else if (e.target.matches('.seleccionar-fila')) {
    const id = e.target.dataset.id;
    if (e.target.checked && S.seleccion.size >= 20) {
      e.target.checked = false;
      toast('Elige como máximo 20 objetivos por lote.');
      return;
    }
    if (e.target.checked) S.seleccion.add(id);
    else S.seleccion.delete(id);
    invalidarBriefs();
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
window.addEventListener('pagehide', () => {
  S.briefEpoch++;
  S.desmontar?.();
});
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
      `<section class="card error-card"><h2 class="h2">No hay datos disponibles</h2><p>${esc(e.message)}</p><p class="muted">La aplicación necesita el snapshot y sus fuentes verificadas. Consulta el procedimiento de restauración institucional.</p><a class="btn" href="/docs">Consultar API</a></section>`;
    $('snapshot').textContent = 'Sin publicación verificada · no se muestran datos de demostración';
  }
}
iniciar();
