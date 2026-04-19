/**
 * Client-side Theme Utilities
 * Provides runtime theme management functionality
 */

;(function () {
  'use strict'

  // Ensure THEME_CONFIG is available globally
  if (typeof window.THEME_CONFIG === 'undefined') {
    console.warn('THEME_CONFIG not found. Theme functionality may be limited.')
    window.THEME_CONFIG = {}
  }

  /**
   * Get theme configuration for current layout
   * @param {string} layoutPath - Current layout path
   * @returns {object} Theme configuration or fallback
   */
  function getLayoutThemeConfig(layoutPath) {
    return (
      window.THEME_CONFIG[layoutPath] || {
        default: 'light',
        light: 'light',
        dark: 'dark',
        system: {
          light: 'light',
          dark: 'dark'
        }
      }
    )
  }

  /**
   * Resolve theme based on selection and layout
   * @param {string} selectedTheme - User selected theme
   * @param {string} layoutPath - Current layout path
   * @returns {string} Resolved theme name
   */
  function resolveTheme(selectedTheme, layoutPath) {
    const config = getLayoutThemeConfig(layoutPath)

    if (selectedTheme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      return prefersDark ? config.system.dark : config.system.light
    }

    return config[selectedTheme] || selectedTheme || config.default
  }

  // Export to window for global access
  window.ThemeUtils = {
    getLayoutThemeConfig,
    resolveTheme
  }
})()
