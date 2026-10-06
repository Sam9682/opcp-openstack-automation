/**
 * ScormApiWrapper — a thin, defensive wrapper over the raw SCORM 1.2 LMS `API`
 * method surface: `LMSInitialize`, `LMSGetValue`, `LMSSetValue`, `LMSCommit`,
 * `LMSFinish`, and `LMSGetLastError`.
 *
 * Two safety guarantees keep the course operational in every environment:
 *
 *  - **Standalone mode (no LMS).** When constructed with a `null` api — the
 *    result of a failed `discoverApi()` — every method is an inert no-op that
 *    returns a safe default (`""` for value reads, `false` for operations), so
 *    the SCO keeps working with no LMS attached.
 *  - **Error tolerance.** Every raw LMS call is wrapped in `try/catch`; a
 *    throwing LMS method is contained and the same safe default is returned,
 *    so an LMS fault never propagates into the course.
 *
 * Validates: Requirements 7.1, 7.3
 *
 * @module scorm-api
 */

export class ScormApiWrapper {
  /**
   * @param {object|null} api  The discovered LMS API object, or `null` to
   *                           build an inert, standalone-mode wrapper.
   */
  constructor(api) {
    /** @type {object|null} */
    this.api = api;
  }

  /**
   * Whether a live LMS API object was discovered.
   * @returns {boolean}
   */
  get available() {
    return this.api != null;
  }

  /**
   * Begin the SCORM session via `LMSInitialize("")`.
   * @returns {boolean} `true` when the LMS reports success; `false` otherwise,
   *                    when no API is available, or when the call throws.
   */
  initialize() {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSInitialize("");
      return result === "true" || result === true;
    } catch {
      return false;
    }
  }

  /**
   * Read a data model element via `LMSGetValue`.
   * @param {string} element  e.g. `"cmi.suspend_data"`.
   * @returns {string} The value as a string; `""` when no API is available or
   *                   the call throws.
   */
  getValue(element) {
    if (!this.available) {
      return "";
    }
    try {
      const value = this.api.LMSGetValue(element);
      return value == null ? "" : String(value);
    } catch {
      return "";
    }
  }

  /**
   * Write a data model element via `LMSSetValue`.
   * @param {string} element  e.g. `"cmi.core.lesson_status"`.
   * @param {string|number} value
   * @returns {boolean} `true` when the LMS reports success; `false` otherwise,
   *                    when no API is available, or when the call throws.
   */
  setValue(element, value) {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSSetValue(element, String(value));
      return result === "true" || result === true;
    } catch {
      return false;
    }
  }

  /**
   * Persist pending values via `LMSCommit("")`.
   * @returns {boolean} `true` when the LMS reports success; `false` otherwise,
   *                    when no API is available, or when the call throws.
   */
  commit() {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSCommit("");
      return result === "true" || result === true;
    } catch {
      return false;
    }
  }

  /**
   * End the SCORM session via `LMSFinish("")`.
   * @returns {boolean} `true` when the LMS reports success; `false` otherwise,
   *                    when no API is available, or when the call throws.
   */
  finish() {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSFinish("");
      return result === "true" || result === true;
    } catch {
      return false;
    }
  }

  /**
   * Read the last LMS error code via `LMSGetLastError`.
   * @returns {string} The error code as a string; `""` when no API is
   *                   available or the call throws.
   */
  getLastError() {
    if (!this.available) {
      return "";
    }
    try {
      const code = this.api.LMSGetLastError();
      return code == null ? "" : String(code);
    } catch {
      return "";
    }
  }
}
