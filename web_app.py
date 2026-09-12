#!/usr/bin/env python3
"""QR Studio local web interface. Run: python web_app.py"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from url_to_svg import generate_svg, svg_to_png


PAGE = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>QR Studio｜透明二维码生成器</title>
  <style>
    :root {
      --ink: #1d1f2a; --muted: #1b365d; --canvas: #f1f0ec; --surface: #fff;
      --line: #bbbcbc; --primary: #004c97; --pale: #d5ebee; --signal: #3dcbd9;
      --accent: #a4dbe8; --danger: #e4002b;
      --sans: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --mono: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    }
    * { box-sizing: border-box; scrollbar-color: var(--line) transparent; scrollbar-width: thin; }
    *::-webkit-scrollbar { width: 10px; height: 10px; }
    *::-webkit-scrollbar-track { background: transparent; }
    *::-webkit-scrollbar-thumb { background: var(--line); border: 3px solid transparent; border-radius: 99px; background-clip: padding-box; }
    *::-webkit-scrollbar-thumb:hover { background-color: var(--muted); }
    html { min-width: 320px; background: var(--canvas); }
    body { margin: 0; color: var(--ink); font: 15px/1.55 var(--sans); }
    button, input { font: inherit; }
    button { cursor: pointer; }
    .shell { width: min(1216px, calc(100% - 40px)); margin: 0 auto; padding: 38px 0 48px; }
    header { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 28px; }
    .eyebrow { margin: 0 0 8px; color: var(--primary); font: 700 12px/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; }
    h1 { margin: 0; font-size: clamp(32px, 5vw, 58px); line-height: .98; letter-spacing: -.055em; }
    .intro { max-width: 390px; margin: 0; color: var(--muted); }
    main { display: grid; grid-template-columns: minmax(290px, 0.78fr) minmax(420px, 1.22fr); gap: 18px; align-items: stretch; }
    .panel { border: 1px solid var(--line); border-radius: 24px; background: var(--surface); }
    .controls { padding: clamp(22px, 3vw, 34px); }
    .section-label { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 24px; padding-bottom: 14px; border-bottom: 1px solid var(--line); font: 700 12px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; }
    .section-label span:last-child { color: var(--muted); font-weight: 500; }
    .field { margin-bottom: 20px; }
    label { display: block; margin-bottom: 7px; font-weight: 700; }
    .hint { display: block; margin-top: 6px; color: var(--muted); font-size: 12px; }
    input { width: 100%; min-height: 48px; padding: 11px 13px; border: 1px solid var(--line); border-radius: 12px; color: var(--ink); background: var(--surface); outline: none; transition: border-color .16s, box-shadow .16s; }
    input:hover { border-color: var(--muted); }
    input:focus-visible { border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 18%, transparent); }
    input[aria-invalid="true"] { border-color: var(--danger); }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .color-field { position: relative; }
    .color-field input { padding-right: 46px; font-family: var(--mono); text-transform: uppercase; }
    .swatch { position: absolute; right: 12px; bottom: 13px; width: 22px; height: 22px; border: 1px solid var(--line); border-radius: 7px; background: #1d1f2a; pointer-events: none; }
    fieldset { min-width: 0; padding: 0; border: 0; }
    legend { margin-bottom: 7px; font-weight: 700; }
    .format-options { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .format-option { display: flex; min-height: 46px; align-items: center; justify-content: center; gap: 8px; margin: 0; border: 1px solid var(--line); border-radius: 12px; cursor: pointer; font: 700 13px/1 var(--mono); }
    .format-option:hover { border-color: var(--muted); }
    .format-option:has(input:checked) { border-color: var(--primary); color: var(--primary); background: var(--pale); }
    .format-option:has(input:focus-visible) { outline: 3px solid color-mix(in srgb, var(--primary) 18%, transparent); outline-offset: 2px; }
    .format-option input { width: 16px; min-height: 16px; padding: 0; accent-color: var(--primary); }
    .ratio-head { display: flex; justify-content: space-between; align-items: baseline; }
    output { color: var(--primary); font: 700 13px/1 var(--mono); }
    input[type="range"] { min-height: 34px; padding: 0; accent-color: var(--primary); background: transparent; }
    .error { min-height: 22px; margin: 2px 0 12px; color: var(--danger); font-size: 13px; }
    .primary { width: 100%; min-height: 50px; border: 0; border-radius: 12px; color: #fff; background: var(--primary); font-weight: 750; transition: transform .12s, background .16s; }
    .primary:hover { background: var(--muted); }
    .primary:active { transform: translateY(1px); }
    .primary:focus-visible, .download:focus-visible { outline: 3px solid color-mix(in srgb, var(--primary) 28%, transparent); outline-offset: 3px; }
    .primary:disabled { cursor: not-allowed; opacity: .58; transform: none; }
    .preview-panel { position: relative; display: flex; min-height: 610px; flex-direction: column; overflow: clip; padding: clamp(20px, 3vw, 34px); }
    .stage { position: relative; display: grid; flex: 1; min-height: 390px; place-items: center; overflow: hidden; border: 1px solid var(--line); border-radius: 16px;
      background-color: var(--surface); background-image: linear-gradient(45deg, var(--pale) 25%, transparent 25%), linear-gradient(-45deg, var(--pale) 25%, transparent 25%), linear-gradient(45deg, transparent 75%, var(--pale) 75%), linear-gradient(-45deg, transparent 75%, var(--pale) 75%); background-size: 24px 24px; background-position: 0 0, 0 12px, 12px -12px, -12px 0; }
    .stage::before, .stage::after { content: ""; position: absolute; z-index: 2; width: 18px; height: 18px; border-color: var(--primary); pointer-events: none; }
    .stage::before { top: 14px; left: 14px; border-top: 2px solid var(--primary); border-left: 2px solid var(--primary); }
    .stage::after { right: 14px; bottom: 14px; border-right: 2px solid var(--primary); border-bottom: 2px solid var(--primary); }
    .placeholder { max-width: 250px; color: var(--muted); text-align: center; }
    .placeholder-mark { display: block; margin-bottom: 12px; color: var(--ink); font: 500 54px/1 var(--mono); }
    #preview { display: none; width: min(78%, 520px); aspect-ratio: 1; }
    .stage.ready #preview { display: block; }
    .stage.ready .placeholder { display: none; }
    .scan { position: absolute; z-index: 3; top: 8%; left: 12%; width: 76%; height: 2px; opacity: 0; background: var(--signal); box-shadow: 0 0 12px var(--signal); pointer-events: none; }
    .stage.busy .scan { opacity: 1; animation: scan 1.05s ease-in-out infinite alternate; }
    @keyframes scan { to { transform: translateY(min(440px, 44vw)); } }
    .result-bar { display: flex; min-height: 62px; align-items: center; justify-content: space-between; gap: 16px; padding-top: 18px; }
    .status { margin: 0; color: var(--muted); font-size: 13px; }
    .status strong { display: block; color: var(--ink); font-size: 14px; }
    .download { display: none; flex: 0 0 auto; padding: 10px 16px; border: 1px solid var(--ink); border-radius: 10px; color: var(--ink); text-decoration: none; font-weight: 700; }
    .download:hover { color: #fff; background: var(--ink); }
    .download.visible { display: inline-flex; }
    @media (max-width: 820px) { .shell { width: min(100% - 24px, 620px); padding-top: 24px; } header { display: block; } .intro { margin-top: 16px; } main { grid-template-columns: 1fr; } .preview-panel { min-height: 520px; } }
    @media (max-width: 440px) { .row { grid-template-columns: 1fr; } .preview-panel { min-height: 430px; } .stage { min-height: 310px; } .result-bar { align-items: flex-start; } }
    /* Override component animation declarations when the operating system requests reduced motion. */
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto; animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; } }
    @media (forced-colors: active) { * { scrollbar-color: auto; } .stage { background: Canvas; } }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div><p class="eyebrow">Vector output / Local only</p><h1>QR Studio</h1></div>
      <p class="intro">输入链接，生成带 Logo 的透明 SVG 或 PNG。链接只在本机编码，不会发送到外部服务。</p>
    </header>
    <main>
      <form class="panel controls" id="form" novalidate>
        <div class="section-label"><span>生成参数</span><span>01 / Input</span></div>
        <div class="field">
          <label for="url">目标链接</label>
          <input id="url" name="url" type="url" inputmode="url" autocomplete="url" placeholder="https://example.com" aria-describedby="url-hint form-error">
          <span class="hint" id="url-hint">请输入完整的 http:// 或 https:// 链接</span>
        </div>
        <div class="row">
          <div class="field"><label for="size">画布尺寸</label><input id="size" name="size" type="number" min="256" max="16384" step="1" value="1024"><span class="hint">256–16384 px</span></div>
          <div class="field"><label for="border">静区宽度</label><input id="border" name="border" type="number" min="4" max="32" step="1" value="4"><span class="hint">4–32 个模块</span></div>
        </div>
        <fieldset class="field">
          <legend>输出格式</legend>
          <div class="format-options">
            <label class="format-option"><input name="format" type="radio" value="svg" checked>SVG 矢量</label>
            <label class="format-option"><input name="format" type="radio" value="png">PNG 图片</label>
          </div>
          <span class="hint">SVG 适合编辑与印刷，PNG 适合直接使用</span>
        </fieldset>
        <div class="field color-field">
          <label for="color">二维码颜色</label>
          <input id="color" name="color" type="text" value="#1D1F2A" maxlength="7" spellcheck="false" autocomplete="off" aria-describedby="color-hint form-error">
          <span class="swatch" id="swatch" aria-hidden="true"></span>
          <span class="hint" id="color-hint">请输入六位十六进制颜色，例如 #004C97</span>
        </div>
        <div class="field">
          <div class="ratio-head"><label for="ratio">中央框比例</label><output id="ratio-value" for="ratio">0.333</output></div>
          <input id="ratio" name="ratio" type="range" min="0.12" max="0.36" step="0.001" value="0.333">
          <span class="hint">解码困难时会自动缩小</span>
        </div>
        <p class="error" id="form-error" role="alert"></p>
        <button class="primary" id="generate" type="submit"><span>生成二维码</span></button>
      </form>
      <section class="panel preview-panel" aria-labelledby="preview-title">
        <div class="section-label"><span id="preview-title">透明预览</span><span>02 / Output</span></div>
        <div class="stage" id="stage">
          <div class="scan"></div>
          <p class="placeholder"><span class="placeholder-mark">⌗</span>生成结果将在这里显示<br>棋盘格代表透明区域</p>
          <img id="preview" alt="生成的透明二维码预览">
        </div>
        <div class="result-bar">
          <p class="status" id="status" aria-live="polite"><strong id="status-title">等待生成</strong><span id="status-detail">SVG / PNG · 透明背景 · Logo</span></p>
          <a class="download" id="download" download="qrcode.svg">下载 SVG</a>
        </div>
      </section>
    </main>
  </div>
  <script>
    const form = document.querySelector('#form');
    const urlInput = document.querySelector('#url');
    const ratio = document.querySelector('#ratio');
    const colorInput = document.querySelector('#color');
    const swatch = document.querySelector('#swatch');
    const ratioValue = document.querySelector('#ratio-value');
    const error = document.querySelector('#form-error');
    const button = document.querySelector('#generate');
    const stage = document.querySelector('#stage');
    const preview = document.querySelector('#preview');
    const statusTitle = document.querySelector('#status-title');
    const statusDetail = document.querySelector('#status-detail');
    const download = document.querySelector('#download');
    let objectUrl = null;

    ratio.addEventListener('input', () => { ratioValue.value = Number(ratio.value).toFixed(3); });
    colorInput.addEventListener('input', () => {
      const value = colorInput.value.trim();
      if (/^#[0-9a-f]{6}$/i.test(value)) swatch.style.backgroundColor = value;
    });
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      error.textContent = '';
      urlInput.setAttribute('aria-invalid', 'false');
      colorInput.setAttribute('aria-invalid', 'false');
      if (!/^https?:\/\/\S+$/i.test(urlInput.value)) {
        error.textContent = '请输入完整且不含空格的 http:// 或 https:// 链接。';
        urlInput.setAttribute('aria-invalid', 'true');
        urlInput.focus();
        return;
      }
      if (!/^#[0-9a-f]{6}$/i.test(colorInput.value.trim())) {
        error.textContent = '颜色必须是 #RRGGBB 格式，例如 #004C97。';
        colorInput.setAttribute('aria-invalid', 'true');
        colorInput.focus();
        return;
      }
      button.disabled = true;
      button.querySelector('span').textContent = '正在生成…';
      stage.classList.add('busy');
      statusTitle.textContent = '正在计算';
      statusDetail.textContent = '尝试掩模并验证解码结果';
      try {
        const format = new FormData(form).get('format');
        const response = await fetch('/generate', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({url: urlInput.value, size: Number(form.size.value), border: Number(form.border.value), center_ratio: Number(ratio.value), color: colorInput.value.trim(), format})
        });
        if (!response.ok) {
          const payload = await response.json();
          throw new Error(payload.error || '生成失败，请检查参数后重试。');
        }
        const blob = await response.blob();
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = URL.createObjectURL(blob);
        preview.src = objectUrl;
        download.href = objectUrl;
        download.download = `qrcode.${format}`;
        download.textContent = `下载 ${format.toUpperCase()}`;
        stage.classList.add('ready');
        download.classList.add('visible');
        const actualRatio = response.headers.get('X-Center-Ratio');
        const version = response.headers.get('X-QR-Version');
        statusTitle.textContent = '生成并验证通过';
        statusDetail.textContent = `${format.toUpperCase()} · QR 版本 ${version} · 中央比例 ${actualRatio}`;
      } catch (problem) {
        error.textContent = problem.message;
        statusTitle.textContent = '未生成';
        statusDetail.textContent = '修正左侧参数后可以再次尝试';
      } finally {
        button.disabled = false;
        button.querySelector('span').textContent = '生成二维码';
        stage.classList.remove('busy');
      }
    });
    window.addEventListener('beforeunload', () => { if (objectUrl) URL.revokeObjectURL(objectUrl); });
  </script>
</body>
</html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        self.respond(200, PAGE.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16_384:
                raise ValueError("请求内容过大或为空。")
            data = json.loads(self.rfile.read(length))
            output_format = data.get("format", "svg")
            if output_format not in ("svg", "png"):
                raise ValueError("输出格式必须是 svg 或 png。")
            svg, ratio, version = generate_svg(
                data.get("url", ""), size=data.get("size", 1024),
                border=data.get("border", 4), center_ratio=data.get("center_ratio", 1 / 3),
                color=data.get("color", "#000000"))
            if output_format == "svg":
                body, content_type = svg.encode(), "image/svg+xml; charset=utf-8"
            else:
                body, content_type = svg_to_png(svg, data.get("size", 1024)), "image/png"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="qrcode.{output_format}"')
            self.send_header("X-Center-Ratio", f"{ratio:.3f}")
            self.send_header("X-QR-Version", str(version))
            self.security_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (json.JSONDecodeError, TypeError, ValueError, OverflowError) as exc:
            self.respond(400, json.dumps({"error": str(exc)}, ensure_ascii=False).encode(),
                         "application/json; charset=utf-8")
        except (ImportError, OSError) as exc:
            self.respond(500, json.dumps({"error": f"生成环境错误：{exc}"}, ensure_ascii=False).encode(),
                         "application/json; charset=utf-8")

    def respond(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.security_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def security_headers(self):
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'self' blob:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")

    def log_message(self, message, *args):
        print(f"[{self.log_date_time_string()}] {message % args}")


def main():
    parser = argparse.ArgumentParser(description="启动 QR Studio 本地网页")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"QR Studio 已启动：http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
