function setupSearchFilters() {
    const form = document.getElementById("search-filter-form");
    const results = document.getElementById("search-results");
    const resultCount = document.getElementById("search-result-count");

    if (!form || !results) {
        return;
    }

    const updateFormFromParams = (params) => {
        const orderInput = form.querySelector("input[name='order']");
        const viewInput = form.querySelector("input[name='view']");
        if (orderInput && params.get("order")) {
            orderInput.value = params.get("order");
        }
        if (viewInput && params.get("view")) {
            viewInput.value = params.get("view");
        }
        const sortSelect = document.getElementById("sort-select");
        if (sortSelect && params.get("order")) {
            sortSelect.value = params.get("order");
        }
        const searchInput = form.querySelector("input[name='title_contains_query']");
        if (searchInput && params.has("title_contains_query")) {
            searchInput.value = params.get("title_contains_query");
        }
        const nearbyInput = form.querySelector("input[name='nearby']");
        if (nearbyInput) {
            nearbyInput.checked = params.get("nearby") === "on";
        }
        const categoryValue = params.get("category");
        if (categoryValue) {
            const categoryInput = form.querySelector(`input[name='category'][value="${categoryValue}"]`);
            if (categoryInput) {
                categoryInput.checked = true;
            }
        }
    };

    const syncActiveStates = () => {
        const orderValue = form.querySelector("input[name='order']")?.value;
        const sortSelect = document.getElementById("sort-select");
        if (sortSelect && orderValue) {
            sortSelect.value = orderValue;
        }

        const viewValue = form.querySelector("input[name='view']")?.value;
        document.querySelectorAll(".js-filter-link").forEach((link) => {
            const linkUrl = new URL(link.href, window.location.origin);
            const linkView = linkUrl.searchParams.get("view");
            if (linkView) {
                link.classList.toggle("active", linkView === viewValue);
            }
        });

        form.querySelectorAll("input[name='category']").forEach((input) => {
            const label = form.querySelector(`label[for="${input.id}"]`);
            if (label) {
                label.classList.toggle("text-success", input.checked);
                label.classList.toggle("font-weight-bold", input.checked);
            }
        });

        const nearbyInput = form.querySelector("input[name='nearby']");
        if (nearbyInput) {
            const label = nearbyInput.closest("label");
            if (label) {
                label.classList.toggle("text-success", nearbyInput.checked);
                label.classList.toggle("font-weight-bold", nearbyInput.checked);
            }
        }

        const searchInput = form.querySelector("input[name='title_contains_query']");
        if (searchInput) {
            searchInput.classList.toggle("border", !!searchInput.value);
            searchInput.classList.toggle("border-success", !!searchInput.value);
        }
    };

    const fetchResults = (params) => {
        const query = params.toString();
        const url = `${form.action}?${query}`;

        return fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                results.innerHTML = data.html;
                if (resultCount) {
                    resultCount.textContent = data.count;
                }
                window.history.replaceState({}, "", url);
                syncActiveStates();
            });
    };

    const buildParamsFromForm = () => {
        const formData = new FormData(form);
        return new URLSearchParams(formData);
    };

    const submitFilters = () => {
        const params = buildParamsFromForm();
        fetchResults(params);
    };

    let searchTimeout = null;
    form.addEventListener("input", (event) => {
        if (event.target.name === "title_contains_query") {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(submitFilters, 300);
            return;
        }
        submitFilters();
    });

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        submitFilters();
    });

    document.addEventListener("click", (event) => {
        const link = event.target.closest(".js-filter-link");
        if (!link) {
            return;
        }
        event.preventDefault();
        const url = new URL(link.href, window.location.origin);
        updateFormFromParams(url.searchParams);
        fetchResults(url.searchParams);
    });

    const sortSelect = document.getElementById("sort-select");
    if (sortSelect) {
        sortSelect.addEventListener("change", (event) => {
            const orderInput = form.querySelector("input[name='order']");
            if (orderInput) {
                orderInput.value = event.target.value;
            }
            submitFilters();
        });
    }

    syncActiveStates();
}

document.addEventListener("DOMContentLoaded", setupSearchFilters);
