/* Site behaviour: mobile navigation and image fallbacks. */
(function () {
  'use strict';

  // Mobile navigation toggle.
  var toggle = document.getElementById('navToggle');
  var mobileNav = document.getElementById('mobileNav');

  if (toggle && mobileNav) {
    toggle.addEventListener('click', function () {
      mobileNav.classList.toggle('hidden');
    });

    mobileNav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        mobileNav.classList.add('hidden');
      });
    });
  }

  // Figures marked data-fallback show a placeholder when the image is missing.
  document.querySelectorAll('img[data-fallback]').forEach(function (img) {
    function showFallback() {
      var placeholder = img.nextElementSibling;
      img.style.display = 'none';
      if (placeholder) {
        placeholder.hidden = false;
      }
    }

    img.addEventListener('error', showFallback);

    // Catch images that already failed before this script ran.
    if (img.complete && img.naturalWidth === 0) {
      showFallback();
    }
  });
})();
