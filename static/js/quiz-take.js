(function () {
  const questions = JSON.parse(document.getElementById("questions-data").textContent);
  let current = 0;
  const answers = {}; // question id -> submitted answer object
  const getters = new Array(questions.length).fill(null);

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

    const pre = document.createElement("pre");
    pre.className = "code-block";
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
    container.appendChild(pre);
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

    const answer = Number(q.data.answer) || 0;
    const tolerance = Number(q.data.tolerance) || Math.max(1, Math.abs(answer) * 0.1);
    const min = q.data.min !== undefined && q.data.min !== null ? Number(q.data.min) : answer - tolerance * 8 - 5;
    const max = q.data.max !== undefined && q.data.max !== null ? Number(q.data.max) : answer + tolerance * 8 + 5;
    const startValue = prev && prev.value !== undefined ? prev.value : Math.round((min + max) / 2);

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
      exact.value = range.value;
      valueDisplay.textContent = range.value + (q.data.unit ? " " + q.data.unit : "");
    });
    exact.addEventListener("input", () => {
      range.value = exact.value;
      valueDisplay.textContent = exact.value + (q.data.unit ? " " + q.data.unit : "");
    });

    row.appendChild(range);
    row.appendChild(exact);
    container.appendChild(row);
    container.appendChild(valueDisplay);

    return () => ({ value: Number(exact.value) });
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
      li.innerHTML = `<span class="handle">⠿</span><span>${it.text}</span>`;
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

    const pairs = q.data.pairs || [];
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
    shuffle(pairs).forEach((pair) => {
      const slot = document.createElement("div");
      slot.className = "match-slot";
      const labelEl = document.createElement("div");
      labelEl.className = "match-slot-label";
      labelEl.textContent = pair.right;
      const targetList = document.createElement("ul");
      targetList.className = "match-drop";
      targetList.dataset.pairId = pair.id;
      targetList.dataset.placeholder = I18N.dropHere || "Drop here";
      slot.appendChild(labelEl);
      slot.appendChild(targetList);
      rightCol.appendChild(slot);
      targetLists[pair.id] = targetList;
      targetSlots[pair.id] = slot;
    });

    shuffle(pairs).forEach((pair) => {
      const li = document.createElement("li");
      li.className = "match-item";
      li.dataset.pairId = pair.id;
      li.textContent = pair.left;
      const assignedTo = prevPairs[pair.id];
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
          onAdd() {
            while (targetList.children.length > 1) {
              pool.appendChild(targetList.children[0]);
            }
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

  const RENDERERS = {
    fill_blank: renderFillBlank,
    matching: renderMatching,
    ordering: renderOrdering,
    multi_select: renderMultiSelect,
    numeric: renderNumeric,
    code_complete: renderCodeComplete,
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

  async function submitQuiz() {
    collectCurrentAnswer();
    btnNext.disabled = true;
    btnPrev.disabled = true;
    btnNext.textContent = I18N.grading || "Grading…";
    try {
      const res = await fetch(window.QUIZ_CONFIG.submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify({ answers }),
      });
      const result = await res.json();
      window.location.href = result.redirect || window.QUIZ_CONFIG.resultsUrl;
    } catch (err) {
      btnNext.disabled = false;
      btnPrev.disabled = false;
      btnNext.textContent = I18N.finish || "Finish →";
      alert(I18N.submitError || "Could not submit your test — check your connection and try again.");
    }
  }

  btnNext.addEventListener("click", () => {
    collectCurrentAnswer();
    if (current < questions.length - 1) {
      current += 1;
      renderQuestion(current);
    } else {
      submitQuiz();
    }
  });

  btnPrev.addEventListener("click", () => {
    collectCurrentAnswer();
    if (current > 0) {
      current -= 1;
      renderQuestion(current);
    }
  });

  if (btnGiveUp && giveUpForm) {
    btnGiveUp.addEventListener("click", () => {
      if (window.confirm(I18N.giveUpConfirm || "Abandon this test?")) {
        giveUpForm.submit();
      }
    });
  }

  renderQuestion(0);
})();
