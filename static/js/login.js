// Şifre alanı için göster/gizle butonu
document.addEventListener("DOMContentLoaded", function () {
    const passwordInput = document.querySelector('input[name="password"]');

    if (passwordInput) {
        const wrapper = document.createElement("div");
        wrapper.style.position = "relative";
        passwordInput.parentNode.insertBefore(wrapper, passwordInput);
        wrapper.appendChild(passwordInput);

        const toggle = document.createElement("span");
        toggle.textContent = "Göster";
        toggle.style.cssText = `
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            font-size: 0.85rem;
            color: #4f46e5;
            user-select: none;
        `;

        wrapper.appendChild(toggle);

        toggle.addEventListener("click", function () {
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                toggle.textContent = "Gizle";
            } else {
                passwordInput.type = "password";
                toggle.textContent = "Göster";
            }
        });
    }
});