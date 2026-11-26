const taskList = document.querySelector("#task-list");
const errorMessage = document.querySelector("#error-message");
const exampleTasks = [
  { name: "Requirements", dependencies: "" },
  { name: "Design", dependencies: "Requirements" },
  { name: "Backend", dependencies: "Design" },
  { name: "Frontend", dependencies: "Design" },
  { name: "Integration", dependencies: "Backend, Frontend" },
  { name: "Testing", dependencies: "Integration" },
];

function addTaskRow(task = { name: "", dependencies: "" }) {
  const row = document.createElement("div");
  row.className = "task-row";

  const nameInput = document.createElement("input");
  nameInput.type = "text";
  nameInput.maxLength = 80;
  nameInput.placeholder = "Task name";
  nameInput.setAttribute("aria-label", "Task name");
  nameInput.value = task.name;

  const dependencyInput = document.createElement("input");
  dependencyInput.type = "text";
  dependencyInput.placeholder = "Depends on…";
  dependencyInput.setAttribute("aria-label", "Task dependencies, separated by commas");
  dependencyInput.value = task.dependencies;

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "remove-task";
  removeButton.textContent = "×";
  removeButton.setAttribute("aria-label", "Remove task");
  removeButton.addEventListener("click", () => {
    row.remove();
    hideError();
  });

  row.append(nameInput, dependencyInput, removeButton);
  taskList.append(row);
}

function loadExample() {
  taskList.replaceChildren();
  exampleTasks.forEach(addTaskRow);
  hideError();
}

function hideError() {
  errorMessage.hidden = true;
  errorMessage.textContent = "";
}

function getTasks() {
  return [...taskList.querySelectorAll(".task-row")].map((row) => {
    const [nameInput, dependencyInput] = row.querySelectorAll("input");
    const dependencies = dependencyInput.value
      .split(",")
      .map((dependency) => dependency.trim())
      .filter(Boolean);
    return { name: nameInput.value.trim(), dependencies };
  });
}

function setOrder(list, order) {
  list.replaceChildren();
  for (const task of order || []) {
    const item = document.createElement("li");
    item.textContent = task;
    list.append(item);
  }
}

function renderAlgorithm(key, result) {
  const order = document.querySelector(`#${key}-order`);
  const cycle = document.querySelector(`#${key}-cycle`);
  const runtime = document.querySelector(`#${key}-time`);
  setOrder(order, result.order);
  cycle.hidden = !result.cycle && !result.blocked;
  cycle.textContent = result.cycle
    ? `Cycle path: ${result.cycle.join(" → ")}`
    : result.blocked
      ? `Unscheduled tasks: ${result.blocked.join(", ")}`
    : "";
  runtime.textContent = result.timeMs === undefined ? "cycle found" : `${result.timeMs} ms`;
}

function renderResults(data) {
  document.querySelector("#empty-state").hidden = true;
  document.querySelector("#results").hidden = false;
  document.querySelector("#task-count").textContent = data.taskCount;
  document.querySelector("#dependency-count").textContent = data.dependencyCount;
  document.querySelector("#schedule-status").textContent = data.cycle ? "Blocked" : "Ready";
  document.querySelector("#schedule-status").style.color = data.cycle ? "#ffaaa1" : "";

  const banner = document.querySelector("#cycle-banner");
  banner.hidden = !data.cycle;
  banner.textContent = data.cycle
    ? `Circular dependency detected: ${data.cycle.join(" → ")}. Break the cycle to create an execution plan.`
    : "";
  renderAlgorithm("kahn", data.results.kahn);
  renderAlgorithm("dfs", data.results.dfs);
}

document.querySelector("#add-task").addEventListener("click", () => addTaskRow());
document.querySelector("#reset-button").addEventListener("click", loadExample);

document.querySelector("#analyze-button").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.querySelector("span").textContent = "Analyzing…";
  hideError();
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tasks: getTasks() }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not analyze these tasks.");
    renderResults(data);
  } catch (error) {
    errorMessage.textContent = error.message || "Could not reach the local server.";
    errorMessage.hidden = false;
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Generate execution plan";
  }
});

document.querySelector("#benchmark-button").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const output = document.querySelector("#benchmark-output");
  button.disabled = true;
  button.firstChild.textContent = "Running… ";
  try {
    const response = await fetch("/api/benchmark", { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Benchmark failed.");
    output.replaceChildren();
    for (const run of data.runs) {
      const cell = document.createElement("div");
      cell.className = "benchmark-cell";
      const heading = document.createElement("strong");
      heading.textContent = `${run.taskCount.toLocaleString()} tasks`;
      const dependencies = document.createElement("span");
      dependencies.textContent = `${run.dependencyCount.toLocaleString()} edges`;
      const kahn = document.createElement("span");
      kahn.className = "benchmark-kahn";
      kahn.textContent = `Kahn BFS  ${run.kahnMs} ms`;
      const dfs = document.createElement("span");
      dfs.className = "benchmark-dfs";
      dfs.textContent = `DFS  ${run.dfsMs} ms`;
      cell.append(heading, dependencies, kahn, dfs);
      output.append(cell);
    }
    output.hidden = false;
  } catch (error) {
    errorMessage.textContent = error.message || "Could not reach the local server.";
    errorMessage.hidden = false;
  } finally {
    button.disabled = false;
    button.firstChild.textContent = "Run benchmark ";
  }
});

loadExample();
