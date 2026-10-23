import { ICONOS } from '/app/iconos.js';
export const $ = (id) => document.getElementById(id);
export const esc = (value) =>
  String(value ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );
export const numero = (value) => new Intl.NumberFormat('es-SV').format(value ?? 0);
export const icono = (name) =>
  `<span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONOS[name] || ICONOS.corpus}</svg></span>`;
export const ESTADOS = {
  respaldado_automaticamente: 'Respaldo automático',
  no_respaldado: 'Sin respaldo',
  abstencion: 'Abstención',
};
export const ROLES = {
  revision_ciencia: 'Ciencia',
  revision_curriculo: 'Currículo',
  revision_psicopedagogia: 'Psicopedagogía',
  revision_adversarial: 'Adversarial',
};
export const DISCIPLINAS = {
  biologia: 'Biología',
  fisica: 'Física',
  quimica: 'Química',
  ciencias_tierra_espacio: 'Tierra y espacio',
};
let snapshot = null;
export async function api(path, options = {}) {
  const response = await fetch('/api/v4/interfaz' + path, {
    headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}) },
    ...options,
  });
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error('La API no devolvió una respuesta válida.');
  }
  if (!response.ok)
    throw new Error(
      typeof data.detail === 'string'
        ? data.detail
        : data.detail?.motivo || 'No se pudo consultar la publicación de Ciencias.',
    );
  if (snapshot && data.snapshot_id !== snapshot)
    throw new Error('La publicación cambió. Recarga la aplicación para consultar una sola versión.');
  if (data.snapshot_id) snapshot = data.snapshot_id;
  return data;
}
export function parametros(filtros, extra = {}) {
  const p = new URLSearchParams();
  for (const [key, value] of Object.entries({ ...filtros, ...extra }))
    if (value !== '' && value != null && value !== false) p.set(key, String(value));
  return '?' + p.toString();
}
export function estado(value) {
  const color =
    value === 'respaldado_automaticamente' ? 'green' : value === 'no_respaldado' ? 'red' : 'amber';
  return `<span class="pill ${color}">${esc(ESTADOS[value] || value)}</span>`;
}
export function enlaceSeguro(url, label) {
  if (!url) return '<span class="mini">Enlace no registrado</span>';
  try {
    const u = new URL(url);
    if (!['https:', 'http:'].includes(u.protocol) || u.username || u.password) return '';
  } catch {
    return '';
  }
  return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;
}
export function guardar(texto, nombre, tipo = 'text/plain;charset=utf-8') {
  const url = URL.createObjectURL(texto instanceof Blob ? texto : new Blob([texto], { type: tipo }));
  const a = document.createElement('a');
  a.href = url;
  a.download = nombre;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export async function descargar(path, nombre) {
  const r = await fetch(path);
  if (!r.ok) throw new Error('La exportación no está disponible para esta publicación.');
  const id = r.headers.get('X-Snapshot-ID');
  if (id && snapshot && id !== snapshot) throw new Error('La exportación pertenece a otra publicación.');
  guardar(await r.blob(), nombre);
}
