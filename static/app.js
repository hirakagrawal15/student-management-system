const API = "/api/students";
const $ = (id) => document.getElementById(id);
const form = $("form"), fields = ["name", "roll_no", "class", "marks", "contact"];
let students = [], pendingDelete = null, searchTimer;

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function toast(msg, isError = false) {
  const t = $("toast");
  t.textContent = msg;
  t.className = "show" + (isError ? " error" : "");
  clearTimeout(toast.t);
  toast.t = setTimeout(() => (t.className = ""), 2600);
}

async function api(path = "", opts = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body && JSON.stringify(opts.body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || "Request failed."), { fields: data.fields });
  return data;
}

/* ---------- client-side validation (mirrors the server rules) ---------- */
function validate(v) {
  const e = {};
  if (!/^[A-Za-z .'-]{2,}$/.test(v.name)) e.name = "Enter a name using letters only (at least 2).";
  if (!/^[A-Za-z0-9-]{1,20}$/.test(v.roll_no)) e.roll_no = "Use 1-20 letters, digits or hyphens.";
  if (!v.class) e.class = "Class is required.";
  const m = Number(v.marks);
  if (v.marks === "" || isNaN(m) || m < 0 || m > 100) e.marks = "Enter a number from 0 to 100.";
  if (!/^[6-9]\d{9}$/.test(v.contact)) e.contact = "Enter a valid 10-digit mobile number.";
  return e;
}

function showErrors(errs = {}) {
  fields.forEach((f) => {
    $(f).classList.toggle("bad", !!errs[f]);
    document.querySelector(`[data-for="${f}"]`).textContent = errs[f] || "";
  });
}

/* ---------- rendering ---------- */
const gradeClass = (m) => (m >= 75 ? "g-hi" : m >= 40 ? "g-mid" : "g-lo");

function render() {
  const q = $("search").value.trim();
  $("rows").innerHTML = students.map((s) => `
    <tr>
      <td class="roll">${esc(s.roll_no)}</td>
      <td>${esc(s.name)}</td>
      <td>${esc(s.class)}</td>
      <td><span class="grade ${gradeClass(s.marks)}">${s.marks}</span></td>
      <td class="num">${esc(s.contact)}</td>
      <td class="btns">
        <button class="ghost" data-edit="${s.id}" aria-label="Edit ${esc(s.name)}">Edit</button>
        <button class="ghost" data-del="${s.id}" aria-label="Delete ${esc(s.name)}">Delete</button>
      </td>
    </tr>`).join("");
  const empty = $("empty");
  empty.hidden = students.length > 0;
  empty.textContent = q ? `No student matches “${q}”. Check the spelling or try the roll number.`
                        : "No students yet. Add the first one using the form.";
}

function renderStats() {
  $("st-count").textContent = students.length;
  if (!students.length) { $("st-avg").textContent = $("st-top").textContent = "–"; return; }
  const avg = students.reduce((a, s) => a + s.marks, 0) / students.length;
  const top = students.reduce((a, s) => (s.marks > a.marks ? s : a));
  $("st-avg").textContent = avg.toFixed(1);
  $("st-top").textContent = top.name.split(" ")[0];
}

async function load() {
  const q = $("search").value.trim();
  try {
    students = await api(q ? `?q=${encodeURIComponent(q)}` : "");
    render();
    if (!q) renderStats();
  } catch (e) { toast(e.message, true); }
}

/* ---------- form handling ---------- */
function resetForm() {
  form.reset();
  $("id").value = "";
  showErrors();
  $("form-title").textContent = "Add student";
  $("save").textContent = "Add student";
  $("cancel").hidden = true;
  document.querySelector(".panel").classList.remove("editing");
}

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const v = Object.fromEntries(fields.map((f) => [f, $(f).value.trim()]));
  const errs = validate(v);
  showErrors(errs);
  if (Object.keys(errs).length) return $(Object.keys(errs)[0]).focus();
  const id = $("id").value;
  try {
    await api(id ? `/${id}` : "", { method: id ? "PUT" : "POST", body: { ...v, marks: Number(v.marks) } });
    toast(id ? "Student updated." : "Student added.");
    resetForm();
    load();
  } catch (e) {
    if (e.fields) showErrors(e.fields); else toast(e.message, true);
  }
});

$("cancel").addEventListener("click", resetForm);

$("rows").addEventListener("click", (ev) => {
  const edit = ev.target.closest("[data-edit]"), del = ev.target.closest("[data-del]");
  if (edit) {
    const s = students.find((x) => x.id == edit.dataset.edit);
    fields.forEach((f) => ($(f).value = s[f]));
    $("id").value = s.id;
    $("form-title").textContent = "Edit student";
    $("save").textContent = "Save changes";
    $("cancel").hidden = false;
    document.querySelector(".panel").classList.add("editing");
    showErrors();
    $("name").focus();
  }
  if (del) {
    pendingDelete = students.find((x) => x.id == del.dataset.del);
    $("confirm-text").textContent = `Delete ${pendingDelete.name} (${pendingDelete.roll_no})? This cannot be undone.`;
    $("confirm").showModal();
  }
});

$("confirm-no").addEventListener("click", () => $("confirm").close());
$("confirm-yes").addEventListener("click", async () => {
  $("confirm").close();
  try {
    await api(`/${pendingDelete.id}`, { method: "DELETE" });
    toast("Student deleted.");
    if ($("id").value == pendingDelete.id) resetForm();
  } catch (e) { toast(e.message, true); }
  load();
});

$("search").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(load, 200); });
$("contact").addEventListener("input", (e) => (e.target.value = e.target.value.replace(/\D/g, "")));

load();
