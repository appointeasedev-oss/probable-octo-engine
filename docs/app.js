const latestRunEl = document.getElementById("latest-run");
const runListEl = document.getElementById("run-list");
const chartEl = document.getElementById("success-chart");

function renderLatest(run) {
  if (!run) {
    latestRunEl.textContent = "No runs recorded yet.";
    return;
  }
  latestRunEl.textContent = [
    `Run #${run.run_id}`,
    `Timestamp: ${run.timestamp}`,
    `Improvement: ${run.improvement_id}`,
    `Summary: ${run.summary}`,
    `Verification: ${run.verification_success ? "passed" : "failed"}`,
  ].join("\n");
}

function renderRunList(runs) {
  runListEl.innerHTML = "";
  runs.slice().reverse().forEach((run) => {
    const li = document.createElement("li");
    li.textContent = `#${run.run_id} | ${run.timestamp} | ${run.improvement_id} | ${run.verification_success ? "PASS" : "FAIL"}`;
    runListEl.appendChild(li);
  });
}

function renderChart(runs) {
  const ctx = chartEl.getContext("2d");
  ctx.clearRect(0, 0, chartEl.width, chartEl.height);

  const padding = 20;
  const width = chartEl.width - padding * 2;
  const height = chartEl.height - padding * 2;

  ctx.strokeStyle = "#d6d6d6";
  ctx.strokeRect(padding, padding, width, height);

  if (!runs.length) {
    ctx.fillStyle = "#5c5c5c";
    ctx.fillText("No data yet", padding + 8, padding + 20);
    return;
  }

  const maxRuns = Math.max(runs.length - 1, 1);
  runs.forEach((run, index) => {
    const x = padding + (index / maxRuns) * width;
    const y = run.verification_success ? padding + height * 0.2 : padding + height * 0.8;
    ctx.fillStyle = run.verification_success ? "#2f7d32" : "#c62828";
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fill();
  });
}

fetch("data.json")
  .then((response) => response.json())
  .then((data) => {
    const runs = data.runs || [];
    renderLatest(runs[runs.length - 1]);
    renderRunList(runs);
    renderChart(runs);
  })
  .catch(() => {
    latestRunEl.textContent = "Failed to load dashboard data.";
  });
