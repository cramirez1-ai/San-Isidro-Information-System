document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector("[data-drawer-toggle]")?.getAttribute("aria-controls");
    const drawer = sidebar ? document.getElementById(sidebar) : document.querySelector(".sidebar");
    const toggle = document.querySelector("[data-drawer-toggle]");
    const overlay = document.querySelector("[data-overlay]");

    if (!drawer || !toggle || !overlay) {
        return;
    }

    const setOpen = (isOpen) => {
        drawer.classList.toggle("open", isOpen);
        overlay.classList.toggle("active", isOpen);
        overlay.setAttribute("aria-hidden", String(!isOpen));
        toggle.setAttribute("aria-expanded", String(isOpen));
    };

    toggle.addEventListener("click", () => {
        setOpen(!drawer.classList.contains("open"));
    });

    overlay.addEventListener("click", () => setOpen(false));

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setOpen(false);
        }
    });
});
