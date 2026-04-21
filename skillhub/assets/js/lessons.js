/**
 * SkillHub — Lesson Catalog Data Module
 *
 * Defines the 10-lesson catalog used by navigation.js and i18n.js.
 * Shared via the window.SkillHub namespace (no build tools).
 */
(function () {
  'use strict';

  /* Ensure namespace exists */
  window.SkillHub = window.SkillHub || {};

  /**
   * Lesson catalog — ordered learning path.
   * Each entry: { id, slug, titleEN, titleFR, difficulty, estimatedMinutes, prerequisites }
   */
  var LESSONS = [
    {
      id: 'intro',
      slug: 'index',
      titleEN: 'Introduction',
      titleFR: 'Introduction',
      difficulty: 'beginner',
      estimatedMinutes: 5,
      prerequisites: []
    },
    {
      id: 'auth',
      slug: 'authentication',
      titleEN: 'Authentication',
      titleFR: 'Authentification',
      difficulty: 'beginner',
      estimatedMinutes: 15,
      prerequisites: ['intro']
    },
    {
      id: 'config',
      slug: 'configuration',
      titleEN: 'Configuration',
      titleFR: 'Configuration',
      difficulty: 'beginner',
      estimatedMinutes: 20,
      prerequisites: ['auth']
    },
    {
      id: 'network',
      slug: 'networking',
      titleEN: 'Networking',
      titleFR: 'Réseau',
      difficulty: 'intermediate',
      estimatedMinutes: 20,
      prerequisites: ['config']
    },
    {
      id: 'secgroup',
      slug: 'security-groups',
      titleEN: 'Security Groups',
      titleFR: 'Groupes de sécurité',
      difficulty: 'intermediate',
      estimatedMinutes: 20,
      prerequisites: ['config']
    },
    {
      id: 'compute',
      slug: 'compute',
      titleEN: 'Compute',
      titleFR: 'Calcul',
      difficulty: 'intermediate',
      estimatedMinutes: 25,
      prerequisites: ['network', 'secgroup']
    },
    {
      id: 'volumes',
      slug: 'volumes',
      titleEN: 'Volumes',
      titleFR: 'Volumes',
      difficulty: 'intermediate',
      estimatedMinutes: 20,
      prerequisites: ['compute']
    },
    {
      id: 'deploy',
      slug: 'deployment',
      titleEN: 'Deployment',
      titleFR: 'Déploiement',
      difficulty: 'advanced',
      estimatedMinutes: 30,
      prerequisites: ['network', 'secgroup', 'compute', 'volumes']
    },
    {
      id: 'terraform',
      slug: 'terraform',
      titleEN: 'Terraform',
      titleFR: 'Terraform',
      difficulty: 'intermediate',
      estimatedMinutes: 30,
      prerequisites: ['config']
    },
    {
      id: 'advanced',
      slug: 'advanced',
      titleEN: 'Advanced Topics',
      titleFR: 'Sujets avancés',
      difficulty: 'advanced',
      estimatedMinutes: 25,
      prerequisites: ['deploy', 'terraform']
    },
    {
      id: 'cleanup',
      slug: 'cleanup',
      titleEN: 'Cleanup',
      titleFR: 'Nettoyage',
      difficulty: 'beginner',
      estimatedMinutes: 15,
      prerequisites: ['advanced']
    }
  ];

  /* Expose on namespace */
  window.SkillHub.lessons = LESSONS;
})();
