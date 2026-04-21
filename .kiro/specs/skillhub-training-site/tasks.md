# Implementation Plan: SkillHub Training Site

## Overview

Build a bilingual (EN/FR) static HTML training website in a `skillhub/` subfolder that teaches users how to use the opcp-openstack-automation project for Infrastructure as Code. The site uses vanilla JavaScript (ES6+), CSS3, and HTML5 with no external dependencies. Implementation language: HTML/CSS/JavaScript.

## Tasks

- [x] 1. Set up project structure and shared assets foundation
  - [x] 1.1 Create the `skillhub/` directory structure with `en/`, `fr/`, and `assets/` folders
    - Create `skillhub/assets/css/`, `skillhub/assets/js/`, `skillhub/assets/images/`
    - Create `skillhub/en/` and `skillhub/fr/` locale folders
    - _Requirements: 12.2, 12.3_

  - [x] 1.2 Create the base CSS stylesheet (`skillhub/assets/css/style.css`)
    - Implement mobile-first responsive layout with sidebar, header, content area, and footer
    - Add CSS-based syntax highlighting rules for Python, YAML, JSON, HCL, and Bash
    - Include styles for navigation items, difficulty badges, progress bar, breadcrumbs, copy buttons, and language toggle
    - Responsive breakpoint at 768px: sidebar collapses to hamburger menu below, always visible at or above
    - _Requirements: 4.5, 4.6, 6.2, 8.5, 14.1, 14.2_

  - [x] 1.3 Create the lesson catalog data module (`skillhub/assets/js/lessons.js`)
    - Define the 10-lesson catalog as a JS data structure with id, slug, titleEN, titleFR, difficulty, estimatedMinutes, and prerequisites
    - Lessons: intro, authentication, configuration, networking, security-groups, compute, volumes, deployment, terraform, advanced
    - Export the catalog for use by navigation.js and i18n.js
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 2. Implement Language Router (i18n.js) and root index.html
  - [x] 2.1 Create the Language Router module (`skillhub/assets/js/i18n.js`)
    - Implement `detectLocale()`: check localStorage ("skillhub-lang"), then `navigator.language`, fall back to "en"
    - Implement `switchLanguage(targetLocale)`: replace locale segment in URL path, persist to localStorage, navigate
    - Implement `getCurrentLocale()`: extract locale from current URL path
    - Wrap localStorage access in try/catch for graceful degradation when unavailable
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 10.1_

  - [x] 2.2 Create the root language selector page (`skillhub/index.html`)
    - On load, call `detectLocale()` and redirect to the appropriate locale landing page
    - Include manual language selection links as fallback (EN / FR buttons)
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 2.3 Write property tests for Language Router (fast-check)
    - **Property 1: Locale Detection Always Returns a Valid Supported Locale**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.5**

  - [ ]* 2.4 Write property tests for Language Switch (fast-check)
    - **Property 2: Language Switch Preserves Page and Persists Preference**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 3. Implement Navigation System (navigation.js) and progress tracking
  - [x] 3.1 Create the Navigation System module (`skillhub/assets/js/navigation.js`)
    - Implement `renderNavigation(locale, currentPath)`: build sidebar HTML from lesson catalog, highlight active page, show difficulty badges, show localized titles
    - Implement `markLessonComplete(lessonId)`: store completion in localStorage, update visual indicator
    - Implement `getProgress()`: return `{completedCount, totalCount, percentage}` computed as `completedCount / totalCount * 100`
    - Implement hamburger menu toggle for viewports < 768px
    - Wrap localStorage access in try/catch; show 0% progress when unavailable
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 10.2_

  - [ ]* 3.2 Write property tests for Navigation rendering (fast-check)
    - **Property 4: Sidebar Renders Exactly One Active Item**
    - **Validates: Requirements 4.1, 4.2**

  - [ ]* 3.3 Write property tests for locale titles and difficulty badges (fast-check)
    - **Property 5: Sidebar Items Have Correct Locale Titles and Difficulty Badges**
    - **Validates: Requirements 4.3, 4.4, 9.2**

  - [ ]* 3.4 Write property tests for progress tracking (fast-check)
    - **Property 6: Progress Tracking Round-Trip**
    - **Validates: Requirements 5.1, 5.4**

  - [ ]* 3.5 Write property tests for progress percentage calculation (fast-check)
    - **Property 7: Progress Percentage Calculation**
    - **Validates: Requirements 5.3, 5.5**

