(() => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const voiceContainers = document.querySelectorAll("[data-voice-container]");

  if (!voiceContainers.length) {
    return;
  }

  const supportsSpeech = Boolean(SpeechRecognition);

  const updateStatus = (statusElement, message) => {
    if (statusElement) {
      statusElement.textContent = message;
    }
  };

  const findInput = (button, target) => {
    if (!target) {
      return null;
    }

    let input = document.getElementById(target);

    if (!input) {
      input = button.closest("form")?.querySelector(`[name="${target}"]`) || null;
    }

    return input;
  };

  const cleanSearchQuery = (text) =>
    text
      .replace(/^(search for|search|find|look for|show me|show)\s+/i, "")
      .trim();

  const extractAmount = (text) => {
    const normalized = text.replace(/,/g, "");
    const match = normalized.match(/(\d+(?:\.\d{1,2})?)/);
    return match ? match[1] : null;
  };

  const handleTranscript = (action, transcript, input, statusElement, form) => {
    if (!transcript) {
      updateStatus(statusElement, "Sorry, we did not catch that.");
      return;
    }

    if (action === "budget") {
      const amount = extractAmount(transcript);

      if (!amount) {
        updateStatus(statusElement, "Say a number like \u201cset budget to 50\u201d.");
        return;
      }

      if (input) {
        input.value = amount;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
      }

      updateStatus(statusElement, `Budget set to \u00a3${amount}.`);
      return;
    }

    const cleaned = cleanSearchQuery(transcript);

    if (input) {
      input.value = cleaned;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }

    updateStatus(statusElement, `Searching for \u201c${cleaned}\u201d.`);

    if (form) {
      form.submit();
    }
  };

  const startRecognition = (button, statusElement) => {
    if (!supportsSpeech) {
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = document.documentElement.lang || "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    const action = button.dataset.voiceAction;
    const target = button.dataset.voiceInput;
    const input = findInput(button, target);
    const form = input ? input.closest("form") : null;

    recognition.onstart = () => {
      button.classList.add("is-listening");
      updateStatus(statusElement, "Listening...");
    };

    recognition.onend = () => {
      button.classList.remove("is-listening");
    };

    recognition.onerror = () => {
      updateStatus(
        statusElement,
        "We could not access the microphone. Please check permissions."
      );
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      handleTranscript(action, transcript, input, statusElement, form);
    };

    recognition.start();
  };

  voiceContainers.forEach((container) => {
    const button = container.querySelector("[data-voice-action]");
    const statusElement = container.querySelector("[data-voice-status]");

    if (!button) {
      return;
    }

    if (!supportsSpeech) {
      button.disabled = true;
      button.classList.add("is-disabled");
      updateStatus(
        statusElement,
        "Voice input is not supported in this browser."
      );
      return;
    }

    button.addEventListener("click", () => {
      startRecognition(button, statusElement);
    });
  });
})();
