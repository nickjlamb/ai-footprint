/*! AI water & energy calculator widget · PharmaTools.AI · {{ORIGIN}}/widget
 * <script src="{{ORIGIN}}/widget.js" data-theme="auto" data-accent="1d5bff" data-prompts="25" data-mix="text" async></script>
 * Replaces the script tag with an iframe and keeps its height in step with the content. No cookies, no tracking.
 */
(function () {
  var ORIGIN = '{{ORIGIN}}';
  var scripts = document.querySelectorAll('script[src^="' + ORIGIN + '/widget.js"]:not([data-done])');
  var frames = {};
  Array.prototype.forEach.call(scripts, function (s, i) {
    s.setAttribute('data-done', '1');
    var id = 'aifp' + Date.now().toString(36) + i;
    var q = new URLSearchParams({ id: id });
    ['theme', 'accent', 'prompts', 'mix', 'basis'].forEach(function (k) { var v = s.getAttribute('data-' + k); if (v) q.set(k, v); });
    var f = document.createElement('iframe');
    f.src = ORIGIN + '/widget?' + q.toString();
    f.title = 'AI water and energy calculator';
    f.loading = 'lazy';
    f.style.cssText = 'display:block;width:100%;max-width:640px;height:470px;border:0;margin:0 auto;color-scheme:normal';
    var credit = document.createElement('p');
    credit.style.cssText = 'max-width:640px;margin:6px auto 0;font:12px/1.4 system-ui,sans-serif;text-align:right;opacity:.75';
    credit.innerHTML = '<a href="https://www.pharmatools.ai/water-consumption-calculator">AI water calculator</a> by PharmaTools.AI';
    s.parentNode.insertBefore(credit, s.nextSibling);
    s.parentNode.insertBefore(f, s.nextSibling);
    frames[id] = f;
  });
  if (window.__aifpListening) { window.__aifpFrames = Object.assign(window.__aifpFrames || {}, frames); return; }
  window.__aifpListening = true; window.__aifpFrames = frames;
  window.addEventListener('message', function (e) {
    if (e.origin !== ORIGIN || !e.data || e.data.type !== 'ai-footprint-widget:height') return;
    var f = window.__aifpFrames[e.data.id];
    var h = Number(e.data.height);
    if (f && h > 100 && h < 2000) f.style.height = h + 'px';
  });
})();
