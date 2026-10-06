/*
 * The scroll sequence, for browsers without scroll-driven CSS animations.
 *
 * Where `animation-timeline: view()` exists, the CSS already does this and this
 * file deliberately stays out of the way — it only marks the container as
 * enhanced and lets the stylesheet decide which mechanism wins.
 *
 * Everywhere else, one IntersectionObserver watches the six steps and sets a
 * single attribute on the matching screen. No scroll handler, no rAF loop, no
 * measurement: the observer fires off the main thread's layout work rather than
 * forcing it, so nothing here reads geometry per frame.
 *
 * With this file absent or blocked, the page still works. The stylesheet's base
 * state shows every screen in order, which is the no-JavaScript answer.
 */
(function () {
  'use strict';

  var seq = document.querySelector('[data-sequence]');
  if (!seq) return;

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduce && reduce.matches) return; // the static sequence is the whole point

  if (!('IntersectionObserver' in window)) return; // stacked fallback stands

  var steps = Array.prototype.slice.call(seq.querySelectorAll('.step'));
  var screens = Array.prototype.slice.call(seq.querySelectorAll('.screen'));
  if (steps.length === 0 || steps.length !== screens.length) return;

  seq.setAttribute('data-enhanced', '');

  function show(index) {
    for (var i = 0; i < screens.length; i++) {
      if (i === index) screens[i].setAttribute('data-visible', '');
      else screens[i].removeAttribute('data-visible');
    }
  }

  // The first screen is correct before any scrolling has happened.
  show(0);

  var ratios = new Array(steps.length).fill(0);

  var io = new IntersectionObserver(
    function (entries) {
      for (var i = 0; i < entries.length; i++) {
        var idx = steps.indexOf(entries[i].target);
        if (idx !== -1) ratios[idx] = entries[i].intersectionRatio;
      }
      // Whichever step is most in view owns the phone. Ties go to the earlier
      // one, so scrolling back up lands on the same screen it came from.
      var best = 0;
      var bestRatio = -1;
      for (var j = 0; j < ratios.length; j++) {
        if (ratios[j] > bestRatio + 0.001) {
          bestRatio = ratios[j];
          best = j;
        }
      }
      if (bestRatio > 0) show(best);
    },
    {
      // A band through the middle of the viewport: a step "owns" the phone while
      // it is the thing being read, not while it is entering or leaving.
      rootMargin: '-35% 0px -35% 0px',
      threshold: [0, 0.25, 0.5, 0.75, 1]
    }
  );

  for (var k = 0; k < steps.length; k++) io.observe(steps[k]);
})();
