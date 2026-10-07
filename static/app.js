/* SHORTLIST frontend */
"use strict";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(path, body) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let msg = `Request failed (${r.status})`;
    try { msg = (await r.json()).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  return r.json();
}

/* ---------------- tabs ---------------- */
$$("nav button").forEach(b => b.addEventListener("click", () => {
  $$("nav button").forEach(x => x.classList.remove("on"));
  $$(".tab").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  $("#t-" + b.dataset.t).classList.add("on");
  if (b.dataset.t === "pipeline") loadPipeline();
}));

function show(id, html) {
  const el = $("#" + id);
  el.innerHTML = html;
  el.classList.add("on");
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
const err = (m) => `<div class="callout bad"><b>Could not run that.</b> ${esc(m)}</div>`;

/* ---------------- dial ---------------- */
function dial(pct, color, label) {
  const r = 48, c = 2 * Math.PI * r;
  return `<div class="dial">
    <svg width="118" height="118" viewBox="0 0 118 118">
      <circle cx="59" cy="59" r="${r}" fill="none" stroke="#232735" stroke-width="9"/>
      <circle cx="59" cy="59" r="${r}" fill="none" stroke="${color}" stroke-width="9"
        stroke-linecap="round" stroke-dasharray="${c}"
        stroke-dashoffset="${c - (c * Math.max(0, Math.min(100, pct)) / 100)}"/>
    </svg>
    <b style="color:${color}">${pct}</b><span>${esc(label)}</span>
  </div>`;
}
const riskColor = (v) => v >= 80 ? "var(--crit)" : v >= 60 ? "#ff8a5d"
  : v >= 40 ? "var(--warn)" : v >= 20 ? "#9fb4d8" : "var(--ok)";
const scoreColor = (v) => v >= 70 ? "var(--ok)" : v >= 48 ? "var(--warn)" : "var(--bad)";

/* ================= 1. GHOST RADAR ================= */
const SAMPLES = {
  scam: {
    title: "Administrative Officer (Federal Placement)",
    company: "Federal Ministry Recruitment Desk",
    jd: "URGENT! We are recruiting for a federal agency placement. No experience required. "
      + "Guaranteed employment. Salary N450,000 monthly plus allowances. Slots are limited.",
    contact: "Congratulations, your name is on the shortlist for the NNPC graduate intake. "
      + "I have a connection inside and can push your name. To secure your slot, send "
      + "N150,000 processing and documentation fee to my account number 0123456789 "
      + "(GTBank, Musa A). You must pay within 10 minutes before close of business today "
      + "or the slot goes to the next candidate. No interview needed.",
    email: "hr.federalrecruitment2026@gmail.com",
    site: "nnpc-career.com",
    channel: "whatsapp",
    age: "", apps: "", interview: "none",
    payto: "individual", pay: true, unsol: true, repost: false, salary: "false",
  },
  ghost: {
    title: "Data Analyst",
    company: "Meridian Holdings",
    jd: "We are seeking a dynamic self-starter to join our fast-paced environment. "
      + "The ideal candidate is a team player, detail oriented, with excellent "
      + "communication skills, a proactive mindset, and the ability to wear many hats. "
      + "You will be responsible for various analytical tasks and support the team. "
      + "Rockstar attitude essential. Go-getter preferred.",
    contact: "", email: "", site: "", channel: "",
    age: "94", apps: "100", interview: "",
    payto: "none", pay: false, unsol: false, repost: true, salary: "false",
  },
  clean: {
    title: "Senior Backend Engineer",
    company: "Acme Fintech Ltd",
    jd: "Senior Backend Engineer — Payments Platform.\nReports to the Head of Engineering. "
      + "You will own the payments ledger service and lead its migration to event sourcing.\n\n"
      + "Requirements:\n- 5+ years Python, strong Django and FastAPI\n- PostgreSQL, Redis\n"
      + "- AWS (EC2, S3, Lambda), Docker, Kubernetes\n- CI/CD with GitHub Actions\n"
      + "- Microservices and REST API design\n- BSc Computer Science or equivalent\n\n"
      + "Team of 8 engineers. First project: migrate the ledger in Q1.\n"
      + "Interview process: recruiter screen, technical panel, take-home, final round.\n"
      + "Salary range: NGN 9,000,000 – 14,000,000. Benefits: pension, HMO, 25 days leave.\n"
      + "Location: Lagos, hybrid (3 days on site).",
    contact: "", email: "talent@acmefintech.com", site: "acmefintech.com",
    channel: "company_portal", age: "6", apps: "34", interview: "video",
    payto: "none", pay: false, unsol: false, repost: false, salary: "true",
  },
};

function loadSample(k) {
  const s = SAMPLES[k];
  $("#g-title").value = s.title; $("#g-company").value = s.company;
  $("#g-jd").value = s.jd; $("#g-contact").value = s.contact;
  $("#g-email").value = s.email; $("#g-site").value = s.site;
  $("#g-channel").value = s.channel; $("#g-age").value = s.age;
  $("#g-apps").value = s.apps; $("#g-interview").value = s.interview;
  $("#g-payto").value = s.payto; $("#g-pay").checked = s.pay;
  $("#g-unsol").checked = s.unsol; $("#g-repost").checked = s.repost;
  $("#g-salary").value = s.salary;
  runGhost();
}
$("#g-sample-scam").onclick = () => loadSample("scam");
$("#g-sample-ghost").onclick = () => loadSample("ghost");
$("#g-sample-clean").onclick = () => loadSample("clean");

function ghostPayload() {
  const int = (v) => (v === "" || v === null ? null : Number(v));
  const tri = (v) => (v === "" ? null : v === "true");
  return {
    job_title: $("#g-title").value, company_name: $("#g-company").value,
    job_description: $("#g-jd").value, contact_text: $("#g-contact").value,
    contact_email: $("#g-email").value, contact_channel: $("#g-channel").value,
    company_website: $("#g-site").value,
    listing_age_days: int($("#g-age").value), applicant_count: int($("#g-apps").value),
    interview_mode: $("#g-interview").value, payment_to: $("#g-payto").value,
    payment_requested: $("#g-pay").checked || null,
    unsolicited: $("#g-unsol").checked, reposted: $("#g-repost").checked,
    salary_listed: tri($("#g-salary").value),
  };
}

async function runGhost() {
  let d;
  try { d = await api("/api/ghost", ghostPayload()); }
  catch (e) { return show("o-ghost", err(e.message)); }

  const col = riskColor(d.risk_score);
  const kind = d.is_probable_scam ? "Probable scam" : d.is_probable_ghost ? "Probable ghost job" : "";

  let h = `<div class="card">
    <div class="gauge">
      ${dial(d.risk_score, col, "risk")}
      <div class="verdict">
        <div class="tagrow">
          <span class="tg ${d.is_probable_scam ? "critical" : "positive"}"
            style="color:${col};border-color:${col}">${esc(d.verdict)}</span>
          ${kind ? `<span class="tg ${d.is_probable_scam ? "critical" : "medium"}">${esc(kind)}</span>` : ""}
        </div>
        <h3 style="color:${col}">${esc(d.verdict)}</h3>
        <p>${esc(d.summary)}</p>
      </div>
    </div>`;

  if (d.naira_at_risk) h += `<div class="callout bad"><b>₦${d.naira_at_risk.toLocaleString()}
    is being demanded.</b> Documented Nigerian victims lost ₦20,000–₦350,000 to exactly this
    pattern; Kano police arrested a man over a ₦40m job scam in 2026. Do not pay.</div>`;

  h += `</div><div class="card"><h3>What triggered this</h3>
    <div class="sub">Every signal is weighted and sourced. Read them, then decide.</div>`;
  h += d.signals.map(s => `<div class="sig ${s.severity}">
      <h4><span class="tg ${s.severity}">${esc(s.severity)}</span>${esc(s.title)}</h4>
      ${s.evidence ? `<div class="ev">${esc(s.evidence)}</div>` : ""}
      <p>${esc(s.detail)}</p>
      <div class="src">Source: ${esc(s.source)}</div>
    </div>`).join("");
  h += `</div><div class="card"><h3>Do this next</h3>
    <div class="sub">${esc(d.signals.filter(s => s.severity === "critical").length)} critical
      signal(s). Total verification time: ~${d.verification_steps.reduce((a, s) => a + (s.minutes || 0), 0)} minutes.</div>
    <ol class="steps">${d.verification_steps.map(s =>
      `<li class="${s.critical ? "urgent" : ""}"><b>${esc(s.title)}</b>
        <small>${esc(s.why)}${s.minutes ? ` · ${s.minutes} min` : ""}</small></li>`).join("")}
    </ol></div>`;

  h += `<div class="row"><button class="btn ghost sm" id="save-ghost">Save to pipeline</button>
    <button class="btn ghost sm" id="ghost-to-match">Tailor my resume for this →</button></div>`;

  show("o-ghost", h);

  $("#save-ghost").onclick = async () => {
    const p = ghostPayload();
    await api("/api/pipeline", {
      application: {
        company: p.company_name || "Unknown", role: p.job_title || "Unknown role",
        stage: d.verdict === "CLEAR" || d.verdict === "LOW RISK" ? "vetted" : "found",
        ghost_score: d.risk_score, ghost_verdict: d.verdict, match_rate: 0,
        source: p.contact_channel || "manual", notes: d.summary,
      },
    });
    $("#save-ghost").textContent = "Saved ✓";
  };
  $("#ghost-to-match").onclick = () => {
    $("#m-jd").value = $("#g-jd").value;
    $$("nav button")[1].click();
    $("#m-resume").focus();
  };
}
$("#g-run").onclick = runGhost;

/* ================= 2. ATS MATCH ================= */
$("#m-sample").onclick = () => {
  $("#m-jd").value = SAMPLES.clean.jd;
  $("#m-resume").value =
`Jane Okoye
jane.okoye@email.com | +234 803 000 0000 | Lagos, Nigeria

EXPERIENCE

Senior Backend Engineer, Paystack
Jan 2021 - Present
- Architected a payments reconciliation service in Python and Django that cut
  settlement errors by 74% across 12,000 merchants.
- Built FastAPI endpoints serving 40M requests per month at p99 latency of 90ms.
- Migrated the ledger from MySQL to PostgreSQL, reducing query time by 61%.
- Automated deployment with Docker, Kubernetes and GitHub Actions CI/CD, cutting
  release time from 3 hours to 18 minutes.
- Led a team of 5 engineers through an AWS migration using Lambda and S3.
- Designed REST API contracts adopted by 3 internal teams.

Backend Engineer, Konga
Mar 2018 - Dec 2020
- Reduced checkout abandonment by 22% by rewriting the cart service.

EDUCATION
BSc Computer Science, University of Lagos, 2016

SKILLS
Python, Django, FastAPI, PostgreSQL, MySQL, AWS, Docker, Kubernetes, CI/CD,
microservices, REST API, communication`;
  runMatch();
};

async function runMatch() {
  let d;
  try {
    d = await api("/api/match", {
      job_description: $("#m-jd").value, resume: $("#m-resume").value,
      pool_size: Number($("#m-pool").value) || 180,
      reviewed: Number($("#m-rev").value) || 20,
    });
  } catch (e) { return show("o-match", err(e.message)); }

  const col = scoreColor(d.match_rate);
  const rk = d.rank;
  let h = `<div class="card"><div class="gauge">
    ${dial(d.match_rate, col, "match")}
    <div class="verdict">
      <h3 style="color:${col}">${d.match_rate}% keyword match</h3>
      <p>Hard skills only: <b style="color:var(--txt)">${d.hard_match_rate}%</b> ·
         Parse safety: <b style="color:var(--txt)">${d.format_score}/100</b></p>
      <div class="callout ${rk.would_be_reviewed ? "good" : "bad"}" style="margin-top:12px">
        <b>${esc(rk.note)}</b>
      </div>
    </div></div>
    <div class="callout">${esc(d.honest_note)}</div>
  </div>`;

  h += `<div class="card"><h3>The search a recruiter would actually run</h3>
    <div class="sub">Recruiters query the ATS database with boolean strings. If your resume
      lacks the exact term, you never surface. This is the string for this role.</div>
    <pre class="bool">${esc(d.boolean_string || "No hard skills detected in this JD.")}</pre>
    <div class="callout" style="margin-top:12px">Copy this into a search on your own resume.
      Anything that does not appear is a term you are invisible to.</div></div>`;

  h += `<div class="card"><h3>Missing — in priority order</h3>
    <div class="sub">${d.missing.length} term(s) the job asks for that your resume never states.
      Weight reflects how often the JD repeats it and whether it sits in the requirements block.</div>
    <div class="chips">${d.missing.length
      ? d.missing.map(k => `<span class="chip miss" title="weight ${k.weight} · appears ${k.count}×">${esc(k.term)}</span>`).join("")
      : `<span class="chip hit">Nothing missing. You mirror this JD's language completely.</span>`}</div></div>`;

  h += `<div class="card"><h3>Matched</h3><div class="chips">${d.matched.map(k =>
      `<span class="chip hit">${esc(k.term)}</span>`).join("") || "<span class='chip'>none</span>"}
    </div></div>`;

  if (d.extras_in_resume.length) h += `<div class="card"><h3>Taking up space this job never asked for</h3>
    <div class="sub">Not wrong to have — but every line of resume is scarce. Consider cutting these
      to make room for the missing terms above.</div>
    <div class="chips">${d.extras_in_resume.map(k => `<span class="chip extra">${esc(k)}</span>`).join("")}</div></div>`;

  h += `<div class="card"><h3>Parse &amp; format safety</h3>
    <div class="sub">${esc(d.parse_risk)}</div>
    ${d.format_checks.map(c => `<div class="fc ${c.ok ? "ok" : "no"}">
      <i>${c.ok ? "✓" : "!"}</i><span><b>${esc(c.label)}</b>${esc(c.why)}</span></div>`).join("")}
    </div>`;

  h += `<div class="row"><button class="btn ghost sm" id="match-to-bullets">Fix my bullets →</button>
    <button class="btn ghost sm" id="match-to-follow">Build my follow-up plan →</button></div>`;

  show("o-match", h);
  $("#match-to-bullets").onclick = () => {
    $("#b-resume").value = $("#m-resume").value;
    $$("nav button")[2].click(); runBullets();
  };
  $("#match-to-follow").onclick = () => { $$("nav button")[3].click(); };
}
$("#m-run").onclick = runMatch;

/* ================= 3. BULLET LAB ================= */
$("#b-sample").onclick = () => {
  $("#b-resume").value =
`EXPERIENCE

Customer Support Officer, Brightline Ltd
Jan 2022 - Present
- Responsible for handling customer queries
- Assisted with monthly reporting tasks
- Worked on various database issues
- Was involved in the onboarding process for new clients
- Helped to improve several different processes

EDUCATION
BSc Business Administration`;
  runBullets();
};

async function runBullets() {
  let d;
  try { d = await api("/api/bullets", { resume: $("#b-resume").value }); }
  catch (e) { return show("o-bullets", err(e.message)); }

  if (!d.fixes.length) return show("o-bullets",
    `<div class="card"><div class="callout good"><b>No broken bullets found.</b>
      Either your bullets are already quantified, or they are not formatted with
      "- " or "• " at the start of the line. Paste them with a leading dash.</div></div>`);

  let h = `<div class="card"><h3>${d.fixes.length} bullet(s) need work</h3>
    <div class="sub">Worst offenders first. Answer the question under each one — that answer
      is the number your bullet is missing.</div>`;
  d.fixes.forEach((f, i) => {
    h += `<div class="sig ${f.has_metric ? "medium" : "high"}" style="margin-bottom:14px">
      <h4><span class="tg ${f.has_metric ? "medium" : "high"}">${f.has_metric ? "weak" : "no evidence"}</span>
        <span style="color:var(--dim2);font-weight:500;font-size:11.5px">domain: ${esc(f.domain)} · ${f.word_count} words</span></h4>
      <div class="ev" style="color:var(--dim);background:var(--bg);width:100%">${esc(f.original)}</div>
      <ul style="margin:9px 0 9px 17px">${f.problems.map(p =>
        `<li style="font-size:12.5px;color:var(--dim);margin-bottom:4px">${esc(p)}</li>`).join("")}</ul>
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--dim2);
        font-weight:700;margin:12px 0 5px">Rewrite shape</div>
      <pre class="bool" style="margin:0">${esc(f.scaffold)}</pre>
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--dim2);
        font-weight:700;margin:12px 0 5px">Open with one of these</div>
      <div class="chips">${f.verb_options.map(v => `<span class="chip">${esc(v)}</span>`).join("")}</div>
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--dim2);
        font-weight:700;margin:12px 0 5px">Answer this and the bullet writes itself</div>
      ${f.questions.map(q => `<div style="font-size:12.5px;color:var(--txt);padding:4px 0">→ ${esc(q)}</div>`).join("")}
    </div>`;
  });
  h += `</div>`;
  show("o-bullets", h);
}
$("#b-run").onclick = runBullets;

/* ================= 4. FOLLOW-UP ================= */
$("#f-anchor").value = new Date().toISOString().slice(0, 10);

async function runFollow() {
  let d;
  try {
    d = await api("/api/followup", {
      stage: $("#f-stage").value, anchor: $("#f-anchor").value || null,
      candidate_name: $("#f-you").value, recruiter_name: $("#f-them").value,
      role: $("#f-role").value, company: $("#f-company").value,
      hook: $("#f-hook").value, stated_timeline: $("#f-timeline").value,
    });
  } catch (e) { return show("o-followup", err(e.message)); }

  let h = `<div class="card"><h3>Your chase schedule</h3>
    <div class="sub">${esc(d.strategy_note)}</div>
    <div class="callout good"><b>Why this works:</b> ${esc(d.expected_lift)}</div>
    <div class="tl" style="margin-top:18px">`;

  d.steps.forEach((s, i) => {
    h += `<div class="step">
      <div class="when">${esc(s.date_human)} · ${s.offset_business_days} business day${s.offset_business_days === 1 ? "" : "s"} out</div>
      <h4>${esc(s.label)}</h4>
      <div class="mail">
        <div class="hd"><button class="copy" data-i="${i}">copy all</button>
          <b>Subject:</b> ${esc(s.subject)}<br>
          <span style="color:var(--dim2)">via ${esc(s.channel)}</span></div>
        <pre>${esc(s.body)}</pre>
      </div>
      <div class="why">${esc(s.rationale)}</div>
    </div>`;
  });

  h += `</div>${d.cold_after_human ? `<div class="callout"><b>Give up after
    ${esc(d.cold_after_human)}.</b> 14–21 days of silence means the trail has gone cold.
    Chasing past that costs you emotional energy on a dead requisition.</div>` : ""}</div>`;

  h += `<div class="card"><h3>Which channel to use</h3>
    <div class="sub">Response rates by channel. Portals are write-only — never treat them as a
      conversation.</div>
    <table><thead><tr><th>Channel</th><th>Response rate</th><th>Use when</th><th>Avoid when</th></tr></thead>
    <tbody>${d.channels.map(c => `<tr><td><b>${esc(c.channel)}</b></td>
      <td><b>${esc(c.response_rate)}</b></td><td>${esc(c.use_when)}</td>
      <td>${esc(c.avoid_when)}</td></tr>`).join("")}</tbody></table></div>`;

  show("o-followup", h);
  $$(".copy", $("#o-followup")).forEach(b => b.onclick = () => {
    const s = d.steps[Number(b.dataset.i)];
    navigator.clipboard?.writeText(`Subject: ${s.subject}\n\n${s.body}`);
    b.textContent = "copied ✓"; setTimeout(() => (b.textContent = "copy all"), 1600);
  });
}
$("#f-run").onclick = runFollow;

/* ================= 5. PIPELINE ================= */
$("#p-add").onclick = async () => {
  if (!$("#p-company").value.trim()) return alert("Give it a company name.");
  await api("/api/pipeline", {
    application: {
      company: $("#p-company").value, role: $("#p-role").value || "—",
      stage: $("#p-stage").value, ghost_score: Number($("#p-ghost").value) || 0,
      ghost_verdict: "", match_rate: Number($("#p-match").value) || 0, source: "manual",
    },
  });
  $("#p-company").value = $("#p-role").value = "";
  loadPipeline();
};

async function loadPipeline() {
  const el = $("#o-pipeline");
  let d;
  try { d = await (await fetch("/api/pipeline")).json(); }
  catch (e) { return (el.innerHTML = err(e.message)); }

  const stages = [["found", "Found"], ["vetted", "Vetted"], ["applied", "Applied"],
    ["following_up", "Following up"], ["interview", "Interview"],
    ["offer", "Offer"], ["rejected", "Closed"]];

  if (!d.applications.length) {
    el.innerHTML = `<div class="card"><div class="empty">Nothing tracked yet.
      Run Ghost Radar on a job and save it — every blocked scam shows up here as money
      you did not lose.</div></div>`;
    return;
  }

  let h = `<div class="card"><div class="stats" style="margin:0">
    <div class="stat"><b>${d.applications.length}</b><span>applications tracked</span></div>
    <div class="stat"><b style="color:var(--crit)">${d.blocked_by_ghost_radar}</b><span>blocked by Ghost Radar</span></div>
    <div class="stat"><b style="color:var(--ok)">₦${(d.naira_protected || 0).toLocaleString()}</b><span>protected from fraud demands</span></div>
  </div></div>`;

  h += `<div class="kanban">` + stages.map(([k, label]) => {
    const items = d.applications.filter(a => a.stage === k);
    return `<div class="col"><h4>${label} <b>${items.length}</b></h4>` +
      (items.map(a => `<div class="kcard">
        <b>${esc(a.company)}</b><span>${esc(a.role)}</span>
        <div class="mini">
          ${a.ghost_verdict ? `<em class="${a.ghost_verdict === "CLEAR" || a.ghost_verdict === "LOW RISK" ? "ok" : ""}">${esc(a.ghost_verdict)}</em>` : ""}
          ${a.ghost_score ? `<em class="${a.ghost_score >= 60 ? "" : "m"}">risk ${a.ghost_score}</em>` : ""}
          ${a.match_rate ? `<em class="m">match ${a.match_rate}%</em>` : ""}
        </div></div>`).join("") || `<div style="font-size:11px;color:var(--dim2)">empty</div>`) +
      `</div>`;
  }).join("") + `</div>`;

  h += `<div class="card" style="margin-top:16px"><h3>All tracked applications</h3>
    <table><thead><tr><th>Company</th><th>Role</th><th>Stage</th><th>Ghost</th><th>Match</th><th></th></tr></thead>
    <tbody>${d.applications.map(a => `<tr>
      <td><b>${esc(a.company)}</b></td><td>${esc(a.role)}</td>
      <td><select class="move" data-id="${a.id}" style="padding:5px 26px 5px 8px;font-size:12px">
        ${stages.map(([k, l]) => `<option value="${k}" ${a.stage === k ? "selected" : ""}>${l}</option>`).join("")}
      </select></td>
      <td>${a.ghost_verdict ? esc(a.ghost_verdict) : "—"}</td>
      <td>${a.match_rate ? a.match_rate + "%" : "—"}</td>
      <td><button class="btn ghost sm del" data-id="${a.id}">✕</button></td>
    </tr>`).join("")}</tbody></table></div>`;

  el.innerHTML = h;
  $$(".move", el).forEach(s => s.onchange = async () => {
    await fetch("/api/pipeline/" + s.dataset.id, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ app_id: s.dataset.id, stage: s.value }),
    });
    loadPipeline();
  });
  $$(".del", el).forEach(b => b.onclick = async () => {
    await fetch("/api/pipeline/" + b.dataset.id, { method: "DELETE" });
    loadPipeline();
  });
}

/* ---------------- health ---------------- */
(async () => {
  try {
    const d = await (await fetch("/api/health")).json();
    $("#health").textContent = `engine v${d.version} · ${d.applications_tracked} tracked`;
  } catch (_) { $("#health").textContent = "offline"; }
})();
