/**
 * Scorm_Adapter — orchestrates the SCORM start / sync / end lifecycle, mapping
 * the SkillHub course's completion data onto the SCORM 1.2 data model.
 *
 * The adapter is deliberately **pure by injection**: all course knowledge
 * arrives through the `deps` object (`getCompletionPercentage`, `totalLessons`,
 * `getCompletedLessons`, `evaluateGuardrailChecklist`, `readCheckedLayers`), so
 * the adapter never imports the course directly and its logic can be exercised
 * in isolation (Req 7.5). Its only collaborators are a `ScormApiWrapper`
 * (the defensive LMS surface) and the Progress_Bridge module (serialize /
 * deserialize / restore).
 *
 * Status mapping is **guardrail-independent**: `cmi.core.lesson_status` is
 * `completed` only when the Completion_Percentage is exactly 100 and
 * `incomplete` otherwise. The Guardrail_Assessment is informational only — it
 * is folded into `cmi.suspend_data` but never participates in the status
 * decision (Req 4.2, 4.3, 4.4).
 *
 * Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 5.4, 5.5, 5.6, 7.5
 *
 * @module scorm-adapter
 */

import {
  STORAGE_PREFIX,
  readCompletedIds,
  serializeProgress,
  deserializeProgress,
  restoreToLocalStorage,
} from "./progress-bridge.js";

/**
 * Default debounce window (ms) for the commit scheduled by {@link ScormAdapter#sync}.
 * @type {number}
 */
export const DEFAULT_COMMIT_DEBOUNCE_MS = 500;

/**
 * Map a Completion_Percentage onto the SCORM `cmi.core.lesson_status` value.
 *
 * The result depends **only** on the percentage — `completed` when it equals
 * 100, `incomplete` for every other value. The Guardrail_Assessment never
 * participates in this decision (Req 4.2, 4.3, 4.4).
 *
 * @param {number} pct  The Completion_Percentage (0–100).
 * @returns {"completed"|"incomplete"} the SCORM lesson status.
 */
export function computeStatus(pct) {
  return pct === 100 ? "completed" : "incomplete";
}

/**
 * @typedef {Object} ScormAdapterDeps
 * @property {() => number} getCompletionPercentage  Current completion percentage (0–100).
 * @property {() => number} [totalLessons]           Total number of lessons.
 * @property {() => string[]} [getCompletedLessons]  Completed lesson ids.
 * @property {() => *} [evaluateGuardrailChecklist]  Informational guardrail result.
 * @property {() => *} [readCheckedLayers]           Checked guardrail layers.
 */

export class ScormAdapter {
  /**
   * @param {import("./scorm-api.js").ScormApiWrapper} wrapper  Defensive LMS wrapper.
   * @param {object} bridge  The Progress_Bridge module (serialize / deserialize / restore).
   * @param {ScormAdapterDeps} deps  Injected course functions (Req 7.5).
   * @param {object} [options]
   * @param {number} [options.commitDebounceMs]  Debounce window for the commit schedule.
   */
  constructor(wrapper, bridge, deps, options = {}) {
    /** @type {import("./scorm-api.js").ScormApiWrapper} */
    this.wrapper = wrapper;
    /** @type {object} */
    this.bridge = bridge || {
      readCompletedIds,
      serializeProgress,
      deserializeProgress,
      restoreToLocalStorage,
      STORAGE_PREFIX,
    };
    /** @type {ScormAdapterDeps} */
    this.deps = deps || {};
    /** @type {number} */
    this.commitDebounceMs =
      typeof options.commitDebounceMs === "number"
        ? options.commitDebounceMs
        : DEFAULT_COMMIT_DEBOUNCE_MS;
    /** @type {ReturnType<typeof setTimeout>|null} */
    this._commitTimer = null;
  }

  /**
   * Read the current Completion_Percentage from the injected course function,
   * clamped to an integer in 0–100. Any missing dep or thrown error yields 0 so
   * the adapter never propagates a fault into the lifecycle.
   *
   * @returns {number} integer percentage in [0, 100]
   */
  _percentage() {
    try {
      const raw = this.deps.getCompletionPercentage
        ? this.deps.getCompletionPercentage()
        : 0;
      const n = Math.round(Number(raw));
      if (!Number.isFinite(n)) {
        return 0;
      }
      return Math.min(100, Math.max(0, n));
    } catch {
      return 0;
    }
  }

