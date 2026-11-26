
// Load the saved theme when the application opens.
const savedTheme = localStorage.getItem("servicedesk-theme");

if (savedTheme === "dark") {
    document.documentElement.dataset.theme = "dark";
}


// Wait until the page is loaded.
document.addEventListener("DOMContentLoaded", () => {

    const themeButton = document.querySelector(".theme-toggle");

    if (!themeButton) return;

    themeButton.addEventListener("click", () => {

        const isDark =
            document.documentElement.dataset.theme === "dark";

        // Switch between light and dark.
        const newTheme = isDark ? "light" : "dark";

        if (newTheme === "dark") {
            document.documentElement.dataset.theme = "dark";
        } else {
            delete document.documentElement.dataset.theme;
        }

        // Remember the selection.
        localStorage.setItem("servicedesk-theme", newTheme);

    });

});
