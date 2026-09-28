const $ = id => document.getElementById(id);
const money = cents => new Intl.NumberFormat("en-US", {style:"currency", currency:"USD"}).format(cents / 100);
let projects = [];
let saving = false;
// Keep a request ID on an uncertain network result, so a retry cannot add another row.
let submissionId = crypto.randomUUID();
let completed = false;
function message(text, error=false) { $("message").textContent = text; $("message").className = error ? "error" : ""; }
async function api(path, method="GET", body) {
  const response = await fetch("/api/" + path, {method, headers:{"Content-Type":"application/json"}, body:body ? JSON.stringify(body) : undefined});
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== "login") { $("workspace").hidden = true; $("auth").hidden = false; }
    throw new Error(Array.isArray(data.detail) ? data.detail.map(e => e.loc.at(-1) + ": " + e.msg).join("; ") : data.detail);
  }
  return data;
}
async function loadHistory() {
  const rows = await api("timesheets");
  $("history").replaceChildren();
  $("empty").hidden = rows.length > 0;
  rows.forEach(row => {
    const tr = document.createElement("tr");
    [row.id,row.project_name,row.working_date,row.hours,money(row.rate_cents),money(row.amount_cents)].forEach(value => {
      const td = document.createElement("td"); td.textContent = value; tr.append(td);
    });
    $("history").append(tr);
  });
}
async function loadWorkspace() {
  const user = await api("me");
  $("employee").textContent = user.email;
  projects = await api("projects");
  $("project").replaceChildren(new Option("Select a project", ""));
  projects.forEach(p => $("project").add(new Option(p.name + " · " + money(p.rate_cents) + "/hr", p.id)));
  $("timesheet").reset(); submissionId = crypto.randomUUID(); completed = false; $("estimate").textContent = money(0);
  await loadHistory(); $("auth").hidden = true; $("workspace").hidden = false;
}
$("login").addEventListener("submit", async event => {
  event.preventDefault();
  try { await api("login", "POST", {email:$("login-email").value,password:$("login-password").value}); await loadWorkspace(); message("You are logged in."); } catch (error) { message(error.message, true); }
});
$("register").addEventListener("submit", async event => {
  event.preventDefault();
  try { const result = await api("register", "POST", {email:$("register-email").value,password:$("register-password").value}); message(result.message); $("register").reset(); } catch (error) { message(error.message, true); }
});
$("logout").addEventListener("click", async () => {
  try { await api("logout", "POST"); $("workspace").hidden = true; $("auth").hidden = false; $("history").replaceChildren(); $("login").reset(); message("Logged out."); } catch (error) { message(error.message, true); }
});
$("timesheet").addEventListener("input", () => {
  if (completed) { submissionId = crypto.randomUUID(); completed = false; }
  const project = projects.find(p => p.id === Number($("project").value));
  $("estimate").textContent = money((project?.rate_cents || 0) * Number($("hours").value));
});
$("timesheet").addEventListener("submit", async event => {
  event.preventDefault();
  if (saving) return;
  saving = true; $("save").disabled = true;
  // Lock fields until the request settles, keeping this request's identity stable.
  const fields = [$("project"), $("working-date"), $("hours")];
  fields.forEach(field => field.disabled = true);
  try {
    const row = await api("timesheets", "POST", {project_id:Number($("project").value),working_date:$("working-date").value,hours:Number($("hours").value),submission_id:submissionId});
    completed = true; message("Timesheet #" + row.id + " saved. Amount: " + money(row.amount_cents));
    $("timesheet").reset(); $("estimate").textContent = money(0); await loadHistory();
  } catch (error) { message(error.message, true); }
  finally { saving = false; $("save").disabled = false; fields.forEach(field => field.disabled = false); }
});
loadWorkspace().catch(error => { if (error.message !== "Please log in.") message(error.message, true); });
