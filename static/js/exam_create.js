document.addEventListener("DOMContentLoaded", function () {
    const totalInput = document.getElementById("id_total");
    const levelInputs = document.querySelectorAll(".level-input");
    const display = document.getElementById("remaining-display");
    const submitBtn = document.getElementById("submit-btn");

    if (!totalInput || !display) return;

    function updateRemaining() {
        const total = parseInt(totalInput.value) || 0;
        let sum = 0;
        levelInputs.forEach(function (input) {
            sum += parseInt(input.value) || 0;
        });

        const remaining = total - sum;

        if (remaining === 0 && total > 0) {
            display.textContent = "Tamam, toplam eşleşti.";
            display.className = "ok";
            if (submitBtn) submitBtn.disabled = false;
        } else if (remaining < 0) {
            display.textContent = `Toplamı ${Math.abs(remaining)} soru aştınız.`;
            display.className = "error";
            if (submitBtn) submitBtn.disabled = true;
        } else {
            display.textContent = `Kalan: ${remaining} soru`;
            display.className = "error";
            if (submitBtn) submitBtn.disabled = true;
        }
    }

    totalInput.addEventListener("input", updateRemaining);
    levelInputs.forEach(function (input) {
        input.addEventListener("input", updateRemaining);
    });

    updateRemaining();
});