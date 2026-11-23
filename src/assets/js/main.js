(function () {
  "use strict";
  var cfg = window.SITE || {};
  var doc = document.documentElement;

  // Header shadow + mobile menu
  var header = document.querySelector(".header");
  var onScroll = function () { header && header.classList.toggle("is-scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  var burger = document.querySelector(".burger");
  if (burger) {
    burger.addEventListener("click", function () {
      var open = doc.classList.toggle("menu-open");
      burger.setAttribute("aria-expanded", String(open));
      document.body.style.overflow = open ? "hidden" : "";
    });
    document.querySelectorAll(".mobile-menu a").forEach(function (a) {
      a.addEventListener("click", function () {
        doc.classList.remove("menu-open");
        burger.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      });
    });
  }

  // Reveal on scroll
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
  }

  // Photo slider inside each case card
  document.querySelectorAll("[data-slider]").forEach(function (track) {
    var box = track.parentNode;
    var dots = box.querySelectorAll(".slider__dots span");
    var prev = box.querySelector(".slider__btn--prev"), next = box.querySelector(".slider__btn--next");
    var n = track.children.length;
    var current = function () { return Math.round(track.scrollLeft / track.clientWidth); };
    var update = function () {
      var i = current();
      Array.prototype.forEach.call(dots, function (d, k) { d.classList.toggle("on", k === i); });
      if (prev) prev.disabled = i <= 0;
      if (next) next.disabled = i >= n - 1;
    };
    var go = function (d) { track.scrollTo({ left: (current() + d) * track.clientWidth, behavior: "smooth" }); };
    if (prev) prev.addEventListener("click", function (e) { e.preventDefault(); go(-1); });
    if (next) next.addEventListener("click", function (e) { e.preventDefault(); go(1); });
    track.addEventListener("scroll", function () { window.requestAnimationFrame(update); }, { passive: true });
    update();
  });

  // Portfolio filters
  var chips = document.querySelectorAll("[data-filter]");
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var f = chip.getAttribute("data-filter");
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      document.querySelectorAll("[data-region]").forEach(function (card) {
        card.hidden = !(f === "all" || card.getAttribute("data-region") === f);
      });
    });
  });
  var hash = location.hash.replace("#", "");
  if (hash) {
    var target = document.querySelector('[data-filter="' + hash + '"]');
    if (target) target.click();
  }

  // Lightbox
  var links = Array.prototype.slice.call(document.querySelectorAll(".gallery a"));
  if (links.length) {
    var lb = document.createElement("div");
    lb.className = "lb";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-modal", "true");
    lb.setAttribute("aria-label", "Просмотр фотографий");
    lb.innerHTML = '<img alt=""><button class="lb__close" aria-label="Закрыть">×</button>' +
      '<button class="lb__prev" aria-label="Предыдущее фото">‹</button><button class="lb__next" aria-label="Следующее фото">›</button><div class="lb__count"></div>';
    document.body.appendChild(lb);
    var img = lb.querySelector("img"), count = lb.querySelector(".lb__count"), idx = 0, lastFocus;
    var show = function (i) {
      idx = (i + links.length) % links.length;
      img.src = links[idx].getAttribute("href");
      img.alt = links[idx].querySelector("img").alt;
      count.textContent = (idx + 1) + " / " + links.length;
    };
    var close = function () { lb.classList.remove("open"); document.body.style.overflow = ""; lastFocus && lastFocus.focus(); };
    links.forEach(function (a, i) {
      a.addEventListener("click", function (e) {
        e.preventDefault(); lastFocus = a; show(i);
        lb.classList.add("open"); document.body.style.overflow = "hidden";
        lb.querySelector(".lb__close").focus();
      });
    });
    lb.querySelector(".lb__close").addEventListener("click", close);
    lb.querySelector(".lb__prev").addEventListener("click", function () { show(idx - 1); });
    lb.querySelector(".lb__next").addEventListener("click", function () { show(idx + 1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") show(idx - 1);
      if (e.key === "ArrowRight") show(idx + 1);
    });
    var x0 = null;
    lb.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 40) show(idx + (dx < 0 ? 1 : -1));
      x0 = null;
    });
  }

  // Lazy YouTube
  document.querySelectorAll("[data-youtube]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + btn.getAttribute("data-youtube") + "?autoplay=1&rel=0";
      f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      f.title = btn.getAttribute("aria-label") || "Видео";
      btn.replaceWith(f);
    });
  });

  // Phone mask (light): keep digits, +, spaces, brackets, dashes
  document.querySelectorAll('input[type="tel"]').forEach(function (inp) {
    inp.addEventListener("input", function () { inp.value = inp.value.replace(/[^\d+()\-\s]/g, ""); });
  });

  // Lead forms
  document.querySelectorAll("form[data-lead]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var phone = form.querySelector('[name="phone"]');
      var digits = (phone.value.match(/\d/g) || []).length;
      var field = phone.closest(".field");
      if (digits < 10) {
        field.classList.add("invalid"); phone.setAttribute("aria-invalid", "true"); phone.focus();
        return;
      }
      field.classList.remove("invalid"); phone.removeAttribute("aria-invalid");

      var data = new FormData(form);
      data.append("page", document.title);
      var lines = [form.getAttribute("data-lead") || (doc.lang === "en" ? "Website request" : "Заявка с сайта")];
      data.forEach(function (v, k) {
        if (!v || k === "_gotcha" || k === "page") return;
        var label = form.querySelector('[name="' + k + '"]');
        var name = (label && label.getAttribute("data-label")) || k;
        lines.push(name + ": " + v);
      });
      var message = lines.join("\n");
      var btn = form.querySelector('[type="submit"]');
      btn.disabled = true;

      var done = function () {
        form.innerHTML = '<div class="form__ok" role="status"><svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="24" cy="24" r="22"/><path d="M15 24.5l6 6 12-13"/></svg>' +
          (doc.lang === "en"
            ? '<h3>Thank you, we have your request</h3><p>Polina or her assistant will get back to you within one business day. Prefer messaging? Write to us on WhatsApp right now.</p></div>'
            : '<h3>Спасибо, заявка получена</h3><p>Полина или её ассистент свяжутся с вами в течение рабочего дня. Если удобнее — напишите нам в WhatsApp прямо сейчас.</p></div>');
        if (window.ym && cfg.metrika) try { window.ym(cfg.metrika, "reachGoal", "lead"); } catch (err) {}
      };
      var toWhatsApp = function () {
        window.open("https://wa.me/" + (form.getAttribute("data-wa") || cfg.whatsapp) + "?text=" + encodeURIComponent(message), "_blank", "noopener");
        done();
      };

      if (cfg.formEndpoint) {
        fetch(cfg.formEndpoint, { method: "POST", body: data, headers: { Accept: "application/json" } })
          .then(function (r) { if (!r.ok) throw new Error(r.status); done(); })
          .catch(function () { btn.disabled = false; toWhatsApp(); });
      } else {
        toWhatsApp();
      }
    });
  });
})();
