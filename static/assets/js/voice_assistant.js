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

  const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i += 1) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === `${name}=`) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  const getRecognitionLang = () => {
    const documentLang = document.documentElement.lang?.trim();
    const fallbackLang = navigator.language || "en-US";

    if (!documentLang || documentLang === "zxx" || documentLang === "und") {
      return fallbackLang;
    }

    return documentLang;
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

  const buildSearchQuery = (payload, transcript) => {
    if (!payload || payload.intent !== "PRODUCT_SEARCH") {
      return cleanSearchQuery(transcript);
    }

    const items = (payload.entities && payload.entities.items) || [];
    const query = (payload.entities && payload.entities.query) || "";
    const maxPrice = payload.entities ? payload.entities.max_price : null;

    const parts = [];
    if (items.length) {
      parts.push(items.join(" "));
    } else if (query) {
      parts.push(query);
    }
    if (maxPrice) {
      parts.push(`under ${maxPrice}`);
    }

    return parts.length ? parts.join(" ").trim() : cleanSearchQuery(transcript);
  };

  const submitSearchTranscript = (transcript, input, statusElement, form) => {
    if (!input) {
      updateStatus(statusElement, "Unable to find the search field.");
      return;
    }

    const csrfToken = getCookie("csrftoken");
    if (!csrfToken || !window.fetch) {
      const cleaned = cleanSearchQuery(transcript);
      input.value = cleaned;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      updateStatus(statusElement, `Searching for “${cleaned}”.`);
      if (form) {
        form.submit();
      }
      return;
    }

    updateStatus(statusElement, "Interpreting your request...");

    fetch("/voice/interpret/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ text: transcript }),
    })
      .then((response) => response.json())
      .then((data) => {
        const query = buildSearchQuery(data, transcript);
        input.value = query;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        updateStatus(statusElement, `Searching for “${query}”.`);
        if (form) {
          form.submit();
        }
      })
      .catch(() => {
        const cleaned = cleanSearchQuery(transcript);
        input.value = cleaned;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        updateStatus(statusElement, `Searching for “${cleaned}”.`);
        if (form) {
          form.submit();
        }
      });
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

    submitSearchTranscript(transcript, input, statusElement, form);
  };

  const startRecognition = (button, statusElement) => {
    if (!supportsSpeech) {
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = getRecognitionLang();
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