- [x] 4. Implement Code Block Manager (code-highlight.js)
  - [x] 4.1 Create the Code Block Manager module (`skillhub/assets/js/code-highlight.js`)
    - Implement `initializeCodeBlocks()`: find all `<pre><code>` elements, apply syntax highlighting, add copy buttons, add language labels, add line numbers for blocks > 5 lines
    - Implement `copyToClipboard(codeBlockId)`: copy `textContent` of `<code>` element to clipboard via Clipboard API; show "Copied!" for 2 seconds; fall back to text selection with "Select + Ctrl+C" message if Clipboard API unavailable
    - Implement `highlightSyntax(element, language)`: apply CSS classes for Python, YAML, JSON, HCL, Bash token types
    - Ensure idempotency: guard against duplicate buttons/highlighting on repeated calls
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 14.1, 14.2_

  - [ ]* 4.2 Write property tests for code block initialization (fast-check)
    - **Property 8: Code Block Initialization Enhancements**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

  - [ ]* 4.3 Write property tests for idempotency (fast-check)
    - **Property 9: Code Block Initialization Idempotency**
    - **Validates: Requirement 6.5**

  - [ ]* 4.4 Write property tests for copy fidelity (fast-check)
    - **Property 10: Copy Fidelity**
    - **Validates: Requirement 7.1**

- [x] 5. Checkpoint — Core JS modules complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create the main entry point script and page template
  - [x] 6.1 Create the main initialization script (`skillhub/assets/js/main.js`)
    - On DOMContentLoaded: call `renderNavigation()`, `initializeCodeBlocks()`, render language toggle, render breadcrumbs, render prev/next buttons
    - Wire up "Mark as Complete" button to `markLessonComplete()` and update progress bar
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 6.2 Create the English landing page (`skillhub/en/index.html`)
    - Include full page template: header (logo, language toggle, progress bar), sidebar navigation, breadcrumbs, main content area with intro lesson content, prev/next buttons, footer with project links and license
    - Add ARIA labels on all interactive elements (buttons, links, toggles)
    - Use semantic HTML5 elements; ensure keyboard navigability
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 13.1, 13.2, 13.3_

  - [x] 6.3 Create the French landing page (`skillhub/fr/index.html`)
    - Mirror the English landing page structure with French-translated content
    - _Requirements: 3.1, 3.2_

- [x] 7. Create all English lesson pages
  - [x] 7.1 Create `skillhub/en/authentication.html` — Authentication lesson
    - Include code examples from `openstack_sdk/auth_manager.py` usage (env vars, file-based, ConnectionManager, context manager)
    - Use `<pre><code class="language-python">` and `<pre><code class="language-bash">` blocks
    - Include page template elements: header, sidebar, breadcrumbs, prev/next, footer
    - Add ARIA labels on interactive elements
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.2 Create `skillhub/en/configuration.html` — Configuration lesson
    - Include YAML and JSON config examples from `examples/config.yaml` and `examples/minimal-config.yaml`
    - Use `<pre><code class="language-yaml">` and `<pre><code class="language-json">` blocks
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.3 Create `skillhub/en/networking.html` — Networking lesson
    - Include network creation examples from OpenStack SDK and Terraform
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.4 Create `skillhub/en/security-groups.html` — Security Groups lesson
    - Include security group creation examples from OpenStack SDK and Terraform
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.5 Create `skillhub/en/compute.html` — Compute lesson
    - Include compute instance examples from OpenStack SDK and Terraform
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.6 Create `skillhub/en/volumes.html` — Volumes lesson
    - Include volume creation and attachment examples
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.7 Create `skillhub/en/deployment.html` — Deployment Engine lesson
    - Include full deployment orchestration examples
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.8 Create `skillhub/en/terraform.html` — Terraform lesson
    - Include HCL code examples from `terraform/main.tf`, `terraform/variables.tf`
    - Use `<pre><code class="language-hcl">` blocks
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

  - [x] 7.9 Create `skillhub/en/advanced.html` — Advanced Topics lesson
    - Cover advanced patterns: multi-region, CI/CD integration, custom modules
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 13.1, 13.2_

