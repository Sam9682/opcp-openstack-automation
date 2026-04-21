/**
 * SkillHub — Main Initialization Script
 *
 * Entry point that wires up all modules on DOMContentLoaded:
 * navigation, code highlighting, language toggle, breadcrumbs,
 * prev/next buttons, hamburger menu, and mark-complete button.
 *
 * Depends on:
 *   - window.SkillHub.lessons   (lessons.js)
 *   - window.SkillHub.i18n      (i18n.js)
 *   - window.SkillHub.navigation (navigation.js)
 *   - window.SkillHub.codeHighlight (code-highlight.js)
 */
(function () {
  'use strict';

  /* ---- Helper: get current lesson ID from path ---- */

  /**
   * Match the current URL path slug to a lesson in the catalog.
   *
   * @param {string} currentPath - window.location.pathname
   * @returns {object|null} The matching lesson object, or null.
   */
  function getCurrentLessonId(currentPath) {
    var lessons = window.SkillHub.lessons || [];
    for (var i = 0; i < lessons.length; i++) {
      var lesson = lessons[i];
      if (currentPath.indexOf('/' + lesson.slug + '.html') !== -1) {
        return lesson;
      }
      /* Special case: intro lesson uses index.html */
      if (lesson.slug === 'index') {
        if (currentPath.indexOf('/index.html') !== -1 ||
            /\/(?:en|fr)\/?$/.test(currentPath)) {
          return lesson;
        }
      }
    }
    return null;
  }

  /* ---- Helper: render breadcrumbs ---- */

  /**
   * Build breadcrumbs: Home > Current Lesson.
   *
   * @param {string} locale - Current locale ("en" or "fr").
   * @param {string} currentPath - window.location.pathname.
   */
  function renderBreadcrumbs(locale, currentPath) {
    var container = document.querySelector('.breadcrumbs');
    if (!container) { return; }

    var homeLabel = locale === 'fr' ? 'Accueil' : 'Home';
    var lesson = getCurrentLessonId(currentPath);
    var lessonTitle = '';

    if (lesson) {
      lessonTitle = locale === 'fr' ? lesson.titleFR : lesson.titleEN;
    }

    var html = '<a href="index.html">' + homeLabel + '</a>';
    if (lessonTitle && lesson && lesson.slug !== 'index') {
      html += '<span class="separator">›</span>';
      html += '<span>' + lessonTitle + '</span>';
    }

    container.innerHTML = html;
  }

  /* ---- Helper: render prev/next buttons ---- */

  /**
   * Build previous / next lesson navigation links.
   *
   * @param {string} locale - Current locale ("en" or "fr").
   * @param {string} currentPath - window.location.pathname.
   */
  function renderPrevNextButtons(locale, currentPath) {
    var container = document.querySelector('.prev-next-nav');
    if (!container) { return; }

    var lessons = window.SkillHub.lessons || [];
    var currentLesson = getCurrentLessonId(currentPath);
    if (!currentLesson) { return; }

    var currentIndex = -1;
    for (var i = 0; i < lessons.length; i++) {
      if (lessons[i].id === currentLesson.id) {
        currentIndex = i;
        break;
      }
    }

    if (currentIndex === -1) { return; }

    var prevLabel = locale === 'fr' ? '← Précédent' : '← Previous';
    var nextLabel = locale === 'fr' ? 'Suivant →' : 'Next →';
    var html = '';

    if (currentIndex > 0) {
      var prev = lessons[currentIndex - 1];
      var prevTitle = locale === 'fr' ? prev.titleFR : prev.titleEN;
      html += '<a href="' + prev.slug + '.html" aria-label="' + prevLabel + ': ' + prevTitle + '">' + prevLabel + '</a>';
    } else {
      html += '<span></span>';
    }

    if (currentIndex < lessons.length - 1) {
      var next = lessons[currentIndex + 1];
      var nextTitle = locale === 'fr' ? next.titleFR : next.titleEN;
      html += '<a href="' + next.slug + '.html" aria-label="' + nextLabel + ': ' + nextTitle + '">' + nextLabel + '</a>';
    } else {
      html += '<span></span>';
    }

    container.innerHTML = html;
  }

  /* ---- DOMContentLoaded ---- */

  document.addEventListener('DOMContentLoaded', function () {
    var locale = window.SkillHub.i18n.getCurrentLocale();
    var currentPath = window.location.pathname;

    /* 1. Sidebar navigation */
    window.SkillHub.navigation.renderNavigation(locale, currentPath);

    /* 2. Code block enhancements */
    window.SkillHub.codeHighlight.initializeCodeBlocks();

    /* 3. Language toggle */
    window.SkillHub.i18n.renderLanguageToggle(locale);

    /* 4. Breadcrumbs */
    renderBreadcrumbs(locale, currentPath);

    /* 5. Prev / Next buttons */
    renderPrevNextButtons(locale, currentPath);

    /* 6. Hamburger menu */
    window.SkillHub.navigation.initHamburgerMenu();

    /* 7. Mark-complete button */
    var completeBtn = document.querySelector('.mark-complete-btn');
    if (completeBtn) {
      var lesson = getCurrentLessonId(currentPath);
      if (lesson) {
        /* Check if already completed */
        var completedLessons = [];
        try {
          var raw = localStorage.getItem('skillhub-completed');
          if (raw) { completedLessons = JSON.parse(raw) || []; }
        } catch (e) { /* noop */ }

        if (completedLessons.indexOf(lesson.id) !== -1) {
          completeBtn.textContent = locale === 'fr' ? '✓ Terminé' : '✓ Completed';
          completeBtn.classList.add('completed');
          completeBtn.setAttribute('disabled', 'true');
        }

        completeBtn.addEventListener('click', function () {
          if (completeBtn.classList.contains('completed')) { return; }
          window.SkillHub.navigation.markLessonComplete(lesson.id);
          completeBtn.textContent = locale === 'fr' ? '✓ Terminé' : '✓ Completed';
          completeBtn.classList.add('completed');
          completeBtn.setAttribute('disabled', 'true');
        });
      }
    }
  });
})();
