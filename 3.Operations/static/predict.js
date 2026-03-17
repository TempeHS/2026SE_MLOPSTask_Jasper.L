document
  .getElementById("predictForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault(); // Stop normal form submission
    document.getElementById("error").textContent = "";

    const formData = new FormData(this);
    const data = {};
    formData.forEach((value, key) => {
      if (key !== "csrf_token") {
        data[key] = parseFloat(value) || 0;
      }
    });

    // Include CSRF token in headers
    const csrfToken = formData.get("csrf_token");

    const res = await fetch("/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    });

    const json = await res.json();
    if (json.error) {
      document.getElementById("error").textContent = json.error;
    } else {
      document.getElementById("biome").textContent = json.biome.replace(
        /_/g,
        " ",
      );
      document.getElementById("confidence").textContent =
        `Confidence: ${json.confidence}%`;
      document.getElementById("result").style.display = "block";

      // Show out-of-range warnings if any
      if (json.warnings && json.warnings.length > 0) {
        document.getElementById("error").textContent =
          "⚠️ Some values were outside training range and clamped: " +
          json.warnings.join(", ");
      }
    }
  });

function resetForm() {
  document.getElementById("predictForm").reset();
  document.getElementById("result").style.display = "none";
  document.getElementById("error").textContent = "";
}
