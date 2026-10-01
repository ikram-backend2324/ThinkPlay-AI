(function () {
  const questions = JSON.parse(document.getElementById("questions-data").textContent);
  const CONFIG = window.QUIZ_CONFIG || {};
  const DRAFT_KEY = `teachx-quiz-${CONFIG.sessionId}`;
  let current = 0;
  let answers = {}; // question id -> submitted answer object
  let times = {}; // question id -> seconds spent (summed over every visit)
  const getters = new Array(questions.length).fill(null);

  // Restore a draft saved earlier (page reload, lost connection, closed tab).
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null");
    if (draft && draft.answers) {
      answers = draft.answers;
      times = draft.times || {};
      current = Math.min(Math.max(0, draft.current || 0), questions.length - 1);
    }
  } catch (e) {
    /* no storage available — start fresh */
  }

  function saveDraft() {
    try {
      localStorage.setItem(DRAFT_KEY, JSON.stringify({ answers, times, current }));
    } catch (e) {
      /* storage full or blocked — the quiz still works, just without a draft */
    }
  }

  // Time on the visible question only: paused while the tab is hidden.
  let shownAt = performance.now();
  function stopClock() {
    const q = questions[current];
    if (!q || shownAt === null) return;
    times[q.id] = (times[q.id] || 0) + (performance.now() - shownAt) / 1000;
    shownAt = null;
  }
  function startClock() {
    shownAt = performance.now();
  }
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopClock();
      collectCurrentAnswer();
      saveDraft();
    } else {
      startClock();
    }
  });

  const mount = document.getElementById("question-mount");
  const counter = document.getElementById("quiz-counter");
  const progressFill = document.getElementById("quiz-progress-fill");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");
  const btnGiveUp = document.getElementById("btn-give-up");
  const giveUpForm = document.getElementById("give-up-form");

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function getCookie(name) {
    const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? match.pop() : "";
  }

  const I18N = window.QUIZ_I18N || {};
  const TYPE_LABELS = I18N.typeLabels || {};

  function renderFillBlank(container, q, prev) {
    const wrap = document.createElement("div");
    wrap.className = "question-prompt";
    const parts = String(q.data.prompt || "").split("___");
    let input;
    parts.forEach((part, i) => {
      wrap.appendChild(document.createTextNode(part));
      if (i < parts.length - 1) {
        input = document.createElement("input");
        input.type = "text";
        input.className = "blank-input";
        input.autocomplete = "off";
        input.value = (prev && prev.value) || "";
        wrap.appendChild(input);
      }
    });
    container.appendChild(wrap);
    return () => ({ value: input ? input.value.trim() : "" });
  }

  function renderCodeComplete(container, q, prev) {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    prompt.textContent = q.data.prompt || "";
    container.appendChild(prompt);

    const console_ = document.createElement("div");
    console_.className = "console-window";
    const titlebar = document.createElement("div");
    titlebar.className = "console-titlebar";
    titlebar.innerHTML =
      '<span class="console-dot red"></span><span class="console-dot yellow"></span>' +
      '<span class="console-dot green"></span>';
    const langLabel = document.createElement("span");
    langLabel.className = "console-lang";
    langLabel.textContent = q.data.language || "code"; // comes from the question, not trusted as HTML
    titlebar.appendChild(langLabel);
    console_.appendChild(titlebar);

    const pre = document.createElement("pre");
    pre.className = "code-block";
    const prompt_ = document.createElement("span");
    prompt_.className = "console-prompt";
    prompt_.textContent = "$ ";
    pre.appendChild(prompt_);

    const parts = String(q.data.code_template || "").split("___");
    let input;
    parts.forEach((part, i) => {
      pre.appendChild(document.createTextNode(part));
      if (i < parts.length - 1) {
        input = document.createElement("input");
        input.type = "text";
        input.className = "code-blank";
        input.autocomplete = "off";
        input.spellcheck = false;
        input.value = (prev && prev.value) || "";
        pre.appendChild(input);
      }
    });
    console_.appendChild(pre);
    container.appendChild(console_);
    return () => ({ value: input ? input.value.trim() : "" });
  }

  function renderMultiSelect(container, q, prev) {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    prompt.textContent = q.data.prompt || "";
    container.appendChild(prompt);

    const grid = document.createElement("div");
    grid.className = "chip-grid";
    const selected = new Set((prev && prev.selected_ids) || []);

    (q.data.options || []).forEach((opt) => {
      const chip = document.createElement("div");
      chip.className = "chip" + (selected.has(opt.id) ? " selected" : "");
      chip.textContent = opt.text;
      chip.dataset.id = opt.id;
      chip.addEventListener("click", () => {
        if (selected.has(opt.id)) {
          selected.delete(opt.id);
          chip.classList.remove("selected");
        } else {
          selected.add(opt.id);
          chip.classList.add("selected");
        }
      });
      grid.appendChild(chip);
    });
    container.appendChild(grid);
    return () => ({ selected_ids: Array.from(selected) });
  }

  function renderNumeric(container, q, prev) {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    prompt.textContent = q.data.prompt || "";
    container.appendChild(prompt);

    // The server computes the range; the answer itself is never sent.
    const min = Number(q.data.min) || 0;
    const max = Number(q.data.max) || 100;
    const hasPrev = prev && prev.value !== undefined;
    const startValue = hasPrev ? prev.value : Math.round((min + max) / 2);
    // An untouched slider is "no answer", not the value it happens to start at.
    let touched = hasPrev;

    const row = document.createElement("div");
    row.className = "numeric-row";

    const range = document.createElement("input");
    range.type = "range";
    range.min = min;
    range.max = max;
    range.step = (max - min) > 40 ? 1 : 0.1;
    range.value = startValue;

    const valueDisplay = document.createElement("div");
    valueDisplay.className = "numeric-value";
    valueDisplay.textContent = startValue + (q.data.unit ? " " + q.data.unit : "");

    const exact = document.createElement("input");
    exact.type = "number";
    exact.className = "numeric-exact";
    exact.value = startValue;
    exact.step = range.step;

    range.addEventListener("input", () => {
      touched = true;
      exact.value = range.value;
      valueDisplay.textContent = range.value + (q.data.unit ? " " + q.data.unit : "");
    });
    exact.addEventListener("input", () => {
      touched = true;
      range.value = exact.value;
      valueDisplay.textContent = exact.value + (q.data.unit ? " " + q.data.unit : "");
    });

    row.appendChild(range);
    row.appendChild(exact);
    container.appendChild(row);
    container.appendChild(valueDisplay);

    return () => (touched && exact.value !== "" ? { value: Number(exact.value) } : {});
  }

  function renderOrdering(container, q, prev) {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    prompt.textContent = q.data.prompt || "";
    container.appendChild(prompt);

    let items = q.data.items || [];
    if (prev && Array.isArray(prev.order) && prev.order.length === items.length) {
      const byId = Object.fromEntries(items.map((it) => [it.id, it]));
      items = prev.order.map((id) => byId[id]).filter(Boolean);
    } else {
      items = shuffle(items);
    }

    const list = document.createElement("ul");
    list.className = "order-list";
    items.forEach((it) => {
      const li = document.createElement("li");
      li.className = "order-item";
      li.dataset.itemId = it.id;
      const handle = document.createElement("span");
      handle.className = "handle";
      handle.textContent = "⠿";
      const text = document.createElement("span");
      text.textContent = it.text; // question text is never trusted as HTML
      li.append(handle, text);
      list.appendChild(li);
    });
    container.appendChild(list);

    if (window.Sortable) {
      new Sortable(list, { animation: 150, handle: ".handle" });
    }

    return () => ({ order: Array.from(list.children).map((li) => li.dataset.itemId) });
  }

  function renderMatching(container, q, prev) {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    prompt.textContent = q.data.prompt || "";
    container.appendChild(prompt);

    // The server sends the two columns separately; right-hand ids are opaque
    // tokens, so the pairing can't be read from the page.
    const lefts = q.data.lefts || [];
    const rights = q.data.rights || [];
    const prevPairs = (prev && prev.pairs) || {};

    const cols = document.createElement("div");
    cols.className = "matching-cols";

    const leftCol = document.createElement("div");
    leftCol.className = "matching-col";
    leftCol.innerHTML = `<h4>${I18N.terms || "Terms"}</h4>`;
    const pool = document.createElement("ul");
    pool.className = "order-list match-pool";
    leftCol.appendChild(pool);

    const rightCol = document.createElement("div");
    rightCol.className = "matching-col";
    rightCol.innerHTML = `<h4>${I18N.definitions || "Definitions"}</h4>`;

    const targetLists = {};
    const targetSlots = {};
    shuffle(rights).forEach((right) => {
      const slot = document.createElement("div");
      slot.className = "match-slot";
      const labelEl = document.createElement("div");
      labelEl.className = "match-slot-label";
      labelEl.textContent = right.text;
      const targetList = document.createElement("ul");
      targetList.className = "match-drop";
      targetList.dataset.pairId = right.id;
      targetList.dataset.placeholder = I18N.dropHere || "Drop here";
      slot.appendChild(labelEl);
      slot.appendChild(targetList);
      rightCol.appendChild(slot);
      targetLists[right.id] = targetList;
      targetSlots[right.id] = slot;
    });

    shuffle(lefts).forEach((left) => {
      const li = document.createElement("li");
      li.className = "match-item";
      li.dataset.pairId = left.id;
      li.textContent = left.text;
      const assignedTo = prevPairs[left.id];
      if (assignedTo && targetLists[assignedTo]) {
        targetLists[assignedTo].appendChild(li);
        targetSlots[assignedTo].classList.add("filled");
      } else {
        pool.appendChild(li);
      }
    });

    cols.appendChild(leftCol);
    cols.appendChild(rightCol);
    container.appendChild(cols);

    if (window.Sortable) {
      const groupName = "match-" + q.id;
      new Sortable(pool, { group: groupName, animation: 150 });
      Object.entries(targetLists).forEach(([pairId, targetList]) => {
        const slotEl = targetSlots[pairId];
        new Sortable(targetList, {
          group: groupName,
          animation: 150,
          onAdd(evt) {
            // Evict whichever item ISN'T the one just dropped — SortableJS
            // can insert the new item either before or after an existing
            // occupant depending on drop position, so children[0] isn't
            // reliably the old resident.
            Array.from(targetList.children).forEach((child) => {
              if (child !== evt.item) pool.appendChild(child);
            });
            slotEl.classList.add("filled");
          },
          onRemove() {
            slotEl.classList.remove("filled");
          },
        });
      });
    }

    return () => {
      const submitted = {};
      Object.entries(targetLists).forEach(([pairId, list]) => {
        if (list.children.length) submitted[list.children[0].dataset.pairId] = pairId;
      });
      return { pairs: submitted };
    };
  }

  function renderCategorize(container, q, prev) {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    prompt.textContent = q.data.prompt || "";
    container.appendChild(prompt);

    const categories = q.data.categories || [];
    const items = shuffle(q.data.items || []);
    const prevAssignments = (prev && prev.assignments) || {};

    const wrap = document.createElement("div");
    wrap.className = "categorize-wrap";

    const poolWrap = document.createElement("div");
    poolWrap.className = "categorize-pool-wrap";
    poolWrap.innerHTML = `<h4>${I18N.itemsLabel || "Items"}</h4>`;
    const pool = document.createElement("ul");
    pool.className = "order-list categorize-pool";
    poolWrap.appendChild(pool);
    wrap.appendChild(poolWrap);

    const bucketGrid = document.createElement("div");
    bucketGrid.className = "categorize-buckets";
    const bucketLists = {};
    categories.forEach((cat) => {
      const bucketWrap = document.createElement("div");
      bucketWrap.className = "categorize-bucket";
      const bucketTitle = document.createElement("h4");
      bucketTitle.textContent = cat.name;
      bucketWrap.appendChild(bucketTitle);
      const list = document.createElement("ul");
      list.className = "order-list categorize-drop";
      list.dataset.categoryId = cat.id;
      bucketWrap.appendChild(list);
      bucketGrid.appendChild(bucketWrap);
      bucketLists[cat.id] = list;
    });
    wrap.appendChild(bucketGrid);
    container.appendChild(wrap);

    items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "match-item";
      li.dataset.itemId = item.id;
      li.textContent = item.text;
      const assignedTo = prevAssignments[item.id];
      if (assignedTo && bucketLists[assignedTo]) {
        bucketLists[assignedTo].appendChild(li);
      } else {
        pool.appendChild(li);
      }
    });

    if (window.Sortable) {
      const groupName = "categorize-" + q.id;
      new Sortable(pool, { group: groupName, animation: 150 });
      Object.values(bucketLists).forEach((list) => {
        new Sortable(list, { group: groupName, animation: 150 });
      });
    }

    return () => {
      const assignments = {};
      Object.entries(bucketLists).forEach(([catId, list]) => {
        Array.from(list.children).forEach((li) => {
          assignments[li.dataset.itemId] = catId;
        });
      });
      return { assignments };
    };
  }

  function renderHotspotText(container, q, prev) {
    const prompt = document.createElement("div");
    prompt.className = "question-prompt";
    prompt.textContent = q.data.prompt || "";
    container.appendChild(prompt);

    const passage = document.createElement("div");
    passage.className = "hotspot-passage";
    const selected = new Set((prev && prev.selected_ids) || []);

    (q.data.tokens || []).forEach((tok) => {
      const span = document.createElement("span");
      span.className = "hotspot-token" + (selected.has(tok.id) ? " selected" : "");
      span.textContent = tok.text;
      span.dataset.id = tok.id;
      span.addEventListener("click", () => {
        if (selected.has(tok.id)) {
          selected.delete(tok.id);
          span.classList.remove("selected");
        } else {
          selected.add(tok.id);
          span.classList.add("selected");
        }
      });
      passage.appendChild(span);
      passage.appendChild(document.createTextNode(" "));
    });

    container.appendChild(passage);
    return () => ({ selected_ids: Array.from(selected) });
  }

  const RENDERERS = {
    fill_blank: renderFillBlank,
    matching: renderMatching,
    ordering: renderOrdering,
    multi_select: renderMultiSelect,
    numeric: renderNumeric,
    code_complete: renderCodeComplete,
    categorize: renderCategorize,
    hotspot_text: renderHotspotText,
  };

  function renderQuestion(index) {
    const q = questions[index];
    mount.innerHTML = "";

    const card = document.createElement("div");
    card.className = "panel question-card";
    const tag = document.createElement("div");
    tag.className = "question-type-tag";
    tag.textContent = TYPE_LABELS[q.type] || q.type;
    card.appendChild(tag);
    mount.appendChild(card);

    const renderer = RENDERERS[q.type];
    const prev = answers[q.id];
    if (renderer) {
      getters[index] = renderer(card, q, prev);
    } else {
      const fallback = document.createElement("div");
      fallback.className = "question-prompt";
      fallback.textContent = I18N.unsupported || "This question type isn't supported yet.";
      card.appendChild(fallback);
      getters[index] = () => ({});
    }

    counter.textContent = `${index + 1} / ${questions.length}`;
    progressFill.style.width = `${Math.round((index / questions.length) * 100)}%`;
    btnPrev.style.visibility = index === 0 ? "hidden" : "visible";
    btnNext.textContent = index === questions.length - 1 ? (I18N.finish || "Finish →") : (I18N.next || "Next →");

    if (window.gsap) {
      gsap.fromTo(card, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out" });
    }
  }

  function collectCurrentAnswer() {
    const q = questions[current];
    const getter = getters[current];
    if (getter) answers[q.id] = getter();
  }

  function saveOffline(body) {
    const app = window.TEACHX || {};
    const saved = app.outbox && app.outbox.add({ url: CONFIG.submitUrl, body, savedAt: Date.now() });
    if (!saved) return false;
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch (e) {
      /* ignore */
    }
    mount.innerHTML = "";
    const card = document.createElement("div");
    card.className = "panel question-card offline-saved";
    const title = document.createElement("h2");
    title.textContent = "📴 " + (I18N.offlineSavedTitle || "Saved offline");
    const text = document.createElement("p");
    text.textContent = I18N.offlineSavedBody || "Your answers are saved on this device and will be sent automatically when you are back online.";
    card.append(title, text);
    mount.appendChild(card);
    document.querySelector(".quiz-nav").style.display = "none";
    if (btnGiveUp) btnGiveUp.style.display = "none";
    return true;
  }

  async function submitQuiz() {
    stopClock();
    collectCurrentAnswer();
    saveDraft();
    btnNext.disabled = true;
    btnPrev.disabled = true;
    btnNext.textContent = I18N.grading || "Grading…";
    const rounded = {};
    Object.keys(times).forEach((id) => { rounded[id] = Math.round(times[id] * 10) / 10; });
    const body = JSON.stringify({ answers, times: rounded });

    if (!navigator.onLine && saveOffline(body)) return;
    try {
      const res = await fetch(CONFIG.submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = await res.json();
      try {
        localStorage.removeItem(DRAFT_KEY);
      } catch (e) {
        /* ignore */
      }
      window.location.href = result.redirect || CONFIG.resultsUrl;
    } catch (err) {
      // A network failure (not a server error) means we're offline: keep the answers for later.
      if (err instanceof TypeError && saveOffline(body)) return;
      btnNext.disabled = false;
      btnPrev.disabled = false;
      btnNext.textContent = I18N.finish || "Finish →";
      startClock();
      alert(I18N.submitError || "Could not submit your test — check your connection and try again.");
    }
  }

  function goTo(index) {
    stopClock();
    collectCurrentAnswer();
    current = index;
    saveDraft();
    renderQuestion(current);
    startClock();
  }

  btnNext.addEventListener("click", () => {
    if (current < questions.length - 1) {
      goTo(current + 1);
    } else {
      submitQuiz();
    }
  });

  btnPrev.addEventListener("click", () => {
    if (current > 0) goTo(current - 1);
  });

  if (btnGiveUp && giveUpForm) {
    btnGiveUp.addEventListener("click", () => {
      if (window.confirm(I18N.giveUpConfirm || "Abandon this test?")) {
        try {
          localStorage.removeItem(DRAFT_KEY);
        } catch (e) {
          /* ignore */
        }
        giveUpForm.submit();
      }
    });
  }

  renderQuestion(current);
  startClock();
})();
