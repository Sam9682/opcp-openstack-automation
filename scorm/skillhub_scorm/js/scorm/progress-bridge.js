/**
 * Progress_Bridge - Translates between the course's localStorage progress keys
 * and the single SCORM `cmi.suspend_data` string (the Suspend_Envelope).
 *
 * This is the non-invasive seam between the course and the LMS: it only ever
 * reads/writes the `skillhub_lesson_complete_*` keys the course's progress
 * module already owns, so no existing course module is modified. Every storage
 * access is guarded so the bridge degrades gracefully when localStorage is
 * unavailable or throws (Req 7.2).
 *
 * The Suspend_Envelope carries both the completed lesson ids and the
 * informational Guardrail_Assessment:
 *
 *   {"v":1,"done":["core-concepts","compute"],"guardrail":{"layers":[...],"covered":3}}
 *
 * The guardrail value is informational only — it rides inside the envelope but
 * never participates in the SCORM completion-status decision (Req 4.5).
 *
 * Validates: Requirements 4.5, 5.1, 5.2, 5.3, 7.2
 */

/**
 * The exact localStorage key prefix used by the course's progress module.
 * Preserved verbatim so restored keys match the course format exactly.
 * @type {string}
 */
export const STORAGE_PREFIX = "skillhub_lesson_complete_";

/**
 * Scan localStorage for the `skillhub_lesson_complete_`-prefixed keys and
 * return the completed lesson ids (prefix stripped). The ids are deduped and
 * sorted so the result is stable regardless of key iteration order.
 *
 * Returns an empty array when localStorage is unavailable or any access throws,
 * so a scan never raises (Req 7.2).
 *
 * @returns {string[]} completed lesson ids ([] on failure)
 */
export function readCompletedIds() {
  try {
    const seen = new Set();
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(STORAGE_PREFIX)) {
        if (localStorage.getItem(key) === "true") {
          seen.add(key.slice(STORAGE_PREFIX.length));
        }
      }
    }
    return Array.from(seen).sort();
  } catch {
    return [];
  }
}

/**
 * Encode completed ids and the informational guardrail into a Suspend_Envelope
 * JSON string of the form `{"v":1,"done":[...],"guardrail":{...}}` (Req 5.1).
 *
 * The ids are deduped and sorted so the output is stable regardless of input
 * ordering, and the envelope carries a schema version (`v`) to allow future
 * evolution. The guardrail is stored verbatim and is informational only
 * (Req 4.5).
 *
 * @param {string[]} ids - completed lesson ids
 * @param {*} [guardrail] - informational Guardrail_Assessment value
 * @returns {string} the serialized Suspend_Envelope
 */
export function serializeProgress(ids, guardrail) {
  const list = Array.isArray(ids) ? ids : [];
  const done = Array.from(
    new Set(list.filter((id) => typeof id === "string")),
  ).sort();
  return JSON.stringify({ v: 1, done, guardrail: guardrail ?? null });
}

/**
 * Decode a Suspend_Envelope back into `{ ids, guardrail }`. Tolerates empty,
 * malformed, or garbage input: a malformed envelope yields `ids = []` (and a
 * `null` guardrail) rather than throwing (Req 5.2, 5.3).
 *
 * @param {string} suspendData - the raw `cmi.suspend_data` string from the LMS
 * @returns {{ ids: string[], guardrail: * }} decoded ids and guardrail value
 */
export function deserializeProgress(suspendData) {
  if (typeof suspendData !== "string" || suspendData.length === 0) {
    return { ids: [], guardrail: null };
  }
  try {
    const parsed = JSON.parse(suspendData);
    if (!parsed || !Array.isArray(parsed.done)) {
      return { ids: [], guardrail: null };
    }
    const ids = parsed.done.filter((id) => typeof id === "string");
    const guardrail = parsed.guardrail ?? null;
    return { ids, guardrail };
  } catch {
    return { ids: [], guardrail: null };
  }
}

/**
 * Write completed ids back into localStorage using the exact course prefix,
 * reproducing the `skillhub_lesson_complete_*` keys the course owns (Req 5.2).
 * Each write is guarded so a storage error (unavailable, quota exceeded) causes
 * the restore to complete without raising (Req 7.2).
 *
 * @param {string[]} ids - completed lesson ids to restore
 */
export function restoreToLocalStorage(ids) {
  const list = Array.isArray(ids) ? ids : [];
  for (const id of list) {
    if (typeof id !== "string") {
      continue;
    }
    try {
      localStorage.setItem(STORAGE_PREFIX + id, "true");
    } catch {
      // Graceful degradation: storage unavailable or quota exceeded (Req 7.2).
    }
  }
}