- [x] 8. Checkpoint — English content complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Create all French lesson pages
  - [x] 9.1 Create `skillhub/fr/authentication.html` — French translation of authentication lesson
    - Mirror English structure and code examples with French prose
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.2 Create `skillhub/fr/configuration.html` — French translation of configuration lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.3 Create `skillhub/fr/networking.html` — French translation of networking lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.4 Create `skillhub/fr/security-groups.html` — French translation of security groups lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.5 Create `skillhub/fr/compute.html` — French translation of compute lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.6 Create `skillhub/fr/volumes.html` — French translation of volumes lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.7 Create `skillhub/fr/deployment.html` — French translation of deployment lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.8 Create `skillhub/fr/terraform.html` — French translation of terraform lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [x] 9.9 Create `skillhub/fr/advanced.html` — French translation of advanced lesson
    - _Requirements: 3.1, 3.2, 8.1, 8.2, 8.3, 8.4, 13.1, 13.2_

  - [ ]* 9.10 Write integration test for locale content parity
    - **Property 3: Locale Content Parity**
    - Script that verifies every `en/{slug}.html` has a corresponding `fr/{slug}.html`
    - **Validates: Requirements 3.1, 3.2**

- [x] 10. Create error handling pages and missing translation fallback
  - [x] 10.1 Create custom 404 page (`skillhub/404.html`)
    - Display friendly error message with links to both EN and FR landing pages
    - Include redirect logic to root language selector
    - _Requirements: 11.1, 11.2_

  - [x] 10.2 Implement missing translation fallback in i18n.js
    - When switching to a locale where the target page doesn't exist, show "translation pending" indicator and navigate to that locale's landing page instead
    - _Requirements: 3.3_

- [x] 11. Accessibility and validation pass
  - [x] 11.1 Audit and add ARIA labels to all interactive elements across all pages
    - Ensure all buttons, links, toggles, and inputs have `aria-label` or `aria-labelledby`
    - Ensure all elements are keyboard-navigable (tab order, focus styles)
    - _Requirements: 13.1, 13.2, 13.3_

  - [ ]* 11.2 Write property tests for ARIA labels (fast-check)
    - **Property 14: ARIA Labels on Interactive Elements**
    - **Validates: Requirement 13.2**

  - [ ]* 11.3 Write property tests for page template structural completeness (fast-check)
    - **Property 11: Page Template Structural Completeness**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

  - [ ]* 11.4 Write integration test for no external dependencies
    - **Property 13: No External Runtime Dependencies**
    - Script that scans all HTML/CSS/JS files for external CDN URLs or API endpoints
    - **Validates: Requirements 12.1, 12.2**

  - [ ]* 11.5 Write integration test for lesson catalog validity
    - **Property 12: Lesson Catalog Validity**
    - Verify no circular dependencies, all prerequisites reference existing lessons, all difficulties valid, all estimated times positive
    - **Validates: Requirements 9.2, 9.3, 9.5**

- [x] 12. Final checkpoint — Full site complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests use fast-check (JavaScript) as specified in the design
- All code examples in lesson pages should use placeholder credentials (`${OS_USERNAME}`, etc.), never real values
- The site must function with zero external CDN or API requests after page load
- Target: total page weight < 200KB, First Contentful Paint < 1 second
