/* AutoLifecycle Predictor — JavaScript */

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss alerts after 5 seconds ─────────────────────
  document.querySelectorAll('.alp-alert').forEach(function (alert) {
    setTimeout(function () {
      var bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // ── Smooth scroll for anchor links ──────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Animate progress bars on scroll ─────────────────────────
  var progressBars = document.querySelectorAll('.alp-progress-bar[data-width]');
  if (progressBars.length > 0) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.width = entry.target.getAttribute('data-width') + '%';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });

    progressBars.forEach(function (bar) {
      bar.style.width = '0%';
      observer.observe(bar);
    });
  }

  // ── Animate stat values ──────────────────────────────────────
  document.querySelectorAll('.stat-value[data-count]').forEach(function (el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    var duration = 1200;
    var start = null;
    var prefix = el.getAttribute('data-prefix') || '';
    var suffix = el.getAttribute('data-suffix') || '';

    function step(timestamp) {
      if (!start) start = timestamp;
      var progress = Math.min((timestamp - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = prefix + Math.round(eased * target).toLocaleString() + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }

    var obs = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) {
        requestAnimationFrame(step);
        obs.unobserve(el);
      }
    });
    obs.observe(el);
  });

  // ── Confirm delete dialogues ─────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(this.getAttribute('data-confirm'))) {
        e.preventDefault();
      }
    });
  });

  // ── Form validation feedback ─────────────────────────────────
  var forms = document.querySelectorAll('.needs-validation');
  forms.forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });

  // ── Tooltips ─────────────────────────────────────────────────
  var tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(function (el) {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });

});
