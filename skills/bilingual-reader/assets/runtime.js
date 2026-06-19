/* global clearTimeout, document, setTimeout, SpeechSynthesisUtterance, window */
/* ===================================================================
   runtime.js — 各独立模板共享的底层运行时（构建时注入 runtime JS token）。
   读取模板内已定义的 DATA / THEME，提供：主题应用与切换、朗读、
   词典浮窗挂载与定位、原文自动包裹可悬停词、词汇表分组、阅读进度。
   各模板只负责自己的页面骨架与渲染，交互能力统一从这里取。
   =================================================================== */
(function (global) {
  'use strict';

  var DATA = global.BILINGUAL_READER_DATA || {};
  var THEME = global.BILINGUAL_READER_THEME || {};
  var GLOSSARY = DATA.glossary || {};
  var DICT = GLOSSARY.dict || {};
  var LVC = { B1: 'b1', B2: 'b2', C1: 'c1', C2: 'c2', '术语': 'term' };
  var ORDER = ['B1', 'B2', 'C1', 'C2', '术语'];
  var LV_DESC = GLOSSARY.groupDesc || {
    B1: '入门进阶 · 日常常用', B2: '中级 · 学术与职场高频',
    C1: '高级 · 专业写作词汇', C2: '精通 · 地道高阶表达', '术语': '文章相关专有名词'
  };

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function applyVars(set) {
    if (!set) return;
    var root = document.documentElement.style;
    Object.keys(set).forEach(function (key) { root.setProperty('--' + key, set[key]); });
  }

  function applyTheme(mode) {
    applyVars(mode === 'light' ? THEME.light : THEME.dark);
    if (THEME.style) applyVars(THEME.style);
  }

  function toggleTheme() {
    var cur = document.documentElement.getAttribute('data-theme');
    if (cur === 'light') {
      document.documentElement.removeAttribute('data-theme');
      applyTheme('dark');
      return 'dark';
    }
    document.documentElement.setAttribute('data-theme', 'light');
    applyTheme('light');
    return 'light';
  }

  function speak(word, ev) {
    if (ev) ev.stopPropagation();
    try {
      global.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(word);
      u.lang = 'en-US'; u.rate = 0.9;
      global.speechSynthesis.speak(u);
    } catch { /* 浏览器不支持时静默 */ }
  }

  function canWrapTextNode(node) {
    var parent = node.parentElement;
    if (!parent || !node.nodeValue.trim()) return false;
    return !parent.closest('.w, script, style');
  }

  function isWordPart(ch) {
    return !!ch && /[A-Za-z0-9'’_-]/.test(ch);
  }

  function safeMatchInText(text, re) {
    var flags = re.flags.indexOf('g') >= 0 ? re.flags : re.flags + 'g';
    var scanner = new RegExp(re.source, flags);
    var match;
    while ((match = scanner.exec(text))) {
      var word = match[0];
      if (!word) {
        scanner.lastIndex += 1;
        continue;
      }
      var start = match.index || 0;
      var end = start + word.length;
      if (!isWordPart(text[start - 1]) && !isWordPart(text[end])) {
        return { word: word, start: start };
      }
    }
    return null;
  }

  function wrapFirstTextMatch(cell, re, key) {
    var walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        return canWrapTextNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var node;
    while ((node = walker.nextNode())) {
      re.lastIndex = 0;
      var match = safeMatchInText(node.nodeValue, re);
      if (!match) continue;
      var word = match.word;
      var start = match.start;
      var before = node.nodeValue.slice(0, start);
      var after = node.nodeValue.slice(start + word.length);
      var frag = document.createDocumentFragment();
      if (before) frag.appendChild(document.createTextNode(before));
      var span = document.createElement('span');
      span.className = 'w';
      span.dataset.k = key;
      span.textContent = word;
      var tip = document.createElement('span');
      tip.className = 'tip';
      span.appendChild(tip);
      frag.appendChild(span);
      if (after) frag.appendChild(document.createTextNode(after));
      node.parentNode.replaceChild(frag, node);
      return true;
    }
    return false;
  }

  /* 原文/正文：自动包裹可悬停词（每个词仅首次出现处高亮）。
     只处理纯文本节点，跳过已存在的 .w 标记，避免嵌套标签和重复词。 */
  function autowrap(cells) {
    var rules = (GLOSSARY.autowrap || []).map(function (a) {
      return [new RegExp(a[0], a[1] || 'i'), a[2]];
    });
    var list = Array.prototype.slice.call(cells);
    rules.forEach(function (rule) {
      var re = rule[0], key = rule[1];
      if (!DICT[key]) return;
      for (var i = 0; i < list.length; i++) {
        if (wrapFirstTextMatch(list[i], re, key)) break;
      }
    });
  }

  function positionTip(el, tip) {
    var m = 8, gap = 6;
    var r = el.getBoundingClientRect();
    var tw = tip.offsetWidth || 290;
    var th = tip.offsetHeight || 160;
    var vw = global.innerWidth, vh = global.innerHeight;
    var left = Math.max(m, Math.min(r.left, vw - tw - m));
    var above = false;
    var top = r.bottom + gap;
    if (top + th > vh - m) { top = r.top - th - gap; above = true; }
    top = Math.max(m, Math.min(top, vh - th - m));
    tip.classList.toggle('tip-above', above);
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }

  /* 为 root 内所有 .w 填充浮窗内容、挂载到 body 顶层并绑定交互。
     悬停由 JS 控制 tip-open 类（非纯 CSS :hover），隐藏延迟 120ms，
     滚动时立即收起（配合 CSS filter blur 淡出）。 */
  function mountTooltips(root) {
    var scope = root || document;
    scope.querySelectorAll('.w').forEach(function (el) {
      if (el.dataset.brBound === '1') return;
      var d = DICT[el.dataset.k];
      if (!d) return;
      var tip = el.querySelector('.tip');
      if (!tip) return;
      el.dataset.brBound = '1';
      var lvc = LVC[d.level] || '';
      var lvHtml = d.level ? '<span class="lv lv-' + lvc + '">' + escapeHtml(d.level) + '</span>' : '';
      var ipaHtml = d.ipa ? '<span class="ipa">' + escapeHtml(d.ipa) + '</span>' : '';
      tip.innerHTML =
        '<div class="h"><span class="word">' + escapeHtml(d.w) + '</span>' +
        '<button class="speak" title="朗读" data-speak="' + escapeHtml(d.w) + '">🔊</button></div>' +
        '<div class="sub">' + ipaHtml + '<span class="pos">' + escapeHtml(d.pos) + '</span>' + lvHtml + '</div>' +
        '<div class="def">' + escapeHtml(d.def) + '</div>' +
        '<div class="eg">' + escapeHtml(d.eg || '') + '<span class="egzh">' + escapeHtml(d.egzh || '') + '</span></div>';
      document.body.appendChild(tip);
      var btn = tip.querySelector('[data-speak]');
      if (btn) btn.addEventListener('click', function (ev) { speak(btn.getAttribute('data-speak'), ev); });
      var hideTimer = null;
      var show = function () { clearTimeout(hideTimer); positionTip(el, tip); tip.classList.add('tip-open'); };
      var hide = function () { hideTimer = setTimeout(function () { tip.classList.remove('tip-open'); }, 120); };
      el.addEventListener('mouseenter', show);
      el.addEventListener('mouseleave', hide);
      el.addEventListener('focusin', show);
      el.addEventListener('focusout', hide);
      tip.addEventListener('mouseenter', function () { clearTimeout(hideTimer); });
      tip.addEventListener('mouseleave', hide);
    });
  }

  /* 滚动时收起全部浮窗，避免气泡脱离单词浮在半空 */
  global.addEventListener('scroll', function () {
    document.querySelectorAll('.tip.tip-open').forEach(function (t) { t.classList.remove('tip-open'); });
  }, { passive: true });

  /* 词汇表按 CEFR 等级分组，返回 [{level, desc, lvc, items:[...]}] */
  function groupGlossary() {
    var grouped = {};
    Object.keys(DICT).forEach(function (k) {
      var d = DICT[k];
      (grouped[d.level] = grouped[d.level] || []).push(d);
    });
    var out = [];
    ORDER.forEach(function (lv) {
      var list = grouped[lv];
      if (!list || !list.length) return;
      list.sort(function (a, b) { return a.w.localeCompare(b.w); });
      out.push({ level: lv, desc: LV_DESC[lv] || '', lvc: LVC[lv] || '', items: list });
    });
    return out;
  }

  /* 阅读进度条：需要页面存在 #progress 元素。onScroll 可选，回传进度比。 */
  function initProgress(onScroll) {
    var bar = document.getElementById('progress');
    function update() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      var pct = max > 0 ? h.scrollTop / max : 0;
      if (bar) bar.style.width = (pct * 100) + '%';
      if (typeof onScroll === 'function') onScroll(pct, h.scrollTop, max);
    }
    global.addEventListener('scroll', update, { passive: true });
    global.addEventListener('resize', update);
    update();
    return update;
  }

  function focusFirstAnchor(anchors, options) {
    var list = Array.prototype.slice.call(anchors || []);
    var first = list.find(function (item) {
      return item && item.el && item.el.getBoundingClientRect;
    });
    if (!first) return;
    var behavior = options && options.behavior ? options.behavior : 'auto';
    global.requestAnimationFrame(function () {
      first.el.scrollIntoView({ behavior: behavior, block: 'start' });
    });
  }

  applyTheme('dark');

  global.BR = {
    DATA: DATA, THEME: THEME, DICT: DICT, LVC: LVC,
    escapeHtml: escapeHtml,
    applyVars: applyVars, applyTheme: applyTheme, toggleTheme: toggleTheme,
    speak: speak, autowrap: autowrap, mountTooltips: mountTooltips,
    positionTip: positionTip, groupGlossary: groupGlossary, initProgress: initProgress,
    focusFirstAnchor: focusFirstAnchor
  };
})(window);
