// Proyección 3D en canvas, sin servicios externos. Los enlaces proceden de la API.
const COLORES = {
  Tema: '#3565fc',
  Unidad: '#1c1e4d',
  MejoraCurricular: '#0fae76',
  RevisionUnidad: '#0ea5a3',
  Documento: '#e0890b',
  ExpectativaNativa: '#8b5cf6',
};
export function montarGrafo(canvas, datos, seleccionar) {
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    canvas.replaceWith(
      Object.assign(document.createElement('p'), {
        textContent: 'Canvas no disponible. Consulta la tabla accesible de nodos.',
      }),
    );
    return () => {};
  }
  const porId = new Map(),
    proyecciones = new Map();
  const nodos = datos.nodos.map((n, i) => {
    const y = 1 - (2 * (i + 0.5)) / Math.max(1, datos.nodos.length),
      radio = Math.sqrt(1 - y * y),
      phi = i * Math.PI * (3 - Math.sqrt(5));
    const p = { ...n, x: radio * Math.cos(phi), y, z: radio * Math.sin(phi) };
    porId.set(n.id, p);
    return p;
  });
  let ancho = 1,
    alto = 1,
    angulo = 0.2,
    inclinacion = 0.15,
    zoom = 1,
    rotando = !matchMedia('(prefers-reduced-motion: reduce)').matches;
  let frame,
    ultimo = 0,
    arrastre = null,
    movido = false,
    activo = true;
  const tamano = () => {
    const r = canvas.getBoundingClientRect();
    ancho = r.width;
    alto = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = ancho * dpr;
    canvas.height = alto * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };
  const observador = new ResizeObserver(tamano);
  observador.observe(canvas);
  tamano();
  function dibujar(t) {
    if (!activo) return;
    if (rotando && !arrastre) angulo += Math.min((t - ultimo) / 1000, 0.04) * 0.12;
    ultimo = t;
    ctx.clearRect(0, 0, ancho, alto);
    proyecciones.clear();
    const radio = Math.min(ancho * 0.4, alto * 0.42) * zoom;
    for (const n of nodos) {
      const x = n.x * Math.cos(angulo) - n.z * Math.sin(angulo),
        z = n.x * Math.sin(angulo) + n.z * Math.cos(angulo);
      const y = n.y * Math.cos(inclinacion) - z * Math.sin(inclinacion),
        z2 = n.y * Math.sin(inclinacion) + z * Math.cos(inclinacion);
      const escala = 3 / (3 - z2 * 0.6);
      proyecciones.set(n.id, {
        x: ancho / 2 + x * radio * escala,
        y: alto / 2 + y * radio * escala,
        z: z2,
        r: (n.tipo === 'Unidad' ? 5 : 3.4) * escala,
      });
    }
    const dark = document.documentElement.classList.contains('dark');
    ctx.lineWidth = 0.7;
    for (const e of datos.aristas) {
      const a = proyecciones.get(e.origen),
        b = proyecciones.get(e.destino);
      if (!a || !b) continue;
      ctx.strokeStyle = dark ? 'rgba(139,153,197,.19)' : 'rgba(57,72,128,.15)';
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
    for (const n of [...nodos].sort((a, b) => proyecciones.get(a.id).z - proyecciones.get(b.id).z)) {
      const p = proyecciones.get(n.id);
      ctx.globalAlpha = 0.55 + (p.z + 1) * 0.22;
      ctx.fillStyle = COLORES[n.tipo] || '#8b5cf6';
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    frame = requestAnimationFrame(dibujar);
  }
  function cercano(e) {
    const r = canvas.getBoundingClientRect(),
      x = e.clientX - r.left,
      y = e.clientY - r.top;
    let elegido = null,
      distancia = 15;
    for (const n of nodos) {
      const p = proyecciones.get(n.id),
        d = Math.hypot(p.x - x, p.y - y);
      if (d < distancia) {
        distancia = d;
        elegido = n;
      }
    }
    return elegido;
  }
  const down = (e) => {
    arrastre = { x: e.clientX, y: e.clientY };
    movido = false;
    canvas.setPointerCapture(e.pointerId);
  };
  const move = (e) => {
    if (arrastre) {
      const dx = e.clientX - arrastre.x,
        dy = e.clientY - arrastre.y;
      if (Math.abs(dx) + Math.abs(dy) > 2) movido = true;
      angulo += dx * 0.006;
      inclinacion += dy * 0.006;
      arrastre = { x: e.clientX, y: e.clientY };
    } else {
      const n = cercano(e),
        label = document.getElementById('graph-hover');
      if (label)
        label.textContent = n ? `${n.tipo} · ${n.etiqueta}` : 'Arrastra para rotar · selecciona un nodo';
    }
  };
  const up = (e) => {
    if (!movido) {
      const n = cercano(e);
      if (n) seleccionar(n.id);
    }
    arrastre = null;
  };
  const rueda = (e) => {
    e.preventDefault();
    zoom = Math.max(0.5, Math.min(2, zoom * Math.exp(-e.deltaY * 0.001)));
  };
  const cancelar = () => {
    arrastre = null;
  };
  canvas.addEventListener('pointerdown', down);
  canvas.addEventListener('pointermove', move);
  canvas.addEventListener('pointerup', up);
  canvas.addEventListener('pointercancel', cancelar);
  canvas.addEventListener('wheel', rueda, { passive: false });
  const toggle = document.getElementById('rotacion');
  const pausa = () => {
    rotando = !rotando;
    toggle.setAttribute('aria-pressed', String(rotando));
    toggle.textContent = rotando ? 'Pausar giro' : 'Activar giro';
  };
  if (toggle) {
    toggle.textContent = rotando ? 'Pausar giro' : 'Activar giro';
    toggle.setAttribute('aria-pressed', String(rotando));
    toggle.addEventListener('click', pausa);
  }
  frame = requestAnimationFrame(dibujar);
  return () => {
    activo = false;
    cancelAnimationFrame(frame);
    observador.disconnect();
    canvas.removeEventListener('pointerdown', down);
    canvas.removeEventListener('pointermove', move);
    canvas.removeEventListener('pointerup', up);
    canvas.removeEventListener('pointercancel', cancelar);
    canvas.removeEventListener('wheel', rueda);
    toggle?.removeEventListener('click', pausa);
  };
}
