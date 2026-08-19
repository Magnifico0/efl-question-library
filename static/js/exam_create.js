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

document.addEventListener("DOMContentLoaded", function () {

    function setupPassageSection(prefix) {
        const perPassageInput = document.getElementById(`id_${prefix}_questions_per_passage`);
        const totalInput = document.getElementById(`id_${prefix}_questions_total`);
        const computedDisplay = document.getElementById(`${prefix}-computed-total`);
        const passageCountInput = document.getElementById(`id_${prefix}_passage_count`);

        if (!perPassageInput || !totalInput || !passageCountInput) return;

        function updateSection() {
            const perPassageValue = parseInt(perPassageInput.value) || 0;
            const totalValue = parseInt(totalInput.value) || 0;
            const passageCount = parseInt(passageCountInput.value) || 0;

            // Karşılıklı devre dışı bırakma: biri doluysa diğeri kilitlensin
            if (perPassageValue > 0) {
                totalInput.disabled = true;
                totalInput.value = "";
            } else if (totalValue > 0) {
                perPassageInput.disabled = true;
                perPassageInput.value = "";
            } else {
                totalInput.disabled = false;
                perPassageInput.disabled = false;
            }

            // Hesaplanan toplamı göster (sadece kesin modda anlamlı)
            if (perPassageValue > 0 && passageCount > 0 && computedDisplay) {
                const computed = passageCount * perPassageValue;
                computedDisplay.textContent = `Bu bölümden toplam: ${computed} soru`;
            } else if (computedDisplay) {
                computedDisplay.textContent = "";
            }
        }

        perPassageInput.addEventListener("input", updateSection);
        totalInput.addEventListener("input", updateSection);
        passageCountInput.addEventListener("input", updateSection);

        updateSection(); // sayfa yüklenirken başlangıç durumu
    }

    setupPassageSection("reading");
    setupPassageSection("listening");

});