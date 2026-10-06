/**
 * scorm-bootstrap — the single runtime entry point a lesson page loads.
 *
 * This module wires the SCORM collaborators together and installs the lifecycle
 * listeners. It is the only `js/scorm/*` file lesson HTML references directly;
 * everything else (discovery, the defensive wrapper, the progress bridge, the
 * adapter) is reached through it.
 *
 * Wiring, in order (mirrors the run-time flow in the design doc):
 *
 *   DOMContentLoaded
 *     └─ bootstrap()
 *          ├─ discoverApi(window)              → Api_Discovery (null when standalone)
 *          ├─ new ScormApiWrapper(api)         → inert no-op surface when api == null
 *          ├─ wrapper.initialize()             → LMSInitialize (no-op when standalone)
 *          ├─ new ScormAdapter(wrapper, bridge, deps)
 *          ├─ adapter.start()                  → restores suspend_data into localStorage
 *          │                                     BEFORE the course renders, then syncs
 *          ├─ addEventListener("storage",  debounced sync)
 *          └─ addEventListener("pagehide", end)  → exit=suspend → Commit → Finish
 *
 * **Non-invasive by injection.** The adapter never imports the course. The
 * course exposes its functions on the `window.SkillHub` global namespace (the
 * same namespace the lesson HTML already uses, e.g. `window.SkillHub.i18n`).
 * The deps are read defensively from that namespace: any missing function
 * falls back to a safe no-op so the SCO still boots when the course modules are
 * absent or when running standalone (Req 7.1).
 *
 * **No double restore.** `adapter.start()` already restores from
 * `cmi.suspend_data` through the bridge before it syncs, so the bootstrap does
 * not restore separately — doing so would redundantly repopulate localStorage.
 *
 * **Testable.** `bootstrap` and `installListeners` are exported and the
 * automatic `DOMContentLoaded` install is guarded behind a `window`/`document`
 * check, so a test can import this module and drive the wiring with a mock
 * window without the module self-installing on import.
 *
 * Requirements: 5.4, 5.5, 5.6, 7.1
 *
 * @module scorm-bootstrap
 */

import { discoverApi } from "./api-discovery.js";
import { ScormApiWrapper } from "./scorm-api.js";
import * as bridge from "./progress-bridge.js";
import { ScormAdapter } from "./scorm-adapter.js";

/** A no-op used as a safe default for any absent course function. */
const NOOP = () => {};

/**
 * The course function names the adapter consumes, read from the course's global
 * namespace. Each is optional — a missing one is replaced by a safe default so
 * the runtime degrades to standalone mode (Req 7.1).
 * @type {readonly string[]}
 */
const DEP_NAMES = [
  "getCompletionPercentage",
  "getCompletedLessons",
  "evaluateGuardrailChecklist",
  "totalLessons",
  "readCheckedLayers",
];

/**
 * Build the injected `deps` object for the adapter by reading the course
 * functions off the `window.SkillHub` global, defensively.
 *
 * The course exposes its public functions on `window.SkillHub` (the same global
 * the lesson HTML already references). Any function that is absent — because
 * the course module did not load, or because the SCO runs standalone — is
 * replaced with a safe no-op so construction never throws and the adapter keeps
 * working with inert data (Req 7.1).
 *
 * @param {Window|object} [win=window] the host window (injectable for tests).
 * @returns {Record<string, Function>} the resolved, always-callable deps.
 */
export function resolveCourseDeps(win = typeof window !== "undefined" ? window : undefined) {
  /** @type {Record<string, Function>} */
  const deps = {};

  let ns = null;
  try {
    ns = win && win.SkillHub ? win.SkillHub : null;
  } catch {
    // Reading the global can throw in exotic hosts; treat as absent.
    ns = null;
  }

  for (const name of DEP_NAMES) {
    let fn = NOOP;
    try {
      const candidate = ns ? ns[name] : undefined;
      if (typeof candidate === "function") {
        // Bind to the namespace so `this` inside the course function is intact.
        fn = candidate.bind(ns);
      }
    } catch {
      fn = NOOP;
    }
    deps[name] = fn;
  }

  return deps;
}

/**
 * Install the SCORM lifecycle listeners that drive the adapter after bootstrap.
 *
 * - `storage` → the adapter's `sync` (the adapter debounces its own commit, so
 *   a burst of cross-tab progress writes collapses into a single commit —
 *   Req 5.6). Progress completion in the course writes the
 *   `skillhub_lesson_complete_*` keys, which fire this event.
 * - `pagehide` → the adapter's `end`, which sets `cmi.core.exit = suspend`,
 *   commits, then finishes, in that order (Req 5.5).
 *
 * Returns a disposer that removes both listeners, so a test (or a re-bootstrap)
 * can tear the wiring down cleanly.
 *
 * @param {ScormAdapter} adapter the wired adapter to drive.
 * @param {Window|object} [win=window] the host window (injectable for tests).
 * @returns {() => void} a disposer that unregisters the installed listeners.
 */
export function installListeners(adapter, win = typeof window !== "undefined" ? window : undefined) {
  if (!win || typeof win.addEventListener !== "function") {
    return NOOP;
  }

  const onStorage = () => {
    try {
      adapter.sync();
    } catch {
      // A sync fault must never break the host page.
    }
  };
  const onPageHide = () => {
    try {
      adapter.end();
    } catch {
      // The terminal sequence must never throw out of an unload handler.
    }
  };

  win.addEventListener("storage", onStorage);
  win.addEventListener("pagehide", onPageHide);

  return () => {
    try {
      win.removeEventListener("storage", onStorage);
      win.removeEventListener("pagehide", onPageHide);
    } catch {
      // Best-effort cleanup.
    }
  };
}

/**
 * Bootstrap the SCORM runtime: discover the LMS API, build the defensive
 * wrapper, initialize the session, construct the adapter from the injected
 * course deps, start it (which restores suspend_data before the course renders
 * — Req 5.4), and install the lifecycle listeners.
 *
 * `adapter.start()` is the sole restore step; the bootstrap deliberately does
 * not restore separately, so localStorage is repopulated exactly once.
 *
 * The whole sequence is defensive: a null API yields an inert wrapper and the
 * SCO continues standalone (Req 7.1).
 *
 * @param {Window|object} [win=window] the host window (injectable for tests).
 * @returns {{ wrapper: ScormApiWrapper, adapter: ScormAdapter, dispose: () => void }}
 *          the wired collaborators and a disposer for the installed listeners.
 */
export function bootstrap(win = typeof window !== "undefined" ? window : undefined) {
  const api = discoverApi(win);
  const wrapper = new ScormApiWrapper(api);
  wrapper.initialize();

  const deps = resolveCourseDeps(win);
  const adapter = new ScormAdapter(wrapper, bridge, deps);

  // start() restores from cmi.suspend_data via the bridge before syncing, so
  // the course picks up resumed progress on first paint — no separate restore.
  adapter.start();

  const dispose = installListeners(adapter, win);

  return { wrapper, adapter, dispose };
}

// Auto-run on DOMContentLoaded when loaded in a real browser document. Guarded
// so importing this module in a test environment does not self-install; a test
// drives `bootstrap` / `installListeners` directly against a mock window.
if (typeof document !== "undefined" && typeof document.addEventListener === "function") {
  document.addEventListener("DOMContentLoaded", () => {
    try {
      bootstrap();
    } catch {
      // Bootstrapping must never break the lesson page; standalone mode wins.
    }
  });
}
