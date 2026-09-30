// SKINOLOGY CLINIC — lightweight interactions

(function () {
  'use strict';

  /* ---- Mobile navigation ---- */
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');

  if (toggle && links) {
    toggle.addEventListener('click', function () {
      links.classList.toggle('open');
    });
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') links.classList.remove('open');
    });
  }

  /* ---- Lazy video embed (YouTube / MP4 added later) ---- */
  var videoFrame = document.querySelector('.video-frame');
  if (videoFrame) {
    videoFrame.addEventListener('click', function () {
      var embed = videoFrame.getAttribute('data-embed');
      if (embed && embed.indexOf('VIDEO_ID') === -1) {
        videoFrame.innerHTML = embed;
      }
    });
  }

  /* ---- Treatment videos: fit 9:16 / 16:9, drop cards that can't play ---- */
  var tvSection = document.getElementById('treatment-videos');
  if (tvSection) {
    tvSection.querySelectorAll('.tv-card video').forEach(function (video) {
      var card = video.closest('.tv-card');
      function fit() {
        if (video.videoWidth && video.videoHeight) {
          // Frame takes the video's exact shape, so nothing is cropped or letterboxed.
          video.parentNode.style.aspectRatio = video.videoWidth + ' / ' + video.videoHeight;
          card.classList.toggle('is-portrait', video.videoHeight > video.videoWidth);
        }
      }
      function drop() {
        card.remove();
        if (!tvSection.querySelector('.tv-card')) tvSection.remove();
      }
      if (video.readyState >= 1) fit();
      video.addEventListener('loadedmetadata', fit);
      video.addEventListener('error', drop);
      if (video.error) drop();
    });
  }

  /* ---- Subtle scroll reveal (progressive enhancement) ---- */
  var revealables = document.querySelectorAll('[data-reveal]');
  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!revealables.length) return;

  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealables.forEach(function (el) { el.classList.add('is-visible'); });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  revealables.forEach(function (el) { observer.observe(el); });
})();