  /**
   * Evaluate the informational Guardrail_Assessment from the injected course
   * function. Returns `null` when no dep is provided or the call throws — the
   * guardrail is informational only and must never break the lifecycle (Req 4.4).
   *
   * @returns {*} the guardrail value, or `null`
   */
  _guardrail() {
    try {
      return this.deps.evaluateGuardrailChecklist
        ? this.deps.evaluateGuardrailChecklist()
        : null;
    } catch {
      return null;
    }
  }

  /**
   * Read the set of completed lesson ids. Prefers the injected
   * `getCompletedLessons` course function and falls back to scanning
   * localStorage through the bridge, so the suspend envelope always reflects
   * the course's own completion keys.
   *
   * @returns {string[]} completed lesson ids
   */
  _completedIds() {
    try {
      if (this.deps.getCompletedLessons) {
        const ids = this.deps.getCompletedLessons();
        if (Array.isArray(ids)) {
          return ids.filter((id) => typeof id === "string");
        }
      }
    } catch {
      // fall through to the bridge scan
    }
    return this.bridge.readCompletedIds();
  }

  /**
   * Restore completed lesson ids from `cmi.suspend_data` into localStorage,
   * then synchronize the SCORM values. Restoring **before** the course renders
   * lets the course pick up resumed progress on first paint (Req 5.4).
   */
  start() {
    const suspendData = this.wrapper.getValue("cmi.suspend_data");
    const { ids } = this.bridge.deserializeProgress(suspendData);
    this.bridge.restoreToLocalStorage(ids);
    this.sync();
  }

  /**
   * Synchronize the current course progress onto the SCORM data model:
   *
   *  - `cmi.core.score.raw`     ← integer Completion_Percentage (Req 4.1)
   *  - `cmi.core.lesson_status` ← {@link computeStatus} of the percentage (Req 4.2, 4.3)
   *  - `cmi.suspend_data`       ← Suspend_Envelope folding in the informational
   *                               guardrail (Req 4.5)
   *
   * The persisting `commit` is scheduled on a debounced timer so a burst of
   * progress changes collapses into a single LMS commit (Req 5.6).
   */
  sync() {
    const pct = this._percentage();
    this.wrapper.setValue("cmi.core.score.raw", pct);
    this.wrapper.setValue("cmi.core.lesson_status", computeStatus(pct));

    const ids = this._completedIds();
    const guardrail = this._guardrail();
    const envelope = this.bridge.serializeProgress(ids, guardrail);
    this.wrapper.setValue("cmi.suspend_data", envelope);

    this._scheduleCommit();
  }

  /**
   * Schedule a debounced `commit`. A pending timer is cleared and replaced, so
   * only the trailing call within the debounce window actually commits.
   *
   * @private
   */
  _scheduleCommit() {
    if (this._commitTimer != null) {
      clearTimeout(this._commitTimer);
    }
    this._commitTimer = setTimeout(() => {
      this._commitTimer = null;
      this.wrapper.commit();
    }, this.commitDebounceMs);
  }

  /**
   * Flush any pending debounced commit immediately, cancelling the timer. Used
   * by {@link end} so the final unload sequence is strictly ordered.
   *
   * @private
   */
  _flushPendingCommit() {
    if (this._commitTimer != null) {
      clearTimeout(this._commitTimer);
      this._commitTimer = null;
    }
  }

  /**
   * End the SCORM session on host unload: set `cmi.core.exit` to `suspend`,
   * then `commit`, then `finish`, in that exact order (Req 5.5). Any pending
   * debounced commit is cancelled so the terminal commit is the one that runs.
   */
  end() {
    this._flushPendingCommit();
    this.wrapper.setValue("cmi.core.exit", "suspend");
    this.wrapper.commit();
    this.wrapper.finish();
  }
}
