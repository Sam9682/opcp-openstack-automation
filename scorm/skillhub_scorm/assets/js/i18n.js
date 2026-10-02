/**
 * SkillHub — Language Router (i18n)
 *
 * Detects user language preference, routes to the correct locale folder,
 * and provides language switching on all pages.
 * Shared via the window.SkillHub namespace (no build tools).
 */
(function () {
  'use strict';

  /* Ensure namespace exists */
  window.SkillHub = window.SkillHub || {};

  var SUPPORTED_LOCALES = ['en', 'fr'];
  var DEFAULT_LOCALE = 'en';
  var STORAGE_KEY = 'skillhub-lang';

  /* ---- localStorage helpers (wrapped in try/catch) ---- */

  /**
   * Safely read a value from localStorage.
   * Returns null when localStorage is unavailable.
   */
  function storageGet(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  /**
   * Safely write a value to localStorage.
   * Silently fails when localStorage is unavailable.
   */
  function storageSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {
      /* graceful degradation — preference won't persist */
    }
  }

  /* ---- Public API ---- */

  /**
   * Detect the user's preferred locale.
   * Priority: localStorage → navigator.language → default ("en").
   * Always returns a member of SUPPORTED_LOCALES.
   */
  function detectLocale() {
    /* 1. Stored preference */
    var stored = storageGet(STORAGE_KEY);
    if (stored && SUPPORTED_LOCALES.indexOf(stored) !== -1) {
      return stored;
    }

    /* 2. Browser language */
    var browserLang = (navigator.language || '').substring(0, 2).toLowerCase();
    if (browserLang && SUPPORTED_LOCALES.indexOf(browserLang) !== -1) {
      return browserLang;
    }

    /* 3. Default */
    return DEFAULT_LOCALE;
  }

  /**
   * Extract the current locale from the URL path.
   * Looks for a supported locale segment (e.g. /en/ or /fr/).
   * Returns DEFAULT_LOCALE if none found.
   */
  function getCurrentLocale() {
    var path = window.location.pathname;
    for (var i = 0; i < SUPPORTED_LOCALES.length; i++) {
      if (path.indexOf('/' + SUPPORTED_LOCALES[i] + '/') !== -1) {
        return SUPPORTED_LOCALES[i];
      }
    }
    return DEFAULT_LOCALE;
  }

  /**
   * Check whether a URL exists on the server (same-origin only).
   * Uses a synchronous HEAD request so the result is available immediately.
   * Returns false on any error or non-200 status.
   */
  function pageExists(url) {
    try {
      var xhr = new XMLHttpRequest();
      xhr.open('HEAD', url, false); /* synchronous */
      xhr.send();
      return xhr.status >= 200 && xhr.status < 400;
    } catch (e) {
      return false;
    }
  }

  /**
   * Show a brief "translation pending" toast notification.
   * Automatically removes itself after 4 seconds.
   */
  function showTranslationPendingIndicator() {
    var toast = document.createElement('div');
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.textContent = 'Translation pending / Traduction en cours';
    toast.style.cssText =
      'position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);' +
      'background:#f59e0b;color:#fff;padding:0.75rem 1.5rem;border-radius:6px;' +
      'font-weight:600;z-index:9999;box-shadow:0 2px 8px rgba(0,0,0,0.15);';
    document.body.appendChild(toast);
    setTimeout(function () {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 4000);
  }

  /**
   * Switch to a different locale.
   * Replaces the locale segment in the current URL, persists the choice,
   * and navigates to the new page. If the target page does not exist,
   * shows a "translation pending" indicator and navigates to the target
   * locale's landing page instead.
   */
  function switchLanguage(targetLocale) {
    if (SUPPORTED_LOCALES.indexOf(targetLocale) === -1) {
      return;
    }

    var currentLocale = getCurrentLocale();
    var currentPath = window.location.pathname;

    /* Replace locale segment */
    var newPath = currentPath.replace(
      '/' + currentLocale + '/',
      '/' + targetLocale + '/'
    );

    /* Persist preference */
    storageSet(STORAGE_KEY, targetLocale);

    /* Check if target page exists; fall back to landing page if not */
    if (!pageExists(newPath)) {
      showTranslationPendingIndicator();
      var landingPath = currentPath.replace(
        '/' + currentLocale + '/',
        '/' + targetLocale + '/'
      ).replace(/\/[^/]*$/, '/index.html');
      setTimeout(function () {
        window.location.href = landingPath;
      }, 1500);
      return;
    }

    /* Navigate */
    window.location.href = newPath;
  }

  /**
   * Render the EN / FR language toggle buttons inside a container.
   * Expects a DOM element with class "lang-toggle" in the header.
   */
  function renderLanguageToggle(locale) {
    var container = document.querySelector('.lang-toggle');
    if (!container) {
      return;
    }

    container.innerHTML = '';

    SUPPORTED_LOCALES.forEach(function (loc) {
      var btn = document.createElement('button');
      btn.textContent = loc.toUpperCase();
      btn.setAttribute('aria-label', 'Switch language to ' + loc.toUpperCase());
      if (loc === locale) {
        btn.classList.add('active');
        btn.setAttribute('aria-current', 'true');
      }
      btn.addEventListener('click', function () {
        if (loc !== locale) {
          switchLanguage(loc);
        }
      });
      container.appendChild(btn);
    });
  }

  /* ---- Expose on namespace ---- */
  window.SkillHub.i18n = {
    detectLocale: detectLocale,
    getCurrentLocale: getCurrentLocale,
    switchLanguage: switchLanguage,
    renderLanguageToggle: renderLanguageToggle,
    SUPPORTED_LOCALES: SUPPORTED_LOCALES,
    DEFAULT_LOCALE: DEFAULT_LOCALE,
    STORAGE_KEY: STORAGE_KEY
  };
})();
