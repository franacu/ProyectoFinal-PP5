"""Genera docs/crce.html: un solo lugar con menú ☰ para presentar el backend y ver los diagramas.

Uso:  python3 docs/crce.py   (regenera diagrama.html, backend_presentacion.html y la carcasa)
Menú ☰ (tecla M):
  · Presentación (P): lista para elegir qué presentar (recorrido general o un grupo de archivos).
  · Diagramas (D): modelo de clases, estados y vista en lista, con zoom y recorrido con el teclado.
Dentro de la presentación: Espacio/→ avanzan, ← vuelve, Esc vuelve a la lista, D abre el diagrama de la clase.
"""
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
for script in ("diagrama_interactivo.py", "backend_presentacion.py"):
    subprocess.run([sys.executable, str(AQUI / script)], check=True)

HTML = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRCE · Presentación y diagramas</title><style>
:root{--bg:#0b1020;--panel:#121a2d;--panel2:#18243b;--text:#eef3ff;--muted:#9eacc6;--accent:#71d5c3;--line:#2a3854;--gold:#f3c969}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{font:15px/1.4 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}
main{position:absolute;inset:0}iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:var(--bg)}
iframe[hidden]{display:none}
#hb{position:fixed;z-index:30;top:6px;left:10px;width:40px;height:40px;border:1px solid var(--line);border-radius:10px;background:var(--panel2);color:var(--accent);font-size:21px;line-height:1;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.35)}
#hb:hover{border-color:var(--accent)}#hb:focus-visible,nav button:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
#velo{position:fixed;inset:0;z-index:15;background:rgba(5,8,18,.55);display:none}#velo.on{display:block}
nav{position:fixed;z-index:20;top:0;bottom:0;left:0;width:min(290px,86vw);background:var(--panel);border-right:1px solid var(--line);color:var(--text);display:flex;flex-direction:column;padding:12px 14px 16px;gap:8px;transform:translateX(-102%);transition:transform .2s}
nav.abierto{transform:none;box-shadow:8px 0 32px rgba(0,0,0,.5)}
@media (prefers-reduced-motion:reduce){nav{transition:none}}
nav h1{font-size:17px;margin:0 0 14px 52px;line-height:1.15}nav h1 small{display:block;font-weight:400;color:var(--muted);font-size:12px;margin-top:2px}
nav button.op{display:flex;gap:12px;align-items:center;width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--panel2);color:inherit;font:inherit;cursor:pointer;text-align:left}
nav button.op:hover{border-color:var(--accent)}nav button.op[aria-pressed=true]{border-color:var(--accent);background:#10242a}
.ico{width:24px;text-align:center;font-size:19px;color:var(--accent)}.t b{display:block;font-size:15px}.t small{display:block;color:var(--muted);font-size:12px;margin-top:1px}
.sp{flex:1}.ayuda{font-size:12.5px;color:var(--muted);padding:6px 4px;line-height:1.9}
kbd{background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:1px 7px;font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--text)}
</style></head><body>
<button id="hb" aria-label="Abrir el menú" aria-expanded="false" title="Menú (M)">☰</button><div id="velo"></div>
<nav aria-label="Menú"><h1>CRCE<small>Coordinación de Emergencias</small></h1>
<button class="op" id="bp" aria-pressed="true"><span class="ico">▶</span><span class="t"><b>Presentación</b><small>Elegí qué presentar: recorrido general o un archivo</small></span></button>
<button class="op" id="bd" aria-pressed="false"><span class="ico">◇</span><span class="t"><b>Diagramas</b><small>Con zoom; recorré clases, estados y lista</small></span></button>
<span class="sp"></span>
<div class="ayuda"><kbd>P</kbd> presentación · <kbd>D</kbd> diagramas · <kbd>M</kbd> menú<br>En la presentación: <kbd>Espacio</kbd> avanza, <kbd>Esc</kbd> vuelve a la lista, <kbd>D</kbd> abre el diagrama de la clase, <kbd>F</kbd> pantalla completa</div></nav>
<main><iframe id="fb" src="backend_presentacion.html" title="Presentación" allow="fullscreen" allowfullscreen></iframe><iframe id="fd" src="diagrama.html" title="Diagramas" allow="fullscreen" allowfullscreen hidden></iframe></main>
<script>
const fb=document.getElementById('fb'),fd=document.getElementById('fd'),bp=document.getElementById('bp'),bd=document.getElementById('bd'),nav=document.querySelector('nav'),velo=document.getElementById('velo'),hb=document.getElementById('hb');
function menu(v){const o=v===undefined?!nav.classList.contains('abierto'):v;nav.classList.toggle('abierto',o);velo.classList.toggle('on',o);hb.setAttribute('aria-expanded',o);hb.setAttribute('aria-label',o?'Cerrar el menú':'Abrir el menú')}
function modo(m,clase){
 if(m==='codigo')m='presentacion';
 const d=m==='diagrama';
 fb.hidden=d;fd.hidden=!d;
 bp.setAttribute('aria-pressed',!d);bd.setAttribute('aria-pressed',d);menu(false);
 const f=d?fd:fb;
 setTimeout(()=>{f.focus();f.contentWindow&&f.contentWindow.focus();if(d&&clase)f.contentWindow.postMessage({irAClase:clase},'*')},60)}
bp.onclick=()=>modo('presentacion');bd.onclick=()=>modo('diagrama');hb.onclick=()=>menu();velo.onclick=()=>menu(false);
addEventListener('message',e=>{const m=e.data||{};if(m.tema)document.body.classList.toggle('claro',m.tema==='claro');else if(m.modo)modo(m.modo,m.clase);else if(m.menu)menu()});
addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey||e.altKey)return;const t=e.key.toLowerCase();if(t==='p')modo('presentacion');else if(t==='d')modo('diagrama');else if(t==='m')menu();else if(e.key==='Escape')menu(false)});
fb.addEventListener('load',()=>fb.contentWindow.focus());
</script></body></html>"""
(AQUI / "crce.html").write_text(HTML, encoding="utf-8")
(AQUI / "index.html").write_text(HTML, encoding="utf-8")  # GitHub Pages sirve index.html en la raíz
print("docs/crce.html e index.html listos")
