# Requirements Document

## Introduction

SkillHub is a bilingual (English/French) static HTML training website that teaches users how to leverage the opcp-openstack-automation project for Infrastructure as Code (IaC). The site lives in a `skillhub/` subfolder at the project root and is hosted at `https://skillhub.ovhcloud.training`. It provides a structured learning path covering Terraform, OpenStack SDK, and Ansible deployment approaches with interactive code examples, copy-to-clipboard functionality, and progressive difficulty. The site uses pure HTML, CSS, and vanilla JavaScript with no server-side rendering or external runtime dependencies.

## Glossary

- **SkillHub_Site**: The complete static training website contained in the `skillhub/` directory
- **Language_Router**: The component (index.html + i18n.js) responsible for detecting user language preference and routing to the correct locale folder
- **Navigation_System**: The sidebar component (navigation.js) that renders lesson hierarchy, tracks progress, and highlights the current page
- **Code_Block_Manager**: The component (code-highlight.js) that enhances code blocks with syntax highlighting, copy-to-clipboard, and language labels
- **Page_Template**: The consistent HTML structure shared across all lesson pages including header, footer, sidebar, and content area
- **Locale**: A supported language identifier, either "en" (English) or "fr" (French)
- **Lesson**: A single training page covering a specific topic, identified by a unique slug
- **Progress**: The count and percentage of lessons a user has marked as complete, persisted in localStorage

## Requirements

### Requirement 1: Language Detection and Routing

**User Story:** As a visitor, I want the site to automatically detect my language preference and route me to the correct locale, so that I can read content in my preferred language without manual selection.

#### Acceptance Criteria

1. WHEN a user visits the root `skillhub/index.html` for the first time with no stored preference, THE Language_Router SHALL check the browser's `navigator.language` and redirect to the matching locale if supported
2. WHEN a user visits the root page and the browser language is not in the supported locales list, THE Language_Router SHALL redirect to the default locale ("en")
3. WHEN a user has a previously stored locale preference in localStorage, THE Language_Router SHALL redirect to the stored locale regardless of browser language
4. THE Language_Router SHALL support exactly two locales: "en" and "fr"
5. WHEN the Language_Router redirects a user, THE Language_Router SHALL persist the selected locale in localStorage under the key "skillhub-lang"

### Requirement 2: Language Switching

**User Story:** As a user, I want to switch between English and French on any page, so that I can read the same lesson content in my other preferred language.

#### Acceptance Criteria

1. WHEN a user clicks the language toggle on any lesson page, THE Language_Router SHALL navigate to the equivalent page in the target locale by replacing the locale segment in the URL path
2. WHEN a user switches language, THE Language_Router SHALL update the localStorage preference to the newly selected locale
3. WHEN a user switches from `en/{slug}.html` to French, THE Language_Router SHALL navigate to `fr/{slug}.html` preserving the same lesson page

### Requirement 3: Locale Content Parity

**User Story:** As a content maintainer, I want every English page to have a corresponding French page, so that users have a complete experience in both languages.

#### Acceptance Criteria

1. FOR ALL pages `en/{slug}.html` in the English locale folder, THE SkillHub_Site SHALL contain a corresponding `fr/{slug}.html` in the French locale folder
2. THE SkillHub_Site SHALL maintain the same lesson structure and ordering in both locale folders
3. IF a French translation is missing for a page during development, THEN THE Language_Router SHALL display a "translation pending" indicator on the language toggle and navigate to the French landing page instead of a broken link

### Requirement 4: Sidebar Navigation Rendering

**User Story:** As a learner, I want a sidebar navigation showing all lessons with my current position highlighted, so that I can easily navigate between topics and track where I am.

#### Acceptance Criteria

1. WHEN a lesson page loads, THE Navigation_System SHALL render a sidebar containing all lessons from the lesson catalog
2. WHEN rendering the sidebar, THE Navigation_System SHALL highlight exactly one navigation item as active, corresponding to the current page
3. WHEN rendering the sidebar, THE Navigation_System SHALL display localized lesson titles matching the current locale
4. THE Navigation_System SHALL display a difficulty badge (beginner, intermediate, advanced) next to each lesson title
5. WHEN the viewport width is less than 768px, THE Navigation_System SHALL collapse the sidebar into a hamburger menu
6. WHEN the viewport width is 768px or greater, THE Navigation_System SHALL display the sidebar as always visible

### Requirement 5: Learning Progress Tracking

**User Story:** As a learner, I want to mark lessons as complete and see my overall progress, so that I can track my learning journey across sessions.

#### Acceptance Criteria

1. WHEN a user marks a lesson as complete, THE Navigation_System SHALL store the lesson completion in localStorage
2. WHEN a lesson page loads, THE Navigation_System SHALL display a visual completion indicator on each completed lesson in the sidebar
3. THE Navigation_System SHALL display a progress bar in the header showing the percentage of completed lessons out of total lessons
4. WHEN a lesson is marked as complete, THE Navigation_System SHALL retain that completion status across page navigations and browser sessions until localStorage is cleared
5. WHEN calculating progress percentage, THE Navigation_System SHALL compute it as `completedCount / totalCount * 100` where totalCount equals the number of lessons in the catalog

### Requirement 6: Code Block Enhancement

**User Story:** As a learner, I want code examples to have syntax highlighting, language labels, and copy buttons, so that I can easily read and reuse code snippets.

#### Acceptance Criteria

