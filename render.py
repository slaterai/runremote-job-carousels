"""Render RunRemote job carousels.
For every jobs/<slug>.json without slides/<slug>/, writes slides/<slug>/slide1-3.png (1080x1350).
"""
import json, html, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

MARK = ('<svg viewBox="0 0 196 272" height="30"><path fill="#F0EADE" d="M33 267C58 263 79 244 89 216L94 204L94 109C94 36 94 12 93 10C89 1 70 1 50 10C26 21 11 40 5 65C4 73 2 210 4 242C5 270 6 271 33 267Z'
        'M160 265C181 260 196 236 192 213C191 203 188 199 179 190C170 181 164 178 154 177C133 176 113 187 107 205C104 215 104 232 108 241C115 259 138 270 160 265Z'
        'M141 162C143 162 144 161 145 161C153 161 174 142 182 128C195 106 196 70 185 50C159 5 114 -6 106 31C105 35 105 51 105 90C105 142 106 143 108 147C114 162 129 169 141 162Z"/></svg>')
ARROW = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
BUBBLE = '<svg width="44" height="44" viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.2 3.6c-.5.4-1.3.1-1.3-.6V16A2.5 2.5 0 0 1 4 13.5z" fill="#F0A92E" stroke="#0C0B0A" stroke-width="1.6" stroke-linejoin="round"/></svg>'

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;font-family:'Inter',sans-serif;overflow:hidden;color:#0C0B0A}
.s{position:relative;isolation:isolate;width:1080px;height:1350px;padding:0 112px;display:flex;flex-direction:column;justify-content:center;background-color:#FEFCF8;
 background-image:linear-gradient(rgba(12,11,10,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(12,11,10,.06) 1px,transparent 1px);background-size:54px 54px}
.grey{background-color:#EAE8E2}
.fade{background-image:none}
.fade::before{content:'';position:absolute;inset:0;z-index:-1;
 background-image:linear-gradient(rgba(12,11,10,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(12,11,10,.07) 1px,transparent 1px);background-size:54px 54px;
 -webkit-mask-image:linear-gradient(to bottom,#000 0,#000 150px,transparent 380px);mask-image:linear-gradient(to bottom,#000 0,#000 150px,transparent 380px)}
.logo{position:absolute;top:80px;left:112px;display:flex;align-items:center;gap:16px;font-weight:600;font-size:30px;letter-spacing:-.02em;padding:14px 26px 14px 16px;border-radius:999px;
 background:#fff;border:1.5px solid rgba(120,104,80,.14);box-shadow:0 10px 28px -14px rgba(52,38,18,.32)}
.logo .b{width:52px;height:52px;border-radius:13px;display:flex;align-items:center;justify-content:center;background:#0C0B0A}
.tag{position:absolute;top:96px;right:112px;font-size:20px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;padding:12px 24px;border-radius:999px;border:2.5px solid currentColor}
.eyebrow{font-size:24px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;margin-bottom:40px;display:flex;align-items:center;gap:14px}
.eyebrow:before{content:'';width:11px;height:11px;border-radius:50%;background:#F0A92E}
h1{font-size:100px;line-height:1.06;font-weight:700;letter-spacing:-.055em}
.g{background:#F0A92E;color:#0C0B0A;border-radius:12px;padding:0 12px;-webkit-box-decoration-break:clone;box-decoration-break:clone;font-style:normal}
.body .g{border-radius:8px;padding:0 6px}
.sub{margin-top:48px;font-size:34px;line-height:1.4;opacity:.62;letter-spacing:-.01em;max-width:820px}
.btn{color:#fff;font-weight:600;border-radius:999px;display:flex;align-items:center;gap:14px;
 background:radial-gradient(140% 90% at 15% 10%,rgba(255,255,255,.14),transparent 45%),linear-gradient(160deg,#2a2826,#0C0B0A 60%);
 box-shadow:0 14px 28px -12px rgba(12,11,10,.5),inset 0 1px 0 rgba(255,255,255,.18)}
.swipe{position:absolute;right:112px;bottom:188px;font-size:26px;padding:20px 34px}
.next{position:absolute;left:0;right:0;bottom:120px;margin:0 auto;width:max-content;font-size:28px;letter-spacing:-.01em;padding:20px 36px}
.dots{position:absolute;bottom:56px;left:0;right:0;display:flex;justify-content:center;gap:12px}
.dots i{width:12px;height:12px;border-radius:50%;display:block;background:rgba(12,11,10,.18)}
.dots i.on{background:#0C0B0A}
.h2{font-size:96px;line-height:.98;font-weight:700;letter-spacing:-.05em;margin:40px 0 48px}
.spec{border-top:2px solid #0C0B0A}
.sr{display:grid;grid-template-columns:250px 1fr;gap:24px;padding:26px 0 24px;border-bottom:1.5px solid rgba(12,11,10,.16);align-items:baseline}
.sr .n{font-size:20px;font-weight:600;letter-spacing:.15em;text-transform:uppercase;color:#8A8782;display:flex;gap:18px}
.sr .n b{color:#0C0B0A;background:#F0A92E;border-radius:6px;padding:2px 7px;font-weight:700;letter-spacing:.04em}
.sr .v{font-size:40px;font-weight:600;letter-spacing:-.035em;line-height:1.15}
.sr .v small{display:block;font-size:26px;color:#6B675F;font-weight:300;letter-spacing:-.01em;margin-top:6px}
.sr.big .v{font-size:58px;font-weight:700;letter-spacing:-.045em}
.top{justify-content:flex-start;padding-top:260px}
.body{font-size:40px;line-height:1.28;font-weight:600;letter-spacing:-.035em}
.apply{position:absolute;left:112px;right:112px;bottom:110px;background:#fff;border-radius:36px;border:1.5px solid rgba(120,104,80,.14);overflow:hidden;
 box-shadow:0 1px 0 rgba(255,255,255,.9) inset,0 24px 48px -26px rgba(52,38,18,.35),0 2px 6px -2px rgba(12,11,10,.06)}
.ap-top{display:flex;gap:26px;align-items:flex-start;padding:40px 44px 36px}
.ap-top svg{flex:none;margin-top:6px}
.lbl{font-size:20px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#8A8782}
.big{font-size:62px;font-weight:700;letter-spacing:-.05em;line-height:1.1;margin-top:10px}
.or{font-size:30px;color:#57534C;letter-spacing:-.015em;margin-top:10px}
.ap-bot{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:24px 30px 24px 44px;background:#F6F4EF;border-top:1.5px solid rgba(12,11,10,.07);font-size:27px;font-weight:500;letter-spacing:-.015em}
.fol{flex:none;font-size:24px;font-weight:600;color:#fff;background:#0C0B0A;border-radius:999px;padding:14px 26px}
.fol b{color:#F0A92E;margin-left:4px}
"""
HEAD = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap">'
        '<style>' + CSS + '</style>')


def e(s):
    return html.escape(s, quote=False)


def slides(job):
    logo = f'<div class="logo"><span class="b">{MARK}</span>RunRemote</div>'
    dots = lambda i: '<div class="dots">' + ''.join(f'<i class="{"on" if j == i else ""}"></i>' for j in range(3)) + '</div>'
    rows = ''
    for i, d in enumerate(job['details']):
        v = e(d['value']) + (f'<small>{e(d["note"])}</small>' if d.get('note') else '')
        rows += f'<div class="sr{" big" if d.get("big") else ""}"><div class="n"><b>{i + 1:02d}</b>{e(d["label"])}</div><div class="v">{v}</div></div>'
    desc = e(job['description'])
    if job.get('highlight'):
        desc = desc.replace(e(job['highlight']), f'<em class="g">{e(job["highlight"])}</em>')
    return [
        f'''<div class="s">{logo}<div class="tag">{e(job["dept"])}</div>
<div class="eyebrow">Now hiring</div><h1>{e(job["title_a"])}<br><span class="g">{e(job["title_b"])}</span></h1>
<div class="sub">{e(job["subtitle"])}</div><div class="btn swipe">Swipe for details →</div>{dots(0)}</div>''',
        f'''<div class="s grey fade">{logo}<div class="tag">Hiring now</div>
<div class="h2">The <span class="g">details</span></div><div class="spec">{rows}</div>
<div class="btn next">Description {ARROW}</div>{dots(1)}</div>''',
        f'''<div class="s top fade">{logo}<div class="tag">The role</div><div class="body">{desc}</div>
<div class="apply"><div class="ap-top">{BUBBLE}<div><div class="lbl">To apply</div>
<div class="big">Comment <span class="g">{e(job.get("keyword", "REMOTE"))}</span></div>
<div class="or">or follow the link in our bio</div></div></div>
<div class="ap-bot"><span>Follow us for more positions like this</span><span class="fol">Follow <b>+</b></span></div></div>{dots(2)}</div>''',
    ]


def render(job, out):
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1080, 'height': 1350}, device_scale_factor=2)
        for i, s in enumerate(slides(job), 1):
            pg.set_content(f'<html><head><meta charset="utf-8">{HEAD}</head><body>{s}</body></html>', wait_until='networkidle')
            pg.evaluate('document.fonts.ready')
            tmp = out / f'_tmp{i}.png'
            pg.screenshot(path=str(tmp))
            Image.open(tmp).convert('RGB').resize((1080, 1350), Image.LANCZOS).save(out / f'slide{i}.png', optimize=True)
            tmp.unlink()
        b.close()


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    for f in sorted((root / 'jobs').glob('*.json')):
        out = root / 'slides' / f.stem
        if (out / 'slide3.png').exists():
            continue
        render(json.loads(f.read_text()), out)
        print('rendered', f.stem)
