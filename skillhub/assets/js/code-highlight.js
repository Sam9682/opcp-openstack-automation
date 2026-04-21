/**
 * SkillHub — Code Block Manager
 *
 * Enhances <pre><code> blocks with CSS-based syntax highlighting,
 * copy-to-clipboard buttons, language labels, and line numbers.
 * Shared via the window.SkillHub namespace (no build tools).
 */
(function () {
  'use strict';

  /* Ensure namespace exists */
  window.SkillHub = window.SkillHub || {};

  /* ---- Regex tokenizers per language ---- */

  var PYTHON_RULES = [
    { pattern: /(#[^\n]*)/g, className: 'token-comment' },
    { pattern: /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, className: 'token-string' },
    { pattern: /(@\w+)/g, className: 'token-decorator' },
    { pattern: /\b(self)\b/g, className: 'token-self' },
    { pattern: /\b(def|class|import|from|if|elif|else|return|for|while|try|except|finally|with|as|raise|pass|break|continue|and|or|not|in|is|lambda|yield|global|nonlocal|assert|del|async|await)\b/g, className: 'token-keyword' },
    { pattern: /\b(True|False|None)\b/g, className: 'token-boolean' },
    { pattern: /\b(print|len|range|int|str|float|list|dict|set|tuple|type|isinstance|open|super|property|staticmethod|classmethod|enumerate|zip|map|filter|sorted|reversed|any|all|min|max|sum|abs|round|input|format|hasattr|getattr|setattr)\b/g, className: 'token-builtin' },
    { pattern: /\b(\d+\.?\d*(?:e[+-]?\d+)?)\b/g, className: 'token-number' }
  ];

  var YAML_RULES = [
    { pattern: /(#[^\n]*)/g, className: 'token-comment' },
    { pattern: /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, className: 'token-string' },
    { pattern: /\b(true|false|yes|no|on|off)\b/gi, className: 'token-boolean' },
    { pattern: /\b(\d+\.?\d*)\b/g, className: 'token-number' },
    { pattern: /^(\s*[\w][\w.\-]*)(?=\s*:)/gm, className: 'token-key' }
  ];

  var JSON_RULES = [
    { pattern: /("(?:\\.|[^"\\])*")(\s*:)/g, className: 'token-key', groupReplace: true },
    { pattern: /:\s*("(?:\\.|[^"\\])*")/g, className: 'token-string', groupIndex: 1 },
    { pattern: /\b(true|false)\b/g, className: 'token-boolean' },
    { pattern: /\b(null)\b/g, className: 'token-boolean' },
    { pattern: /\b(-?\d+\.?\d*(?:e[+-]?\d+)?)\b/g, className: 'token-number' }
  ];

  var HCL_RULES = [
    { pattern: /(#[^\n]*|\/\/[^\n]*)/g, className: 'token-comment' },
    { pattern: /("(?:\\.|[^"\\])*")/g, className: 'token-string' },
    { pattern: /(\$\{[^}]*\})/g, className: 'token-interp' },
    { pattern: /\b(resource|variable|provider|output|data|module|locals|terraform|backend)\b/g, className: 'token-block' },
    { pattern: /\b(true|false)\b/g, className: 'token-boolean' },
    { pattern: /\b(\d+\.?\d*)\b/g, className: 'token-number' },
    { pattern: /^\s*([\w]+)\s*=/gm, className: 'token-attr', groupIndex: 1 }
  ];

  var BASH_RULES = [
    { pattern: /(#[^\n]*)/g, className: 'token-comment' },
    { pattern: /("(?:\\.|[^"\\])*"|'[^']*')/g, className: 'token-string' },
    { pattern: /(\$\{?\w+\}?)/g, className: 'token-env' },
    { pattern: /(--[\w][\w-]*|-[a-zA-Z])\b/g, className: 'token-flag' },
    { pattern: /([|]|>{1,2}|<)/g, className: 'token-redirect' },
    { pattern: /\b(sudo|cd|ls|cat|echo|grep|awk|sed|curl|wget|pip|python|python3|export|source|chmod|chown|mkdir|rm|cp|mv|ssh|scp|docker|git|npm|apt|yum|dnf|systemctl|openstack|terraform|ansible)\b/g, className: 'token-command' },
    { pattern: /\b(\d+\.?\d*)\b/g, className: 'token-number' }
  ];

  var LANGUAGE_RULES = {
    python: PYTHON_RULES,
    yaml: YAML_RULES,
    yml: YAML_RULES,
    json: JSON_RULES,
    hcl: HCL_RULES,
    terraform: HCL_RULES,
    tf: HCL_RULES,
    bash: BASH_RULES,
    sh: BASH_RULES,
    shell: BASH_RULES
  };

  /* ---- Helper: escape HTML entities ---- */

  function escapeHtml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* ---- Helper: extract language from class name ---- */

  function extractLanguage(className) {
    if (!className) { return null; }
    var match = className.match(/(?:language|lang)-(\w+)/);
    return match ? match[1].toLowerCase() : null;
  }

  /* ---- Helper: count lines ---- */

  function countLines(text) {
    if (!text) { return 0; }
    var lines = text.split('\n');
    /* Ignore trailing empty line */
    if (lines.length > 1 && lines[lines.length - 1] === '') {
      return lines.length - 1;
    }
    return lines.length;
  }

  /* ---- Syntax Highlighting ---- */

  /**
   * Apply CSS-based syntax highlighting to a <code> element.
   * Uses regex tokenization to wrap matched tokens in <span class="token-xxx">.
   *
   * @param {HTMLElement} element - The <code> element to highlight.
   * @param {string} language - The language identifier (e.g. "python").
   */
  function highlightSyntax(element, language) {
    var rules = LANGUAGE_RULES[language];
    if (!rules) { return; }

    /* Add language class to the parent <pre> */
    var pre = element.parentElement;
    if (pre && pre.tagName === 'PRE') {
      pre.classList.add('lang-' + language);
    }

    var code = element.textContent;
    var escaped = escapeHtml(code);

    /* Track which character positions are already tokenized */
    var tokens = [];

    for (var r = 0; r < rules.length; r++) {
      var rule = rules[r];
      /* Reset regex lastIndex */
      rule.pattern.lastIndex = 0;
      var m;

      while ((m = rule.pattern.exec(escaped)) !== null) {
        var matchText;
        var matchStart;

        if (rule.groupReplace) {
          /* For JSON keys: wrap group 1 only, keep group 2 as-is */
          matchText = m[1];
          matchStart = m.index;
        } else if (rule.groupIndex) {
          matchText = m[rule.groupIndex];
          matchStart = m.index + m[0].indexOf(m[rule.groupIndex]);
        } else {
          matchText = m[1] || m[0];
          matchStart = m.index + m[0].indexOf(matchText);
        }

        var matchEnd = matchStart + matchText.length;

        /* Check overlap with existing tokens */
        var overlaps = false;
        for (var t = 0; t < tokens.length; t++) {
          if (matchStart < tokens[t].end && matchEnd > tokens[t].start) {
            overlaps = true;
            break;
          }
        }

        if (!overlaps) {
          tokens.push({
            start: matchStart,
            end: matchEnd,
            text: matchText,
            className: rule.className
          });
        }
      }
    }

    /* Sort tokens by start position (descending) so we can replace from end to start */
    tokens.sort(function (a, b) { return b.start - a.start; });

    /* Apply replacements from end to start to preserve positions */
    var result = escaped;
    for (var i = 0; i < tokens.length; i++) {
      var tok = tokens[i];
      result = result.substring(0, tok.start) +
        '<span class="' + tok.className + '">' + tok.text + '</span>' +
        result.substring(tok.end);
    }

    element.innerHTML = result;
  }

  /* ---- Copy to Clipboard ---- */

  /**
   * Copy the textContent of a <code> element to the clipboard.
   * Falls back to text selection when the Clipboard API is unavailable.
   *
   * @param {string} codeBlockId - The id of the <code> element.
   */
  function copyToClipboard(codeBlockId) {
    var element = document.getElementById(codeBlockId);
    if (!element) { return; }

    var text = element.textContent;
    var wrapper = element.closest('.code-block-wrapper');
    var button = wrapper ? wrapper.querySelector('.copy-btn') : null;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        /* Success feedback */
        if (button) {
          var originalText = button.textContent;
          button.textContent = '✓ Copied!';
          button.classList.add('copied');
          setTimeout(function () {
            button.textContent = originalText;
            button.classList.remove('copied');
          }, 2000);
        }
      }).catch(function () {
        /* Clipboard write failed — use fallback */
        fallbackSelect(element, button);
      });
    } else {
      /* Clipboard API unavailable — use fallback */
      fallbackSelect(element, button);
    }
  }

  /**
   * Fallback: select the text content so the user can Ctrl+C manually.
   */
  function fallbackSelect(element, button) {
    var selection = window.getSelection();
    var range = document.createRange();
    range.selectNodeContents(element);
    selection.removeAllRanges();
    selection.addRange(range);

    if (button) {
      var originalText = button.textContent;
      button.textContent = 'Select + Ctrl+C';
      button.classList.add('copied');
      setTimeout(function () {
        button.textContent = originalText;
        button.classList.remove('copied');
      }, 2000);
    }
  }

  /* ---- Code Block Initialization ---- */

  /** Counter for generating unique code block IDs */
  var codeBlockCounter = 0;

  /**
   * Find all <pre><code> elements and enhance them with:
   * - Syntax highlighting
   * - Copy-to-clipboard button
   * - Language label
   * - Line numbers (for blocks > 5 lines)
   *
   * Idempotent: skips blocks that already have a `data-highlighted` attribute.
   */
  function initializeCodeBlocks() {
    var codeBlocks = document.querySelectorAll('pre > code');

    for (var i = 0; i < codeBlocks.length; i++) {
      var codeEl = codeBlocks[i];
      var preEl = codeEl.parentElement;

      /* Idempotency guard */
      if (preEl.hasAttribute('data-highlighted')) {
        continue;
      }
      preEl.setAttribute('data-highlighted', 'true');

      /* Ensure the code element has an id for copy */
      if (!codeEl.id) {
        codeEl.id = 'code-block-' + codeBlockCounter++;
      }

      /* Extract language */
      var language = extractLanguage(codeEl.className);

      /* Apply syntax highlighting */
      if (language) {
        highlightSyntax(codeEl, language);
      }

      /* Wrap <pre> in .code-block-wrapper */
      var wrapper = document.createElement('div');
      wrapper.className = 'code-block-wrapper';
      preEl.parentNode.insertBefore(wrapper, preEl);
      wrapper.appendChild(preEl);

      /* Add language label */
      if (language) {
        var label = document.createElement('span');
        label.className = 'code-lang-label';
        label.textContent = language;
        wrapper.insertBefore(label, preEl);
      }

      /* Add copy button (positioned absolute top-right via CSS) */
      var copyBtn = document.createElement('button');
      copyBtn.className = 'copy-btn';
      copyBtn.textContent = 'Copy';
      copyBtn.setAttribute('aria-label', 'Copy code to clipboard');
      copyBtn.setAttribute('type', 'button');
      var blockId = codeEl.id;
      copyBtn.addEventListener('click', (function (id) {
        return function () { copyToClipboard(id); };
      })(blockId));
      wrapper.appendChild(copyBtn);

      /* Add line numbers for blocks > 5 lines */
      var lineCount = countLines(codeEl.textContent);
      if (lineCount > 5) {
        addLineNumbers(codeEl);
      }
    }
  }

  /**
   * Add line numbers to a code element.
   * Wraps each line in a <span class="line"> inside a line-numbers container.
   *
   * @param {HTMLElement} codeEl - The <code> element.
   */
  function addLineNumbers(codeEl) {
    codeEl.classList.add('line-numbers');

    var html = codeEl.innerHTML;
    var lines = html.split('\n');

    /* Remove trailing empty line if present */
    if (lines.length > 1 && lines[lines.length - 1] === '') {
      lines.pop();
    }

    var numbered = '';
    for (var i = 0; i < lines.length; i++) {
      numbered += '<span class="line">' + lines[i] + '</span>\n';
    }

    codeEl.innerHTML = numbered;
  }

  /* ---- Expose on namespace ---- */
  window.SkillHub.codeHighlight = {
    initializeCodeBlocks: initializeCodeBlocks,
    copyToClipboard: copyToClipboard,
    highlightSyntax: highlightSyntax
  };
})();
