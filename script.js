(() => {
  const story = document.querySelector(".app-story");
  const storyVisual = document.querySelector(".story-visual");
  const stage = document.querySelector(".app-stage");
  const screens = Array.from(document.querySelectorAll(".screen-layer"));
  const chapters = Array.from(document.querySelectorAll(".chapter"));
  const notes = Array.from(document.querySelectorAll(".stage-note"));
  const heroVisual = document.querySelector(".hero-visual");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const mobileLayout = window.matchMedia("(max-width: 900px)");

  const noteMotion = [
    { fromX: -0.52, fromY: -0.3, toX: -0.36, toY: -0.18, rotate: -3 },
    { fromX: 0.56, fromY: -0.54, toX: 0.37, toY: -0.35, rotate: 3 },
    { fromX: 0.62, fromY: 0.06, toX: 0.42, toY: 0.02, rotate: -2 },
    { fromX: -0.58, fromY: 0.5, toX: -0.38, toY: 0.34, rotate: 4 },
    { fromX: 0.54, fromY: 0.58, toX: 0.36, toY: 0.4, rotate: 2 },
  ];

  const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
  const lerp = (from, to, amount) => from + (to - from) * amount;
  const easeOutCubic = (value) => 1 - Math.pow(1 - value, 3);

  let ticking = false;

  function chapterProgress(chapter, viewportHeight) {
    const rect = chapter.getBoundingClientRect();
    const start = viewportHeight * 0.82;
    const distance = viewportHeight * 0.58;
    return clamp((start - rect.top) / distance);
  }

  function pickActiveChapter(viewportHeight) {
    const pivot = viewportHeight * (mobileLayout.matches ? 0.78 : 0.5);
    let activeIndex = 0;
    let activeDistance = Infinity;

    chapters.forEach((chapter, index) => {
      const rect = chapter.getBoundingClientRect();
      const mid = rect.top + rect.height * 0.5;
      const distance = Math.abs(mid - pivot);

      if (distance < activeDistance) {
        activeDistance = distance;
        activeIndex = index;
      }
    });

    return activeIndex;
  }

  function mobileFadeUnderStage(chapter) {
    if (!storyVisual) return 1;

    const rect = chapter.getBoundingClientRect();
    const stageEdge = storyVisual.getBoundingClientRect().bottom;

    if (rect.bottom <= stageEdge) return 0.2;
    if (rect.top >= stageEdge) return 1;

    return clamp((rect.bottom - stageEdge) / rect.height, 0.2, 1);
  }

  function updateScreens(activeIndex) {
    screens.forEach((screen, index) => {
      const isActive = index === activeIndex;
      const isBefore = index < activeIndex;

      screen.classList.toggle("is-active", isActive);
      screen.classList.toggle("is-before", isBefore);
      screen.style.zIndex = String(10 + index);
    });
  }

  function storyExitFade(viewportHeight) {
    if (!story) return 1;

    const bottom = story.getBoundingClientRect().bottom;
    return clamp((bottom - viewportHeight * 0.26) / (viewportHeight * 0.5));
  }

  function updateNotes(viewportHeight, activeIndex, exitFade) {
    const stageSize = stage?.clientWidth || 1;

    notes.forEach((note, index) => {
      const motion = noteMotion[index];
      const chapter = chapters[index];

      if (!motion || !chapter || mobileLayout.matches) {
        note.style.opacity = "0";
        return;
      }

      const rawProgress = chapterProgress(chapter, viewportHeight);
      const eased = reducedMotion ? 1 : easeOutCubic(rawProgress);
      const x = lerp(motion.fromX, motion.toX, eased) * stageSize;
      const y = lerp(motion.fromY, motion.toY, eased) * stageSize;
      const scale = lerp(0.82, 1, eased);
      const baseOpacity = index <= activeIndex ? 1 : rawProgress;
      const oldOpacity = index < activeIndex ? 0.08 : baseOpacity;
      const opacity = clamp(oldOpacity) * exitFade;

      note.style.opacity = opacity.toFixed(3);
      note.style.transform = `translate(-50%, -50%) translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) scale(${scale.toFixed(3)}) rotate(${motion.rotate.toFixed(2)}deg)`;
    });
  }

  function updateChapters(activeIndex) {
    chapters.forEach((chapter, index) => {
      chapter.classList.toggle("is-active", index === activeIndex);
      chapter.classList.toggle("is-before", index < activeIndex);

      if (mobileLayout.matches) {
        chapter.style.opacity = mobileFadeUnderStage(chapter).toFixed(3);
      } else if (chapter.style.opacity) {
        chapter.style.opacity = "";
      }
    });
  }

  function updateStoryProgress(viewportHeight) {
    if (!story) return;

    const rect = story.getBoundingClientRect();
    const progress = clamp((viewportHeight - rect.top) / (rect.height + viewportHeight));
    story.style.setProperty("--story-progress", progress.toFixed(3));

    if (stage && !reducedMotion) {
      const stageShift = lerp(24, -24, progress);
      stage.style.setProperty("--stage-y", `${stageShift.toFixed(1)}px`);
    }
  }

  function updateHero() {
    if (!heroVisual || reducedMotion) return;

    const shift = clamp(window.scrollY / 720) * -48;
    heroVisual.style.setProperty("--hero-y", `${shift.toFixed(1)}px`);
  }

  function render() {
    ticking = false;

    const viewportHeight = window.innerHeight || 1;
    const activeIndex = pickActiveChapter(viewportHeight);

    updateScreens(activeIndex);
    updateNotes(viewportHeight, activeIndex, storyExitFade(viewportHeight));
    updateChapters(activeIndex);
    updateStoryProgress(viewportHeight);
    updateHero();
  }

  function requestRender() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(render);
  }

  render();
  window.addEventListener("scroll", requestRender, { passive: true });
  window.addEventListener("resize", requestRender);
  mobileLayout.addEventListener?.("change", requestRender);

  window.addEventListener("load", () => {
    render();
  });
})();
