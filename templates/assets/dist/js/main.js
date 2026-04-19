/**
 * Main JavaScript file for common functionality
 * Enhanced with advanced theme and layout management
 */

;(function () {
  'use strict'

  // Set assets path and layout path variables
  window.assetsPath = document.documentElement.getAttribute('data-assets-path')
  window.layoutPath = ''
  window.commonAssetsPath = ''

  const root = document.documentElement
  const layoutPath = 'free-landing-page'
  const localStorageKey = `${layoutPath}-theme`

  // Function to get current system theme preference
  const getSystemPreference = () => window.matchMedia('(prefers-color-scheme: dark)').matches

  // Function to resolve theme based on selected theme and layout configuration
  const resolveTheme = theme => {
    // Use more robust access pattern
    const layoutConfig = window.THEME_CONFIG && window.THEME_CONFIG[layoutPath] ? window.THEME_CONFIG[layoutPath] : null

    if (theme === 'system') {
      if (layoutConfig && layoutConfig.system) {
        const prefersDark = getSystemPreference()
        const resolvedTheme = prefersDark ? layoutConfig.system.dark : layoutConfig.system.light

        return resolvedTheme
      }
      // Fallback for layouts without system config - use layout's light/dark themes if available
      if (layoutConfig) {
        const prefersDark = getSystemPreference()
        const resolvedTheme = prefersDark ? layoutConfig.dark || 'dark' : layoutConfig.light || 'light'

        return resolvedTheme
      }
      // Final fallback if no layout config exists
      const resolvedTheme = getSystemPreference() ? 'dark' : 'light'

      return resolvedTheme
    }

    // Check if layout has theme mapping
    if (layoutConfig) {
      const resolvedTheme = layoutConfig[theme] || theme || layoutConfig.default || 'light'

      return resolvedTheme
    }

    return theme
  }

  // Apply selected theme and update dropdown UI
  const applyTheme = themeValue => {
    const finalTheme = resolveTheme(themeValue)
    root.setAttribute('data-theme', finalTheme)
    localStorage.setItem(localStorageKey, themeValue)

    // Update dropdown active state
    document.querySelectorAll('[data-theme-value]').forEach(btn => {
      const isActive = btn.getAttribute('data-theme-value') === themeValue
      btn.classList.toggle('dropdown-active', isActive)
      btn.setAttribute('aria-pressed', isActive)
    })

    // Toggle icon visibility
    const activeBtn = document.querySelector(`[data-theme-value="${themeValue}"]`)
    const iconName = activeBtn?.getAttribute('data-icon') || 'sun-moon'
    document.querySelectorAll('.theme-icon').forEach(iconEl => {
      if (iconEl.classList.contains(`icon-[tabler--${iconName}]`)) {
        iconEl.classList.remove('hidden')
      } else {
        iconEl.classList.add('hidden')
      }
    })
  }

  // Get saved theme or default to 'system'
  const savedTheme = localStorage.getItem(localStorageKey) || 'system'
  applyTheme(savedTheme)

  // Bind dropdown click handlers
  document.querySelectorAll('[data-theme-value]').forEach(btn => {
    btn.addEventListener('click', () => {
      const selectedTheme = btn.getAttribute('data-theme-value')
      applyTheme(selectedTheme)
    })
  })

  // Listen to system theme changes (live update if in 'system' mode)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    const currentTheme = localStorage.getItem(localStorageKey)
    if (currentTheme === 'system') {
      // Force recalculation of the system theme fallback
      applyTheme('system')
    }
  })
})()

// Scroll to top button
document.addEventListener('DOMContentLoaded', () => {
  const scrollToTopBtn = document.getElementById('scrollToTopBtn')
  // Only proceed if button exists
  if (scrollToTopBtn) {
    scrollToTopBtn.classList.add('hidden')

    scrollToTopBtn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })

    window.onscroll = function () {
      if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        scrollToTopBtn.classList.remove('hidden')
      } else {
        scrollToTopBtn.classList.add('hidden')
      }
    }
  }
})
