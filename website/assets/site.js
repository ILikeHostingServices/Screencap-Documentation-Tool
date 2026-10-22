/*
  site.js
  2026-10-22
  Version: v1.0.0

  PURPOSE:
  The small scripts behind https://screencap.ilhs.app, built by
  website/build.py. Every page works without them.
  - Home page: links to the sections of the old single-page site
    (/#install, /#features, ...) go to the page that has them now.
  - Download page: the Windows, Linux, and macOS tabs. The address can
    pick one (download/#windows, #linux, #mac, or #install-windows and the
    like); otherwise the visitor's own system is picked. On Windows on ARM
    the ARM64 installer is offered first.
  - Copy buttons next to commands.
*/
(function () {
  var page = document.body.dataset.page;
  var hash = location.hash.slice(1);

  // Sections of the old single-page site, now pages of their own
  var moved = {
    'install': 'download/', 'install-windows': 'download/#windows',
    'install-linux': 'download/#linux', 'install-mac': 'download/#mac',
    'features': 'features/', 'psr': 'steps-recorder/',
    'requirements': 'requirements/', 'it': 'for-it/'
  };
  if (page === 'index' && moved[hash]) {
    location.replace(moved[hash]);
    return;
  }

  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  if (tabs.length) {
    var byName = {};
    tabs.forEach(function (t) { byName[t.getAttribute('aria-controls')] = t; });
    var show = function (tab, remember) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', on);
        document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
      });
      if (remember) history.replaceState(null, '', '#' + tab.getAttribute('aria-controls'));
    };
    tabs.forEach(function (t) { t.addEventListener('click', function () { show(t, true); }); });
    var choose = function () {
      var name = location.hash.slice(1).replace(/^install-/, '');
      if (byName[name]) {
        show(byName[name]);
        // Land on the tabs, not on the panel the address names
        var land = function () { document.querySelector('.install').scrollIntoView(); };
        if (document.readyState === 'complete') land();
        else window.addEventListener('load', function () { setTimeout(land, 0); });
        return;
      }
      // No system in the address: open on the visitor's own system
      var ua = navigator.userAgent;
      if (/Mac OS X/.test(ua) && !/iPhone|iPad/.test(ua)) show(byName.mac);
      else if (/Linux|X11/.test(ua) && !/Android/.test(ua)) show(byName.linux);
      else show(byName.windows);
    };
    choose();
    window.addEventListener('hashchange', choose);

    // Windows on ARM: offer the ARM64 installer first
    if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
      navigator.userAgentData.getHighEntropyValues(['architecture']).then(function (h) {
        if (h.architecture !== 'arm' || !/Windows/.test(navigator.userAgent)) return;
        var main = document.getElementById('dl-win'), alt = document.getElementById('dl-win-alt');
        var href = main.href, text = main.textContent;
        main.href = alt.href; main.textContent = alt.textContent;
        alt.href = href; alt.textContent = text;
      }).catch(function () {});
    }
  }

  function select(el) {
    var r = document.createRange();
    r.selectNodeContents(el);
    var s = getSelection();
    s.removeAllRanges();
    s.addRange(r);
  }
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var code = b.previousElementSibling;
      var done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1500); };
      try {
        navigator.clipboard.writeText(code.textContent).then(done, function () { select(code); });
      } catch (e) { select(code); }
    });
  });
})();
