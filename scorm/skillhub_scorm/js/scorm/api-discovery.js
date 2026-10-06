/**
 * Api_Discovery — locates the LMS SCORM 1.2 API object.
 *
 * The SCORM 1.2 API is exposed by an ancestor (or opener) window as a global
 * named `API` that implements `LMSInitialize`. Because the SCO may be nested in
 * frames owned by the LMS — potentially on a different origin — every window
 * access is wrapped in try/catch: a cross-origin SecurityError must not abort
 * the search, it simply means that window is not ours and we move on.
 *
 * Pure, dependency-free ES module.
 *
 * Requirements: 6.1, 6.2, 6.3, 6.4
 */

/** Maximum number of windows to traverse in either the parent or opener chain. */
export const MAX_DEPTH = 20;

/**
 * Decide whether a given window hosts the LMS SCORM 1.2 API.
 *
 * A window hosts the API when it exposes an `API` object carrying an
 * `LMSInitialize` function. The access itself can throw on a cross-origin
 * window, so the caller is responsible for wrapping this in try/catch.
 *
 * @param {Window} win
 * @returns {object|null} the API object, or null when absent
 */
function apiOnWindow(win) {
  if (win && win.API && typeof win.API.LMSInitialize === "function") {
    return win.API;
  }
  return null;
}

/**
 * Walk the `.parent` chain starting at `startWin`, up to `MAX_DEPTH` windows,
 * returning the LMS `API` object as soon as it is found.
 *
 * Each window access is guarded so a cross-origin access error does not
 * terminate the search — traversal continues to the next window. The walk also
 * stops once a window is its own parent (the top of the chain).
 *
 * @param {Window} startWin
 * @returns {object|null} the LMS API object, or null when not found
 */
export function findApiInChain(startWin) {
  let win = startWin;
  let depth = 0;

  while (win && depth < MAX_DEPTH) {
    try {
      const api = apiOnWindow(win);
      if (api) {
        return api;
      }
    } catch (_err) {
      // Cross-origin access raised — this window is not reachable; keep going.
    }

    let parent = null;
    try {
      // A window at the top of the chain is its own parent; detect and stop.
      if (win.parent && win.parent !== win) {
        parent = win.parent;
      }
    } catch (_err) {
      // Reading `.parent` can also throw cross-origin; treat as end of chain.
      parent = null;
    }

    if (!parent) {
      break;
    }
    win = parent;
    depth += 1;
  }

  return null;
}

/**
 * Discover the LMS API by searching the parent chain first, then the opener
 * chain, each bounded by `MAX_DEPTH`.
 *
 * @param {Window} [win=window] the window from which to start the search
 * @returns {object|null} the LMS API object, or null when found in neither chain
 */
export function discoverApi(win = window) {
  // 1. Parent chain.
  const fromParent = findApiInChain(win);
  if (fromParent) {
    return fromParent;
  }

  // 2. Opener chain. Reading `.opener` can throw cross-origin, so guard it.
  let opener = null;
  try {
    if (win && win.opener && win.opener !== win) {
      opener = win.opener;
    }
  } catch (_err) {
    opener = null;
  }

  if (opener) {
    const fromOpener = findApiInChain(opener);
    if (fromOpener) {
      return fromOpener;
    }
  }

  // 3. Found in neither chain.
  return null;
}
