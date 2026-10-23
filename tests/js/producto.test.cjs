const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function application() {
  const filename = path.resolve(__dirname, '../../src/goes_science_kg/interfaz/estaticos/producto.js');
  const source = fs.readFileSync(filename, 'utf8')
    .replace(/^import \{[\s\S]*?\} from '\/app\/cliente\.js';\n/, '')
    .replace(/^import \{ montarGrafo \} from '\/app\/grafo\.js';\n/, '')
    .replace(/iniciar\(\);\s*$/, '');
  const elements = new Map();
  const events = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      innerHTML: '', textContent: '', hidden: true,
      setAttribute() {}, addEventListener() {}, focus() {}, scrollIntoView() {},
      classList: { add() {}, remove() {}, toggle() {} },
      querySelector() { return element('button'); }, querySelectorAll() { return []; },
      style: { setProperty() {} },
    });
    return elements.get(id);
  }
  const requests = [];
  const context = {
    URLSearchParams, Intl, Map, Set, setTimeout() {}, clearTimeout() {},
    document: { getElementById: element, addEventListener(name, handler) { events.set(name, handler); }, documentElement: element('root'), body: element('body') },
    window: { addEventListener(name, handler) { events.set(name, handler); } }, location: { hash: '' },
    $: element, esc: String, numero: String, icono() { return ''; },
    DISCIPLINAS: {}, ROLES: {}, enlaceSeguro() { return ''; }, estado() { return ''; },
    guardar() {}, descargar() {}, montarGrafo() {},
    parametros(filters, extras = {}) { return '?' + new URLSearchParams({ ...filters, ...extras }); },
    api(url, options) { return new Promise((resolve, reject) => requests.push({ url, options, resolve, reject })); },
  };
  vm.createContext(context);
  vm.runInContext(source + '\nglobalThis.applicationTest = { S, render, accion };', context);
  const api = context.applicationTest;
  api.S.resumen = { grados: [], disciplinas: [], cobertura: { unidades: 0 }, nodos: 0, alertas_originales: 0 };
  return { ...api, requests, element, events };
}

test('a late corpus response cannot replace the current curriculum data or pagination', async () => {
  const { S, render, accion, requests, element } = application();
  S.ruta = 'corpus';
  const old = render();
  S.ruta = 'curricularizacion';
  const current = render();
  requests[1].resolve({ total: 60, offset: 0, limite: 25, filas: [] });
  await current;
  const visible = element('view').innerHTML;
  requests[0].resolve({ total: 35, documentos: [] });
  await old;
  assert.equal(S.datosVista.limite, 25);
  assert.equal(element('view').innerHTML, visible);
  const next = accion({ target: { closest() { return { dataset: { action: 'siguiente' } }; } } });
  assert.equal(S.offset, 25);
  assert.match(requests[2].url, /offset=25/);
  assert.doesNotMatch(requests[2].url, /NaN/);
  requests[2].resolve({ total: 60, offset: 25, limite: 25, filas: [] });
  await next;
});

test('pagination is ignored while a view has no committed page data', async () => {
  const { S, accion, requests } = application();
  S.datosVista = null;
  await accion({ target: { closest() { return { dataset: { action: 'siguiente' } }; } } });
  assert.equal(S.offset, 0);
  assert.equal(requests.length, 0);
});

function compileBrief(app) {
  const button = app.element('compilar-briefs');
  button.dataset = { action: 'briefs' };
  return app.accion({ target: { closest() { return button; } } });
}

function brief(formato = 'evaluacion') {
  return { fila_id: 'fila1', formato, titulo: 'Brief documental', markdown: `Formato: ${formato}` };
}

test('a late brief cannot restore an obsolete format, even after switching back', async () => {
  const app = application();
  app.S.ruta = 'contenido';
  app.S.seleccion.add('fila1');
  const old = compileBrief(app);
  for (const formato of ['cinco_fases', 'evaluacion']) {
    app.events.get('change')({ target: { closest() { return null; }, name: 'formato', value: formato } });
  }
  app.requests[0].resolve({ briefs: [brief()] });
  await old;
  assert.equal(app.S.briefs.length, 0);
  assert.equal(app.element('briefs-resultados').innerHTML, '');
  assert.equal(app.element('compilar-briefs').disabled, false);
});

test('selection changes discard pending and previously compiled briefs', async () => {
  const app = application();
  app.S.ruta = 'contenido';
  app.S.seleccion.add('fila1');
  const first = compileBrief(app);
  app.requests[0].resolve({ briefs: [brief()] });
  await first;
  assert.match(app.element('briefs-resultados').innerHTML, /Formato: evaluacion/);
  const pending = compileBrief(app);
  app.events.get('change')({ target: {
    closest() { return null; }, matches() { return true; }, dataset: { id: 'fila1' }, checked: false,
  } });
  app.requests[1].resolve({ briefs: [brief()] });
  await pending;
  assert.equal(app.S.seleccion.size, 0);
  assert.equal(app.S.briefs.length, 0);
  assert.equal(app.element('briefs-resultados').innerHTML, '');
  assert.equal(app.element('compilar-briefs').disabled, true);
});

test('a brief from an earlier visit cannot replace the latest compilation', async () => {
  const app = application();
  app.S.ruta = 'contenido';
  app.S.seleccion.add('fila1');
  const old = compileBrief(app);
  app.S.ruta = 'inicio';
  await app.render();
  app.S.ruta = 'contenido';
  const view = app.render();
  app.requests[1].resolve({ total: 1, offset: 0, limite: 20, filas: [] });
  await view;
  const current = compileBrief(app);
  app.requests[0].resolve({ briefs: [brief()] });
  await old;
  assert.equal(app.element('compilar-briefs').disabled, true);
  assert.equal(app.S.briefs.length, 0);
  app.requests[2].resolve({ briefs: [{ ...brief(), markdown: 'Current visit' }] });
  await current;
  assert.match(app.element('briefs-resultados').innerHTML, /Current visit/);
  assert.equal(app.element('compilar-briefs').disabled, false);
});

test('an error from an obsolete compilation does not display a stale notification', async () => {
  const app = application();
  app.S.ruta = 'contenido';
  app.S.seleccion.add('fila1');
  const old = compileBrief(app);
  app.events.get('change')({ target: { closest() { return null; }, name: 'formato', value: 'cinco_fases' } });
  app.requests[0].reject(new Error('Obsolete error'));
  await old;
  assert.equal(app.element('toast').textContent, '');
});
