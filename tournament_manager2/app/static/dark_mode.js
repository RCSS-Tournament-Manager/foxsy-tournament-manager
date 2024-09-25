// dark_mode.js

document.addEventListener("DOMContentLoaded", function () {
    // Create Dark Mode Toggle Button
    const darkModeButton = document.createElement("button");
    darkModeButton.innerHTML = "🌙 Dark Mode";
    darkModeButton.style.position = "fixed";
    darkModeButton.style.top = "10px";
    darkModeButton.style.right = "10px";
    darkModeButton.style.padding = "10px 20px";
    darkModeButton.style.backgroundColor = "#ff5722";
    darkModeButton.style.color = "#ffffff";
    darkModeButton.style.border = "none";
    darkModeButton.style.borderRadius = "5px";
    darkModeButton.style.cursor = "pointer";
    darkModeButton.style.zIndex = "1000";

    document.body.appendChild(darkModeButton);

    // Function to Toggle Dark Mode
    darkModeButton.addEventListener("click", function () {
        const darkMode = document.body.classList.toggle("swagger-dark-mode");
        if (darkMode) {
            // Add Dark Mode CSS
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = "/static/dark_mode.css";
            link.id = "dark-mode-stylesheet";
            document.head.appendChild(link);
            darkModeButton.innerHTML = "☀️ Light Mode";
        } else {
            // Remove Dark Mode CSS
            const darkModeStylesheet = document.getElementById("dark-mode-stylesheet");
            if (darkModeStylesheet) {
                darkModeStylesheet.remove();
            }
            darkModeButton.innerHTML = "🌙 Dark Mode";
        }
    });
});
