document.addEventListener("DOMContentLoaded", function () {
    const totalInput = document.getElementById("id_total");
    const levelInputs = document.querySelectorAll(".level-input");
    const remainingDisplay = document.getElementById("remaining-display");
    const submitBtn = document.getElementById("submit-btn");
    const independentEl = document.getElementById("independent-count");
    const passageWarnings = document.getElementById("passage-level-warnings");

    /* ------------------------------------------------------------------ */
    /* TEK KARAR NOKTASI                                                   */
    /*                                                                      */
    /* İki bağımsız kontrolümüz var: (1) level toplamı == total mi,        */
    /* (2) passage'ların istediği level bazlı miktar, o level'a ayrılan     */
    /* kotayı aşıyor mu. İkisi de submit butonunu etkilemeli. Eğer ikisi de */
    /* kendi başına submitBtn.disabled'ı yazsaydı, biri diğerinin kararını  */
    /* ezebilirdi (services.py'de gördüğümüz "iki ayrı yerin aynı sonucu    */
    /* bağımsız hesaplaması" hatasının JS karşılığı). Bunun yerine her      */
    /* kontrol sonucunu `validity` nesnesine yazar, tek `applySubmitState`  */
    /* ikisine birden bakıp son kararı verir.                               */
    /* ------------------------------------------------------------------ */
    const validity = { totalOk: false, passageOk: true };

    function applySubmitState() {
        if (submitBtn) submitBtn.disabled = !(validity.totalOk && validity.passageOk);
    }

    /* ---- Kontrol 1: level toplamı == total ---- */
    function updateRemaining() {
        if (!totalInput || !remainingDisplay) return;
        const total = parseInt(totalInput.value) || 0;
        let sum = 0;
        levelInputs.forEach(function (input) {
            sum += parseInt(input.value) || 0;
        });
        const remaining = total - sum;

        if (remaining === 0 && total > 0) {
            remainingDisplay.textContent = "Tamam, toplam eşleşti.";
            remainingDisplay.className = "ok";
            validity.totalOk = true;
        } else if (remaining < 0) {
            remainingDisplay.textContent = `Toplamı ${Math.abs(remaining)} soru aştınız.`;
            remainingDisplay.className = "error";
            validity.totalOk = false;
        } else {
            remainingDisplay.textContent = `Kalan: ${remaining} soru`;
            remainingDisplay.className = "error";
            validity.totalOk = false;
        }
        applySubmitState();
    }

    /* ---- Dropdown seçenekleri: aktif level'lardan türetilir ---- */
    function activeLevels() {
        const levels = [];
        levelInputs.forEach(function (input) {
            const level = input.dataset.level;
            const count = parseInt(input.value, 10) || 0;
            if (level && count > 0) levels.push(level);
        });
        return levels;
    }

    function optionsHtml(levels, selectedValue) {
        let html = '<option value="">Seviye seçin</option>';
        levels.forEach(function (l) {
            const selected = (l === selectedValue) ? " selected" : "";
            html += '<option value="' + l + '"' + selected + '>' + l + '</option>';
        });
        return html;
    }

    function refreshSlotLevelOptions() {
        const levels = activeLevels();
        document.querySelectorAll(".passage-slot-level").forEach(function (select) {
            const current = select.value;
            select.innerHTML = optionsHtml(levels, current);
            if (current && !levels.includes(current)) {
                select.value = "";
            }
        });
    }

    /* ---- Bağımsız soru sayısı (toplam - tüm passage slotları) ---- */
    function recalcIndependent() {
        if (!totalInput || !independentEl) return;
        const total = parseInt(totalInput.value, 10) || 0;
        let passageTotal = 0;
        document.querySelectorAll(".passage-slot-count").forEach(function (input) {
            passageTotal += parseInt(input.value, 10) || 0;
        });
        const independent = total - passageTotal;
        independentEl.textContent = independent;
        independentEl.classList.toggle("text-danger", independent < 0);
    }

    /* ---- Kontrol 2: her level için passage talebi, o level'ın kotasını aşıyor mu ---- */
    function levelQuotas() {
        const quotas = {};
        levelInputs.forEach(function (input) {
            const level = input.dataset.level;
            if (level) quotas[level] = parseInt(input.value, 10) || 0;
        });
        return quotas;
    }

    function passageDemandByLevel() {
        const demand = {};
        document.querySelectorAll(".slot-row").forEach(function (row) {
            const levelSelect = row.querySelector(".passage-slot-level");
            const countInput = row.querySelector(".passage-slot-count");
            if (!levelSelect || !countInput) return;
            const level = levelSelect.value;
            const count = parseInt(countInput.value, 10) || 0;
            if (!level || count <= 0) return;
            demand[level] = (demand[level] || 0) + count;
        });
        return demand;
    }

    function checkPassageQuota() {
        const demand = passageDemandByLevel();
        const quotas = levelQuotas();
        const violations = [];

        Object.keys(demand).forEach(function (level) {
            const needed = demand[level];
            const quota = quotas[level] || 0;
            if (needed > quota) {
                violations.push(
                    `${level}: parçalar toplam ${needed} soru istiyor, ama bu seviyeye ` +
                    `ayrılan kota ${quota}.`
                );
            }
        });

        if (passageWarnings) {
            if (violations.length > 0) {
                passageWarnings.style.display = "block";
                passageWarnings.innerHTML = violations.map(function (v) {
                    return `<div>${v}</div>`;
                }).join("");
            } else {
                passageWarnings.style.display = "none";
                passageWarnings.innerHTML = "";
            }
        }

        validity.passageOk = violations.length === 0;
        applySubmitState();
    }

    /* ---- Satır şablonu (yeni parça eklerken) ---- */
    function rowTemplate(prefix, index) {
        const levels = activeLevels();
        return `
      <div class="row g-2 align-items-end mb-2 slot-row">
        <div class="col-5">
          <label class="form-label">Seviye</label>
          <select name="${prefix}-${index}-level" id="id_${prefix}-${index}-level"
                  class="form-select passage-slot-level">${optionsHtml(levels, "")}</select>
        </div>
        <div class="col-5">
          <label class="form-label">Soru Sayısı</label>
          <input type="number" min="1" name="${prefix}-${index}-question_count"
                 id="id_${prefix}-${index}-question_count" class="form-control passage-slot-count">
        </div>
        <div class="col-2">
          <button type="button" class="btn btn-outline-danger btn-sm remove-slot">Sil</button>
        </div>
      </div>`;
    }

    function totalFormsInput(prefix) {
        return document.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
    }

    function reindex(container, prefix) {
        const rows = container.querySelectorAll(".slot-row");
        rows.forEach(function (row, i) {
            const pattern = new RegExp("^" + prefix + "-\\d+-");
            const replacement = prefix + "-" + i + "-";

            row.querySelectorAll("select, input").forEach(function (field) {
                if (field.name) field.name = field.name.replace(pattern, replacement);
                if (field.id) {
                    field.id = field.id.replace(
                        new RegExp("^id_" + prefix + "-\\d+-"), "id_" + replacement
                    );
                }
            });

            row.querySelectorAll("label[for]").forEach(function (label) {
                const forAttr = label.getAttribute("for");
                if (!forAttr) return;
                label.setAttribute("for", forAttr.replace(
                    new RegExp("^id_" + prefix + "-\\d+-"), "id_" + replacement
                ));
            });
        });
        totalFormsInput(prefix).value = rows.length;
    }

    /* ---- Olay bağlama ---- */

    if (totalInput) totalInput.addEventListener("input", function () {
        updateRemaining();
        recalcIndependent();
    });

    levelInputs.forEach(function (input) {
        input.addEventListener("input", function () {
            updateRemaining();
            refreshSlotLevelOptions();
            checkPassageQuota();
        });
    });

    document.querySelectorAll(".add-slot").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const container = document.getElementById(btn.dataset.target);
            const prefix = container.dataset.prefix;
            const totalFormsEl = totalFormsInput(prefix);
            const index = parseInt(totalFormsEl.value, 10);

            container.insertAdjacentHTML("beforeend", rowTemplate(prefix, index));
            totalFormsEl.value = index + 1;
            recalcIndependent();
            checkPassageQuota();
        });
    });

    document.addEventListener("click", function (e) {
        if (!e.target.classList.contains("remove-slot")) return;
        const row = e.target.closest(".slot-row");
        const container = row.parentElement;
        const prefix = container.dataset.prefix;
        row.remove();
        reindex(container, prefix);
        recalcIndependent();
        checkPassageQuota();
    });

    // Passage satırlarındaki seviye (select) ya da soru sayısı (input)
    // değiştiğinde: hem "change" (select için) hem "input" (number için)
    // dinlemek gerekiyor -- select elemanları her tarayıcıda "input"
    // olayını güvenilir şekilde tetiklemeyebilir.
    function handlePassageFieldChange(e) {
        if (e.target.classList.contains("passage-slot-count") ||
            e.target.classList.contains("passage-slot-level")) {
            recalcIndependent();
            checkPassageQuota();
        }
    }
    document.addEventListener("input", handlePassageFieldChange);
    document.addEventListener("change", handlePassageFieldChange);

    /* ---- İlk yükleme: sayfa GET ile açıldığında ya da hata sonrası
       formset dolu geldiğinde, mevcut duruma göre senkronla ---- */
    updateRemaining();
    recalcIndependent();
    refreshSlotLevelOptions();
    checkPassageQuota();
});