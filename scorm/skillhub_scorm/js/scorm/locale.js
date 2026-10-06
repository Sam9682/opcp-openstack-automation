/**
 * Locale resolution for the SkillHub SCORM runtime.
 *
 * Resolves the display locale using Locale_Resolution precedence
 * (Requirements 3.1, 3.2, 3.3):
 *   1. A valid stored `skillhub-locale` value wins.
 *   2. Otherwise, a browser language beginning with `fr` resolves to `fr`.
 *   3. Otherwise, the resolved locale is `en`.
 *
 * All storage and navigator access is wrapped in try/catch so a missing or
 * throwing environment degrades gracefully to the default locale.
 *
 * Validates: Requirements 3.1, 3.2, 3.3
 */

/**
 * The locales shipped with the SCORM package (`en/` and `fr/` trees).
 * A stored value is only honoured when it is one of these.
 * @type {readonly string[]}
 */
export const SUPPORTED_LOCALES = ['en', 'fr'];

/**
 * The locale used when neither a stored value nor the browser language yields
 * a supported locale.
 * @type {string}
 */
export const DEFAULT_LOCALE = 'en';

/**
 * The localStorage key under which the learner's chosen locale is persisted.
 * @type {string}
 */
export const STORAGE_KEY = 'skillhub-locale';

/**
 * Read a key from localStorage, tolerating an absent or throwing storage.
 *
 * @param {string} key - The storage key to read.
 * @returns {string|null} The stored value, or `null` on absence / error.
 */
function readStored(key) {
  try {
    if (typeof localStorage === 'undefined' || localStorage == null) {
      return null;
    }
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

/**
 * Read the browser's preferred language, tolerating an absent navigator.
 *
 * @returns {string} The browser language string, or `''` when unavailable.
 */
function readBrowserLanguage() {
  try {
    if (typeof navigator === 'undefined' || navigator == null) {
      return '';
    }
    return navigator.language || '';
  } catch {
    return '';
  }
}

/**
 * Resolve the display locale following the Locale_Resolution precedence.
 *
 * A valid stored `skillhub-locale` value (one of {@link SUPPORTED_LOCALES})
 * takes precedence. Otherwise, a browser language beginning with `fr`
 * (case-insensitive, e.g. `fr`, `fr-FR`, `FR`) resolves to `fr`. Otherwise
 * the resolved locale is {@link DEFAULT_LOCALE} (`en`).
 *
 * @returns {string} The resolved locale: a supported stored value, `fr`, or `en`.
 */
export function resolveLocale() {
  // 1. Valid stored value wins (Req 3.2).
  const stored = readStored(STORAGE_KEY);
  if (stored && SUPPORTED_LOCALES.indexOf(stored) !== -1) {
    return stored;
  }

  // 2. Browser language beginning with `fr` resolves to `fr` (Req 3.1).
  const browserLang = readBrowserLanguage().toLowerCase();
  if (browserLang.indexOf('fr') === 0) {
    return 'fr';
  }

  // 3. Fall back to the default locale (Req 3.3).
  return DEFAULT_LOCALE;
}
