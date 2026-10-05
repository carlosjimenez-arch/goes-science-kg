"""Descarga (o verifica) las fuentes externas listadas en data/referencia/externos/manifest.csv.

Uso:  python scripts/descargar_fuentes.py            # descarga lo que falte
      python scripts/descargar_fuentes.py --check    # solo verifica qué hay y qué falta
- Guarda cada archivo en data/referencia/externos/<archivo_local>.
- Si un archivo ya existe en ~/Downloads con el mismo nombre (descargado con el navegador), lo mueve.
- Escribe data/referencia/externos/estado.csv con tamaño y SHA-256 (trazabilidad).
- Algunos sitios gubernamentales bloquean descargas automáticas: en ese caso indica la URL para bajarla a mano.
"""
import csv, hashlib, os, shutil, sys, urllib.request

BASE = 'data/referencia/externos'
MAN = os.path.join(BASE, 'manifest.csv')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def valido(p):
    """Existe, pesa más de 1 KB y, si es PDF, empieza con %PDF (descarta páginas HTML de error)."""
    if not os.path.exists(p) or os.path.getsize(p) <= 1000:
        return False
    if p.lower().endswith('.pdf'):
        with open(p, 'rb') as f:
            return f.read(4) == b'%PDF'
    return True


def main(check=False):
    rows = list(csv.DictReader(open(MAN, encoding='utf-8')))
    estado = []
    for r in rows:
        dest = os.path.join(BASE, r['archivo_local'])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        dl = os.path.expanduser(os.path.join(os.environ.get('DESCARGAS', '~/Downloads'), os.path.basename(dest)))
        if not valido(dest) and valido(dl):
            shutil.copy2(dl, dest)
        if not valido(dest) and not check:
            try:
                req = urllib.request.Request(r['url'], headers=UA)
                with urllib.request.urlopen(req, timeout=120) as resp, open(dest, 'wb') as out:
                    shutil.copyfileobj(resp, out)
            except Exception as e:
                print(f"FALTA {r['id']}: {e} → descargar a mano: {r['url']}")
        ok = valido(dest)
        estado.append({'id': r['id'], 'archivo_local': r['archivo_local'], 'ok': ok,
                       'bytes': os.path.getsize(dest) if ok else 0, 'sha256': sha(dest) if ok else ''})
        print(('OK    ' if ok else 'FALTA ') + r['archivo_local'])
    with open(os.path.join(BASE, 'estado.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(estado[0].keys())); w.writeheader(); w.writerows(estado)
    print(f"{sum(e['ok'] for e in estado)}/{len(estado)} fuentes disponibles")


if __name__ == '__main__':
    main(check='--check' in sys.argv)
