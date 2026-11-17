const $ = id => document.getElementById(id);
let jobs = [];
let marks = {};
try { marks = JSON.parse(localStorage.getItem("jobHunterMarks") || "{}"); } catch (_) { marks = {}; }

const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
  "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
}[ch]));

function deviceGroup(value) {
  const s = String(value || "").toLowerCase();
  if (s.includes("lebih memungkinkan") || s.includes("possible") || s.includes("likely")) return "likely";
  if (s.includes("meragukan") || s.includes("laptop") || s.includes("unlikely")) return "unlikely";
  return "unknown";
}

function updateStats() {
  $("savedCount").textContent = Object.values(marks).filter(v => v === "saved").length;
}

function render() {
  const q = $("search").value.trim().toLowerCase();
  const src = $("source").value;
  const status = $("status").value;
  const minScore = Number($("score").value);
  const device = $("device").value;

  const list = jobs.filter(j => {
    const haystack = [j.title, j.company, j.location, j.description, j.source, j.eligibility, ...(j.reasons || [])].join(" ").toLowerCase();
    const mark = marks[j.id] || "";
    return haystack.includes(q)
      && (!src || src === j.source)
      && (status === "all" || (status === "new" ? !mark : mark === status))
      && Number(j.fit_score || 0) >= minScore
      && (device === "all" || deviceGroup(j.android_feasibility) === device);
  });

  $("resultCount").textContent = list.length + " hasil";
  $("jobs").innerHTML = list.map(j => {
    const mark = marks[j.id] || "";
    const score = Number(j.fit_score || 0);
    const reasons = (j.reasons || []).map(reason => "<li>" + esc(reason) + "</li>").join("");
    const safeUrl = /^https:\/\//i.test(j.url || "") ? esc(j.url) : "";
    return `<article class="job">
      <div class="job-top"><span class="tag">${esc(j.source || "Sumber tidak diketahui")}</span><span class="score">${score}/100</span></div>
      <h3>${esc(j.title || "Posisi tanpa judul")}</h3>
      <p class="meta">${esc(j.company || "Perusahaan tidak tercantum")} · ${esc(j.location || "Lokasi belum tercantum")}</p>
      <div class="details">
        <p><strong>Kelayakan negara:</strong> ${esc(j.eligibility || "Belum diketahui — cek halaman asli")}</p>
        <p><strong>Perangkat:</strong> ${esc(j.android_feasibility || "Belum diketahui — cek persyaratan")}</p>
        <p><strong>Tingkat awal:</strong> ${esc(j.difficulty || "Belum dinilai")}</p>
      </div>
      ${reasons ? '<ul class="reasons">' + reasons + '</ul>' : ""}
      <p class="meta">Tanggal: ${esc(j.published ? new Date(j.published).toLocaleDateString("id-ID") : "Tidak tersedia")} · Status: <strong>${esc(mark || "Belum ditandai")}</strong></p>
      <div class="actions">
        ${safeUrl ? '<a class="primary" href="' + safeUrl + '" target="_blank" rel="noopener noreferrer">Periksa lowongan ↗</a>' : ""}
        <button type="button" data-id="${esc(j.id)}" data-mark="saved">Simpan</button>
        <button type="button" data-id="${esc(j.id)}" data-mark="applied">Sudah dilamar</button>
        <button type="button" data-id="${esc(j.id)}" data-mark="skip">Lewati</button>
        <button type="button" data-id="${esc(j.id)}" data-mark="">Reset</button>
      </div>
    </article>`;
  }).join("") || '<div class="empty">Tidak ada lowongan yang cocok dengan filter ini. Coba turunkan skor minimum atau ubah kata kunci.</div>';

  $("message").textContent = "Skor adalah aturan pencocokan sederhana. Selalu verifikasi informasi pada sumber asli.";
  updateStats();
}

async function init() {
  try {
    const response = await fetch("../data/jobs.json", { cache: "no-store" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    jobs = Array.isArray(data.jobs) ? data.jobs : [];
    $("count").textContent = data.count ?? jobs.length;
    $("updated").textContent = data.updated_at
      ? new Date(data.updated_at).toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" })
      : "Belum tersedia";

    [...new Set(jobs.map(j => j.source).filter(Boolean))].sort().forEach(source => {
      const option = document.createElement("option");
      option.value = source;
      option.textContent = source;
      $("source").append(option);
    });
    render();
  } catch (error) {
    $("count").textContent = "—";
    $("updated").textContent = "—";
    $("message").textContent = "Data gagal dimuat. Pastikan dashboard dibuka melalui GitHub Pages dan file data/jobs.json tersedia. (" + error.message + ")";
  }
}

["search", "source", "status", "score", "device"].forEach(id => {
  $(id).addEventListener(id === "search" ? "input" : "change", render);
});

$("jobs").addEventListener("click", event => {
  const button = event.target.closest("button[data-id]");
  if (!button) return;
  const id = button.dataset.id;
  if (button.dataset.mark) marks[id] = button.dataset.mark;
  else delete marks[id];
  try { localStorage.setItem("jobHunterMarks", JSON.stringify(marks)); } catch (_) {}
  render();
});

init();