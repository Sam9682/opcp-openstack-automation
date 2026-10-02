/**
 * SkillHub — Navigation System
 *
 * Renders sidebar navigation from the lesson catalog, tracks learning
 * progress via localStorage, and handles the mobile hamburger menu.
 * Depends on window.SkillHub.lessons (lessons.js) and window.SkillHub.i18n (i18n.js).
 * Shared via the window.SkillHub namespace (no build tools).
 */
(function () {
  'use strict';

  /* Ensure namespace exists */
  window.SkillHub = window.SkillHub || {};

  var COMPLETED_KEY = 'skillhub-completed';

  /* ---- localStorage helpers (wrapped in try/catch) ---- */

  /**
   * Read the completed-lessons array from localStorage.
   * Returns an empty array when localStorage is unavailable or data is invalid.
   */
  function getCompletedLessons() {
    try {
      var raw = localStorage.getItem(COMPLETED_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          return parsed;
        }
      }
    } catch (e) {
      /* graceful degradation */
    }
    return [];
  }

  /**
   * Persist the completed-lessons array to localStorage.
   * Silently fails when localStorage is unavailable.
   */
  function saveCompletedLessons(arr) {
    try {
      localStorage.setItem(COMPLETED_KEY, JSON.stringify(arr));
    } catch (e) {
      /* graceful degradation */
    }
  }

  /* ---- Public API ---- */

  /**
   * Render the sidebar navigation.
   *
   * @param {string} locale  - Current locale ("en" or "fr").
   * @param {string} currentPath - window.location.pathname used to detect the active page.
   */
  function renderNavigation(locale, currentPath) {
    var lessons = window.SkillHub.lessons;
    if (!lessons || !lessons.length) {
      return;
    }

    var sidebarEl = document.getElementById('sidebar-nav');
    if (!sidebarEl) {
      return;
    }

    var completed = getCompletedLessons();
    var html = '<ul class="nav-list" role="list">';

    for (var i = 0; i < lessons.length; i++) {
      var lesson = lessons[i];

      /* Determine active state — match slug in the current path */
      var isActive = currentPath.indexOf('/' + lesson.slug + '.html') !== -1;
      /* Special case: the intro lesson uses index.html as its slug */
      if (lesson.slug === 'index') {
        /* Active when path ends with /index.html or with just the locale dir */
        var localeDir = '/' + locale + '/';
        isActive = currentPath.indexOf(localeDir + 'index.html') !== -1 ||
                   currentPath.replace(/\/$/, '').endsWith('/' + locale);
      }

      var isCompleted = completed.indexOf(lesson.id) !== -1;

      /* CSS classes */
      var classes = 'nav-item';
      if (isActive) { classes += ' active'; }
      if (isCompleted) { classes += ' completed'; }

      /* Localized title */
      var title = locale === 'fr' ? lesson.titleFR : lesson.titleEN;

      /* Difficulty badge */
      var badgeClass = 'badge badge-' + lesson.difficulty;
      var badge = '<span class="' + badgeClass + '">' + lesson.difficulty + '</span>';

      /* Build nav item */
      var href = lesson.slug + '.html';
      html += '<li class="' + classes + '" data-lesson-id="' + lesson.id + '">';
      html += '<a href="' + href + '" aria-label="' + title + ' — ' + lesson.difficulty + '">';
      html += '<span class="nav-title">' + title + '</span> ' + badge;
      html += '</a></li>';
    }

    html += '</ul>';
    sidebarEl.innerHTML = html;

    /* Update progress bar */
    var progress = getProgress();
    updateProgressBar(progress.percentage);
  }

  /**
   * Mark a lesson as complete.
   * Stores the lesson ID in localStorage and updates the sidebar UI.
   *
   * @param {string} lessonId - The lesson id (e.g. "auth", "compute").
   */
  function markLessonComplete(lessonId) {
    var completed = getCompletedLessons();
    if (completed.indexOf(lessonId) === -1) {
      completed.push(lessonId);
      saveCompletedLessons(completed);
    }

    /* Update visual indicator on the nav item */
    var navItem = document.querySelector('.nav-item[data-lesson-id="' + lessonId + '"]');
    if (navItem) {
      navItem.classList.add('completed');
    }

    /* Update progress bar */
    var progress = getProgress();
    updateProgressBar(progress.percentage);
  }

  /**
   * Get current learning progress.
   *
   * @returns {{ completedCount: number, totalCount: number, percentage: number }}
   */
  function getProgress() {
    var lessons = window.SkillHub.lessons || [];
    var totalCount = lessons.length;
    var completed = getCompletedLessons();

    /* Only count IDs that actually exist in the catalog */
    var completedCount = 0;
    for (var i = 0; i < lessons.length; i++) {
      if (completed.indexOf(lessons[i].id) !== -1) {
        completedCount++;
      }
    }

    var percentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

    return {
      completedCount: completedCount,
      totalCount: totalCount,
      percentage: percentage
    };
  }

  /**
   * Update the progress bar UI.
   *
   * @param {number} percentage - Progress percentage (0–100).
   */
  function updateProgressBar(percentage) {
    var fill = document.querySelector('.progress-bar-fill');
    if (fill) {
      fill.style.width = percentage + '%';
    }

    var text = document.querySelector('.progress-text');
    if (text) {
      text.textContent = Math.round(percentage) + '% complete';
    }
  }

  /* ---- Hamburger Menu Toggle ---- */

  /**
   * Wire up the hamburger button and sidebar overlay for mobile navigation.
   * Call once after DOM is ready.
   */
  function initHamburgerMenu() {
    var hamburgerBtn = document.querySelector('.hamburger-btn');
    var sidebar = document.querySelector('.sidebar');
    var overlay = document.querySelector('.sidebar-overlay');

    if (!hamburgerBtn || !sidebar) {
      return;
    }

    hamburgerBtn.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      var isOpen = sidebar.classList.contains('open');
      hamburgerBtn.setAttribute('aria-expanded', String(isOpen));
      if (overlay) {
        overlay.classList.toggle('visible');
      }
    });

    /* Close sidebar when overlay is clicked */
    if (overlay) {
      overlay.addEventListener('click', function () {
        sidebar.classList.remove('open');
        overlay.classList.remove('visible');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
      });
    }
  }

  /* ---- Expose on namespace ---- */
  window.SkillHub.navigation = {
    renderNavigation: renderNavigation,
    markLessonComplete: markLessonComplete,
    getProgress: getProgress,
    updateProgressBar: updateProgressBar,
    initHamburgerMenu: initHamburgerMenu
  };
})();