1. WHEN a lesson page loads, THE Code_Block_Manager SHALL add a copy-to-clipboard button to every `<pre><code>` element on the page
2. WHEN a code block has a recognized language class (python, yaml, json, hcl, bash), THE Code_Block_Manager SHALL apply CSS-based syntax highlighting to that block
3. WHEN a code block has a recognized language class, THE Code_Block_Manager SHALL display a language label above the code block
4. WHEN a code block contains more than 5 lines, THE Code_Block_Manager SHALL add line numbers to that block
5. WHEN `initializeCodeBlocks()` is called multiple times on the same DOM, THE Code_Block_Manager SHALL produce the same result as calling it once, with no duplicate buttons or highlighting

### Requirement 7: Copy to Clipboard

**User Story:** As a learner, I want to copy code examples to my clipboard with one click, so that I can quickly use them in my own environment.

#### Acceptance Criteria

1. WHEN a user clicks a copy button on a code block, THE Code_Block_Manager SHALL copy the exact textContent of the associated `<code>` element to the clipboard
2. WHEN a copy operation succeeds, THE Code_Block_Manager SHALL display a "Copied!" confirmation on the button for 2 seconds before reverting to the original label
3. IF the Clipboard API is unavailable, THEN THE Code_Block_Manager SHALL fall back to selecting the text in the code block for manual copying
4. IF the Clipboard API is unavailable and fallback is used, THEN THE Code_Block_Manager SHALL display "Select + Ctrl+C" instead of "Copied!" on the button

### Requirement 8: Page Template and Layout

**User Story:** As a learner, I want a consistent page layout across all lessons with navigation aids, so that I can focus on learning without getting lost.

#### Acceptance Criteria

1. THE Page_Template SHALL include a header with the site logo, language toggle, and progress bar on every lesson page
2. THE Page_Template SHALL include breadcrumb navigation showing the current page location on every lesson page
3. THE Page_Template SHALL include previous/next lesson navigation buttons at the bottom of every lesson page
4. THE Page_Template SHALL include a footer with project links and license information on every lesson page
5. THE Page_Template SHALL use a responsive mobile-first CSS layout

### Requirement 9: Lesson Catalog Structure

**User Story:** As a learner, I want lessons organized in a progressive difficulty path with clear prerequisites, so that I can follow a structured learning journey.

#### Acceptance Criteria

1. THE SkillHub_Site SHALL provide exactly 10 lessons: intro, authentication, configuration, networking, security-groups, compute, volumes, deployment, terraform, and advanced
2. THE SkillHub_Site SHALL assign each lesson a difficulty level of beginner, intermediate, or advanced
3. THE SkillHub_Site SHALL define prerequisites for each lesson referencing existing lesson IDs
4. THE SkillHub_Site SHALL ensure no circular dependencies exist in the lesson prerequisite graph
5. THE SkillHub_Site SHALL assign a positive integer estimated time in minutes to each lesson

### Requirement 10: Error Handling — localStorage Unavailable

**User Story:** As a user with restricted browser settings, I want the site to work even without localStorage, so that I can still access all training content.

#### Acceptance Criteria

1. IF localStorage is unavailable, THEN THE Language_Router SHALL fall back to browser language detection only for locale selection
2. IF localStorage is unavailable, THEN THE Navigation_System SHALL display 0% progress but keep all lessons accessible
3. IF localStorage is unavailable, THEN THE SkillHub_Site SHALL remain fully functional for reading all lesson content

### Requirement 11: Error Handling — Invalid Locale in URL

**User Story:** As a user who manually edits the URL, I want to be guided back to a valid page, so that I do not encounter a broken experience.

#### Acceptance Criteria

1. IF a user navigates to an unsupported locale path (e.g., `/skillhub/de/`), THEN THE SkillHub_Site SHALL display a 404 page with links to the supported locales
2. THE SkillHub_Site SHALL include a custom `404.html` in the `skillhub/` directory that redirects users to the root language selector

### Requirement 12: Self-Contained Static Deployment

**User Story:** As a site operator, I want the site to have zero external runtime dependencies, so that it loads fast and works reliably without third-party CDN availability.

#### Acceptance Criteria

1. THE SkillHub_Site SHALL function with zero network requests to external CDNs or APIs after initial page load
2. THE SkillHub_Site SHALL contain all CSS, JavaScript, and image assets within the `skillhub/assets/` directory
3. THE SkillHub_Site SHALL use only vanilla JavaScript (ES6+) with no framework dependencies
4. THE SkillHub_Site SHALL target a total page weight under 200KB and First Contentful Paint under 1 second

### Requirement 13: Accessibility

**User Story:** As a user who relies on keyboard navigation or assistive technology, I want all interactive elements to be accessible, so that I can use the training site effectively.

#### Acceptance Criteria

1. THE SkillHub_Site SHALL make all interactive elements (buttons, links, toggles) keyboard-navigable
2. THE SkillHub_Site SHALL provide appropriate ARIA labels on all interactive elements
3. THE SkillHub_Site SHALL produce HTML that passes W3C HTML5 validation with zero errors for every page

### Requirement 14: Syntax Highlighting Support

**User Story:** As a learner working with multiple IaC tools, I want code blocks to support all relevant languages used in the project, so that I can clearly read examples for each tool.

#### Acceptance Criteria

1. THE Code_Block_Manager SHALL support syntax highlighting for Python, YAML, JSON, HCL (Terraform), and Bash languages
2. THE Code_Block_Manager SHALL use CSS-based syntax highlighting with no external library dependencies
