document
  .getElementById("predictForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    const errorDiv = document.getElementById("error");
    errorDiv.style.display = "none";
    errorDiv.textContent = "";

    const formData = new FormData(this);
    const data = {};
    formData.forEach((value, key) => {
      if (key !== "csrf_token") {
        data[key] = parseFloat(value) || 0;
      }
    });

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
      errorDiv.textContent = json.error;
      errorDiv.style.display = "block";
    } else {
      document.getElementById("biome").textContent = json.biome.replace(
        /_/g,
        " ",
      );
      document.getElementById("confidence").textContent =
        `Confidence: ${json.confidence}%`;
      document.getElementById("result").style.display = "block";

      if (json.warnings && json.warnings.length > 0) {
        errorDiv.textContent =
          "⚠️ Some values were outside training range and clamped: " +
          json.warnings.join(", ");
        errorDiv.style.display = "block";
      }
    }
  });

function resetForm() {
  // Reset each input to its median value instead of 0
  document
    .querySelectorAll("#predictForm input[type='number']")
    .forEach((input) => {
      const min = parseFloat(input.min) || 0;
      const max = parseFloat(input.dataset.max) || 0;
      input.value = Math.floor((min + max) / 2);
    });
  document.getElementById("result").style.display = "none";
  const errorDiv = document.getElementById("error");
  errorDiv.style.display = "none";
  errorDiv.textContent = "";
}
