document.addEventListener('DOMContentLoaded', () => {
  function counter(id, start, end, duration, suffix = '') {
    let obj = document.getElementById(id),
      current = start,
      range = end - start,
      increment = end > start ? 1 : -1,
      step = Math.abs(Math.floor(duration / range)),
      timer = setInterval(() => {
        current += increment
        let formattedNumber = current

        // Check if the number is 1000 or more to add "k+" (for thousands)
        if (current >= 1000) {
          formattedNumber = (current / 1000).toFixed(1) + 'k' // Adding the "k" suffix
        }

        obj.textContent = formattedNumber + suffix
        if (current == end) {
          clearInterval(timer)
        }
      }, step)
  }

  counter('count1', 100, 7, 5000, '+')
  counter('count2', 100, 30, 5000, '+')
  counter('count3', 0, 500, 5000, '+')
  counter('count4', 100, 10, 5000, 'k+')
})
const sections = document.querySelectorAll('section')
const navLinks = document.querySelectorAll('.nav-link')

window.addEventListener('scroll', () => {
  let current = ''

  sections.forEach(section => {
    const sectionTop = section.offsetTop - 80 // Adjust for fixed navbar height
    if (scrollY >= sectionTop) {
      current = section.getAttribute('id')
    }
  })

  navLinks.forEach(link => {
    link.classList.remove('text-primary')
    if (link.getAttribute('href') === '#' + current) {
      link.classList.add('text-primary')
    }
  })
})

window.addEventListener('load', function () {
  // Basic
  flatpickr('.flatpickr-date', {
    monthSelectorType: 'static'
  })
})
