const statusEl = document.getElementById("status");
const imagePreview = document.getElementById("image-preview");
const fileInput = document.getElementById("file-input");
const cameraInput = document.getElementById("camera-input");
const assessButton = document.getElementById("assess-button");
const resultCard = document.getElementById("result-card");
const riskBadge = document.getElementById("risk-badge");
const riskScore = document.getElementById("risk-score");
const riskExplanation = document.getElementById("risk-explanation");
const signalsList = document.getElementById("signals-list");
const stepsList = document.getElementById("steps-list");
const resultDisclaimer = document.getElementById("result-disclaimer");
const reportedPain = document.getElementById("reported-pain");
const reportedWarmth = document.getElementById("reported-warmth");
const reportedSwelling = document.getElementById("reported-swelling");
const reportedDrainage = document.getElementById("reported-drainage");
const reportedSpreadingRedness = document.getElementById("reported-spreading-redness");

const settingsModal = document.getElementById("settings-modal");
const settingsButton = document.getElementById("settings-button");
const settingsClose = document.getElementById("settings-close");
const backendUrlInput = document.getElementById("backend-url");
const testConnectionButton = document.getElementById("test-connection");
const useCurrentButton = document.getElementById("use-current");
const connectionStatus = document.getElementById("connection-status");

const limitationsModal = document.getElementById("limitations-modal");
const limitationsButton = document.getElementById("limitations-button");
const limitationsClose = document.getElementById("limitations-close");

let selectedFile = null;

const STORAGE_KEY = "backendURL";
const storage = {
  get(key) {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      return "";
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (error) {
      // Ignore storage errors in restricted environments.
    }
  },
};

backendUrlInput.value = storage.get(STORAGE_KEY) || "";

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function setConnectionStatus(message, isError = false) {
  connectionStatus.textContent = message;
  connectionStatus.classList.toggle("error", isError);
}

function openModal(modal) {
  modal.hidden = false;
}

function closeModal(modal) {
  modal.hidden = true;
}

function handleFile(file) {
  if (!file) {
    return;
  }
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (event) => {
    imagePreview.innerHTML = "";
    const img = document.createElement("img");
    img.src = event.target.result;
    imagePreview.appendChild(img);
  };
  reader.readAsDataURL(file);
}

fileInput.addEventListener("change", (event) => {
  handleFile(event.target.files[0]);
});

cameraInput.addEventListener("change", (event) => {
  handleFile(event.target.files[0]);
});

settingsButton.addEventListener("click", () => openModal(settingsModal));
settingsClose.addEventListener("click", () => closeModal(settingsModal));
limitationsButton.addEventListener("click", () => openModal(limitationsModal));
limitationsClose.addEventListener("click", () => closeModal(limitationsModal));

settingsModal.addEventListener("click", (event) => {
  if (event.target === settingsModal) {
    closeModal(settingsModal);
  }
});

limitationsModal.addEventListener("click", (event) => {
  if (event.target === limitationsModal) {
    closeModal(limitationsModal);
  }
});

backendUrlInput.addEventListener("input", () => {
  storage.set(STORAGE_KEY, backendUrlInput.value.trim());
});

useCurrentButton.addEventListener("click", () => {
  backendUrlInput.value = window.location.origin;
  storage.set(STORAGE_KEY, backendUrlInput.value);
});

async function testConnection() {
  const backendUrl = backendUrlInput.value.trim();
  if (!backendUrl) {
    setConnectionStatus("Enter a backend URL in Settings.", true);
    return;
  }

  setConnectionStatus("Checking...");
  try {
    const response = await fetch(`${backendUrl}/health`);
    if (!response.ok) {
      throw new Error("Backend unavailable");
    }
    setConnectionStatus("Connected", false);
  } catch (error) {
    setConnectionStatus("Unavailable", true);
  }
}

testConnectionButton.addEventListener("click", testConnection);

function buildList(listElement, items) {
  listElement.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    listElement.appendChild(li);
  });
}

