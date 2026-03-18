const API_BASE_URL = "https://SEU-BACKEND-AQUI.onrender.com";

let currentStep = 1;
const totalSteps = 5;
let isSubmitting = false;

const quizAnswers = {
  surname_italian: "",
  ancestor_born_italy: "",
  family_documents: "",
  state: ""
};

function updateProgress() {
  const progressText = document.getElementById("progressText");
  const progressFill = document.getElementById("progressFill");

  const progressPercent = (currentStep / totalSteps) * 100;

  if (progressText) {
    progressText.textContent = `Etapa ${currentStep} de ${totalSteps}`;
  }

  if (progressFill) {
    progressFill.style.width = `${progressPercent}%`;
  }
}

function scrollToQuizTop() {
  const quizSection = document.getElementById("quiz");
  if (quizSection) {
    quizSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function goToStep(nextStepNumber) {
  if (nextStepNumber < 1 || nextStepNumber > totalSteps) return;

  const current = document.getElementById(`step${currentStep}`);
  const next = document.getElementById(`step${nextStepNumber}`);

  if (current) current.classList.remove("active");
  if (next) next.classList.add("active");

  currentStep = nextStepNumber;
  updateProgress();

  setTimeout(() => {
    scrollToQuizTop();
  }, 80);
}

function selectAnswer(field, value, nextStepNumber, buttonElement) {
  if (!buttonElement) return;

  quizAnswers[field] = value;

  const answersContainer = buttonElement.parentElement;
  const buttons = answersContainer.querySelectorAll(".answer-btn");

  buttons.forEach((btn) => {
    btn.classList.remove("selected");
    btn.disabled = true;
  });

  buttonElement.classList.add("selected");

  setTimeout(() => {
    goToStep(nextStepNumber);

    buttons.forEach((btn) => {
      btn.disabled = false;
    });
  }, 180);
}

function nextStep() {
  if (currentStep === 4) {
    const stateInput = document.getElementById("state");
    const stateValue = stateInput ? stateInput.value.trim() : "";

    if (!stateValue) {
      alert("Digite seu estado para continuar.");
      if (stateInput) stateInput.focus();
      return;
    }

    quizAnswers.state = stateValue;
    goToStep(5);
    return;
  }

  if (currentStep < totalSteps) {
    goToStep(currentStep + 1);
  }
}

async function sendLead() {
  if (isSubmitting) return;

  const nameInput = document.getElementById("name");
  const phoneInput = document.getElementById("phone");
  const submitButton = document.querySelector("#step5 .primary-btn");

  const name = nameInput ? nameInput.value.trim() : "";
  const phone = phoneInput ? phoneInput.value.trim() : "";

  if (!name) {
    alert("Preencha seu nome.");
    if (nameInput) nameInput.focus();
    return;
  }

  if (!phone) {
    alert("Preencha seu WhatsApp.");
    if (phoneInput) phoneInput.focus();
    return;
  }

  try {
    isSubmitting = true;

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Enviando...";
    }

    const response = await fetch(`${API_BASE_URL}/lead`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        name: name,
        phone: phone,
        quiz_answers: quizAnswers
      })
    });

    if (!response.ok) {
      throw new Error("Erro ao enviar lead");
    }

    const step5 = document.getElementById("step5");
    const success = document.getElementById("success");
    const progressText = document.getElementById("progressText");
    const progressFill = document.getElementById("progressFill");

    if (step5) step5.classList.remove("active");
    if (success) success.style.display = "block";

    if (progressText) {
      progressText.textContent = "Análise enviada";
    }

    if (progressFill) {
      progressFill.style.width = "100%";
    }

    scrollToQuizTop();
  } catch (error) {
    console.error(error);
    alert("Erro ao enviar os dados.");

    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = "Receber análise gratuita";
    }

    isSubmitting = false;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  updateProgress();

  window.selectAnswer = selectAnswer;
  window.nextStep = nextStep;
  window.sendLead = sendLead;
});