/*
 * Site-wide behaviour: language menu, service worker (offline mode), the
 * offline banner and the "outbox" of test submissions that were made while
 * offline and are sent automatically once the connection is back.
 */
(function () {
  const APP = window.TEACHX || {};
  const I18N = APP.i18n || {};
  const OUTBOX_KEY = "teachx-outbox";

  // ------------------------------------------------------------ language menu
  const langBtn = document.getElementById("lang-btn");
  const langWrap = document.getElementById("lang-switcher");
  if (langBtn && langWrap) {
    langBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      langWrap.classList.toggle("open");
    });
    document.addEventListener("click", () => langWrap.classList.remove("open"));
  }

  // ------------------------------------------- selectable cards (forms)
  // <label data-choice><input type="radio|checkbox" ...> ... </label> gets
  // the "selected" class while its input is checked.
  function syncChoice(input) {
    if (input.type === "radio") {
      document.querySelectorAll(`input[name="${input.name}"]`).forEach((i) => {
        const card = i.closest("label[data-choice]");
        if (card) card.classList.toggle("selected", i.checked);
      });
    } else {
      const card = input.closest("label[data-choice]");
      if (card) card.classList.toggle("selected", input.checked);
    }
  }
  document.querySelectorAll("label[data-choice] input").forEach((input) => {
    input.addEventListener("change", () => syncChoice(input));
    if (input.checked) syncChoice(input);
  });
  // <button data-select-all="field-name"> toggles every checkbox with that name.
  document.querySelectorAll("[data-select-all]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const boxes = Array.from(document.querySelectorAll(`input[name="${btn.dataset.selectAll}"]`));
      const allChecked = boxes.every((b) => b.checked);
      boxes.forEach((b) => {
        b.checked = !allChecked;
        syncChoice(b);
      });
    });
  });
  // <form data-busy="Text…"> disables its submit button and shows the text while the server works.
  document.querySelectorAll("form[data-busy]").forEach((form) => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = form.dataset.busy;
      }
    });
  });

  // ---------------------------------------------------------- storage helpers
  function readJSON(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }
  function writeJSON(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      return false;
    }
  }

  function getCookie(name) {
    const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? match.pop() : "";
  }

  // ----------------------------------------------------------------- outbox
  const outbox = {
    list() {
      return readJSON(OUTBOX_KEY, []);
    },
    add(entry) {
      const items = this.list().filter((e) => e.url !== entry.url);
      items.push(entry);
      return writeJSON(OUTBOX_KEY, items);
    },
    remove(url) {
      writeJSON(OUTBOX_KEY, this.list().filter((e) => e.url !== url));
    },
  };
  APP.outbox = outbox;
  APP.getCookie = getCookie;

  const outboxBanner = document.getElementById("outbox-banner");
  function showOutboxBanner(text, linkHref, linkText) {
    if (!outboxBanner) return;
    outboxBanner.textContent = text;
    if (linkHref) {
      const a = document.createElement("a");
      a.href = linkHref;
      a.textContent = linkText;
      outboxBanner.append(" ", a);
    }
    outboxBanner.hidden = !text;
  }

  let flushing = false;
  async function flushOutbox() {
    if (flushing || !navigator.onLine || !APP.authenticated) return;
    const items = outbox.list();
    if (!items.length) return;
    flushing = true;
    let lastRedirect = null;
    let sent = 0;
    let needsLogin = false;
    for (const item of items) {
      try {
        const res = await fetch(item.url, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
          body: item.body,
          credentials: "same-origin",
        });
        if (res.redirected) {
          // Sent to the login page: the session expired. Keep the answers until
          // the student logs in again — never drop them.
          needsLogin = true;
          break;
        }
        if (res.ok) {
          const data = await res.json().catch(() => ({}));
          lastRedirect = data.redirect || lastRedirect;
          outbox.remove(item.url);
          sent += 1;
        } else if (res.status === 403 || res.status === 404) {
          // Not ours to retry (logged out / session gone): drop it rather than looping forever.
          outbox.remove(item.url);
        }
      } catch (e) {
        break; // still offline
      }
    }
    flushing = false;
    const left = outbox.list().length;
    if (sent) {
      showOutboxBanner(
        `✅ ${(I18N.outboxSent || "Sent {n} saved test(s).").replace("{n}", sent)}`,
        lastRedirect,
        I18N.outboxView || "View"
      );
    } else if (left && needsLogin) {
      showOutboxBanner(`🔑 ${(I18N.outboxLogin || "Log in again to send {n} saved test(s).").replace("{n}", left)}`);
    } else if (left) {
      showOutboxBanner(`⏳ ${(I18N.outboxPending || "{n} test(s) waiting to be sent.").replace("{n}", left)}`);
    }
  }
  APP.flushOutbox = flushOutbox;

  // ---------------------------------------------------------- offline banner
  const offlineBanner = document.getElementById("offline-banner");
  function updateOnlineState() {
    if (offlineBanner) offlineBanner.hidden = navigator.onLine;
    if (navigator.onLine) flushOutbox();
  }
  window.addEventListener("online", updateOnlineState);
  window.addEventListener("offline", updateOnlineState);
  updateOnlineState();

  // ---------------------------------------------------------- service worker
  APP.prefetch = function (urls) {
    if (!("serviceWorker" in navigator) || !urls || !urls.length) return;
    navigator.serviceWorker.ready.then((reg) => {
      if (reg.active) reg.active.postMessage({ type: "prefetch", urls });
    });
  };

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
    navigator.serviceWorker.ready.then((reg) => {
      // Logged-out visitors must not see pages a previous user left in the cache.
      if (!APP.authenticated && reg.active) reg.active.postMessage({ type: "clear-pages" });
    });
  }
  // The SCAFFOLD guide is useful offline too: cache it once per browser session.
  if (APP.authenticated) {
    try {
      if (!sessionStorage.getItem("teachx-guide-cached")) {
        APP.prefetch(["/guide/"]);
        sessionStorage.setItem("teachx-guide-cached", "1");
      }
    } catch (e) {
      /* storage blocked: skip the prefetch */
    }
  }

  const logoutLink = document.getElementById("logout-link");
  if (logoutLink && "serviceWorker" in navigator) {
    logoutLink.addEventListener("click", () => {
      if (navigator.serviceWorker.controller) navigator.serviceWorker.controller.postMessage({ type: "clear-pages" });
    });
  }

  window.TEACHX = APP;
})();
