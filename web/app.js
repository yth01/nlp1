const state = {
  scenarioId: "hotel_lobby_crisis",
  scenarios: [],
};

const elements = {
  scenarioSelect: document.querySelector("#scenarioSelect"),
  level: document.querySelector("#level"),
  title: document.querySelector("#title"),
  context: document.querySelector("#context"),
  transcript: document.querySelector("#transcript"),
  staffLine: document.querySelector("#staffLine"),
  responseGoal: document.querySelector("#responseGoal"),
  form: document.querySelector("#responseForm"),
  response: document.querySelector("#response"),
  finalScore: document.querySelector("#finalScore"),
  semanticScore: document.querySelector("#semanticScore"),
  nuanceScore: document.querySelector("#nuanceScore"),
  ratingLine: document.querySelector("#ratingLine"),
  contextExplanation: document.querySelector("#contextExplanation"),
  intentMatch: document.querySelector("#intentMatch"),
  socialNuance: document.querySelector("#socialNuance"),
  businessAppropriateness: document.querySelector("#businessAppropriateness"),
  improvements: document.querySelector("#improvements"),
  grammarFeedback: document.querySelector("#grammarFeedback"),
  rubricBreakdown: document.querySelector("#rubricBreakdown"),
  betterResponse: document.querySelector("#betterResponse"),
  button: document.querySelector("button"),
};

function resetResult() {
  elements.finalScore.textContent = "--";
  elements.semanticScore.textContent = "--";
  elements.nuanceScore.textContent = "--";
  elements.ratingLine.textContent = "Submit a response to see situational feedback.";
  elements.contextExplanation.textContent = "--";
  elements.intentMatch.textContent = "--";
  elements.socialNuance.textContent = "--";
  elements.businessAppropriateness.textContent = "--";
  elements.improvements.replaceChildren();
  elements.grammarFeedback.replaceChildren();
  elements.rubricBreakdown.replaceChildren();
  elements.betterResponse.textContent = "--";
}

async function loadScenarios() {
  const response = await fetch("/api/scenarios");
  state.scenarios = await response.json();
  elements.scenarioSelect.replaceChildren(
    ...state.scenarios.map((scenario) => {
      const option = document.createElement("option");
      option.value = scenario.id;
      option.textContent = scenario.title;
      return option;
    }),
  );
  elements.scenarioSelect.value = state.scenarioId;
}

async function loadScenario() {
  const response = await fetch(`/api/scenarios/${state.scenarioId}`);
  const scenario = await response.json();
  elements.level.textContent = scenario.level;
  elements.title.textContent = scenario.title;
  elements.context.textContent = scenario.context;
  elements.transcript.replaceChildren(
    ...(scenario.transcript || []).map((turn) => {
      const row = document.createElement("div");
      row.className = "transcript-turn";

      const speaker = document.createElement("strong");
      speaker.textContent = turn.speaker;

      const line = document.createElement("p");
      line.textContent = turn.line;

      row.append(speaker, line);
      return row;
    }),
  );
  elements.staffLine.textContent = scenario.pause_line || scenario.staff_line;
  elements.responseGoal.textContent = scenario.response_goal || "";
  elements.response.value = "";
  resetResult();
}

function renderResult(result) {
  elements.finalScore.textContent = result.scores.final_score;
  elements.semanticScore.textContent = result.scores.semantic_score;
  elements.nuanceScore.textContent = result.scores.nuance_score;
  elements.ratingLine.textContent = result.feedback.rating_line;
  elements.contextExplanation.textContent = result.feedback.context_explanation;
  elements.intentMatch.textContent = result.feedback.intent_match;
  elements.socialNuance.textContent = result.feedback.social_nuance;
  elements.businessAppropriateness.textContent = result.feedback.business_appropriateness;
  elements.betterResponse.textContent = result.feedback.better_response;
  elements.improvements.replaceChildren(
    ...result.feedback.improvements.map((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      return li;
    }),
  );
  elements.grammarFeedback.replaceChildren(
    ...result.feedback.grammar_feedback.map((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      return li;
    }),
  );
  elements.rubricBreakdown.replaceChildren(
    ...result.scores.rubric_breakdown.map((item) => {
      const row = document.createElement("div");
      row.className = "rubric-item";

      const top = document.createElement("div");
      const label = document.createElement("strong");
      label.textContent = item.label;
      const score = document.createElement("span");
      score.textContent = `${item.score}`;
      top.append(label, score);

      const bar = document.createElement("div");
      bar.className = "rubric-bar";
      const fill = document.createElement("i");
      fill.style.width = `${item.score}%`;
      bar.append(fill);

      row.append(top, bar);
      return row;
    }),
  );
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.button.disabled = true;
  elements.button.textContent = "Evaluating...";

  try {
    const response = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_id: state.scenarioId,
        response: elements.response.value,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Evaluation failed");
    }
    renderResult(result);
  } catch (error) {
    elements.ratingLine.textContent = error.message;
    elements.contextExplanation.textContent = "--";
    elements.intentMatch.textContent = "--";
    elements.socialNuance.textContent = "--";
    elements.businessAppropriateness.textContent = "--";
    elements.improvements.replaceChildren();
    elements.grammarFeedback.replaceChildren();
    elements.rubricBreakdown.replaceChildren();
    elements.betterResponse.textContent = "--";
  } finally {
    elements.button.disabled = false;
    elements.button.textContent = "Evaluate Response";
  }
});

elements.scenarioSelect.addEventListener("change", () => {
  state.scenarioId = elements.scenarioSelect.value;
  loadScenario();
});

loadScenarios().then(loadScenario);