function showResult(result) {
  resultCard.hidden = false;
  const level = result.risk_level || result.riskLevel;
  riskBadge.textContent = level;
  riskBadge.classList.remove("low", "medium", "high");
  riskBadge.classList.add(level);
  riskScore.textContent = Number(result.risk_score ?? result.riskScore).toFixed(2);
  riskExplanation.textContent = result.explanation;

  const signals = result.signals.map(
    (signal) =>
      `• ${signal.name.replace(/_/g, " ")}: ${Number(signal.value).toFixed(2)}`
  );
  buildList(signalsList, signals);

  buildList(stepsList, result.recommended_next_steps || result.recommendedNextSteps);
  resultDisclaimer.textContent = result.disclaimer;
}

function localDemoAssessment(imageData, questionnaire) {
  const weights = {
    reported_pain: 0.06,
    reported_warmth: 0.08,
    reported_swelling: 0.06,
    reported_drainage: 0.12,
    reported_spreading_redness: 0.1,
  };
  let score = imageData.avgRed;
  const signals = [
    {
      name: "local_demo",
      value: score,
      weight: 1.0,
      note: "Local-only heuristic signal.",
    },
  ];

  Object.entries(questionnaire).forEach(([key, value]) => {
    const weight = weights[key] ?? 0.0;
    score += weight * (value ? 1 : 0);
    signals.push({
      name: key,
      value: value ? 1.0 : 0.0,
      weight,
      note: "User-reported symptom.",
    });
  });

  score = Math.min(Math.max(score, 0), 1);
  const level = score >= 0.66 ? "high" : score >= 0.33 ? "medium" : "low";
  return {
    risk_score: score,
    risk_level: level,
    signals,
    explanation:
      "Local-only demo estimate based on average color intensity. Not diagnostic.",
    disclaimer: "This output is a non-diagnostic risk estimation for triage support only.",
    recommended_next_steps: [
      "Monitor changes over time.",
      "Seek clinical guidance if you are concerned.",
    ],
  };
}

async function computeAverageRed(file) {
  const img = new Image();
  const url = URL.createObjectURL(file);
  img.src = url;
  await img.decode();
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  canvas.width = img.width;
  canvas.height = img.height;
  ctx.drawImage(img, 0, 0);
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let redSum = 0;
  for (let i = 0; i < data.length; i += 4) {
    redSum += data[i];
  }
  URL.revokeObjectURL(url);
  const avgRed = redSum / (data.length / 4) / 255;
  return { avgRed: Math.min(Math.max(avgRed, 0), 1) };
}

function buildQuestionnairePayload() {
  return {
    reported_pain: reportedPain.checked,
    reported_warmth: reportedWarmth.checked,
    reported_swelling: reportedSwelling.checked,
    reported_drainage: reportedDrainage.checked,
    reported_spreading_redness: reportedSpreadingRedness.checked,
  };
}

function appendQuestionnaire(formData) {
  const questionnaire = buildQuestionnairePayload();
  Object.entries(questionnaire).forEach(([key, value]) => {
    formData.append(key, value ? "true" : "false");
  });
}

async function assessRisk() {
  if (!selectedFile) {
    setStatus("Please select an image first.", true);
    return;
  }

  setStatus("Analyzing...");
  resultCard.hidden = true;

  const backendUrl = backendUrlInput.value.trim();
  if (!backendUrl) {
    const imageData = await computeAverageRed(selectedFile);
    const questionnaire = buildQuestionnairePayload();
    const result = localDemoAssessment(imageData, questionnaire);
    setStatus("Local-only demo estimate.");
    showResult(result);
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);
  appendQuestionnaire(formData);

  try {
    const response = await fetch(`${backendUrl}/assess`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error("Backend unavailable");
    }
    const result = await response.json();
    setStatus("Analysis complete.");
    showResult(result);
  } catch (error) {
    const imageData = await computeAverageRed(selectedFile);
    const questionnaire = buildQuestionnairePayload();
    const result = localDemoAssessment(imageData, questionnaire);
    setStatus("Backend unavailable. Showing local-only demo estimate.", true);
    showResult(result);
  }
}

assessButton.addEventListener("click", () => {
  assessRisk();
});
