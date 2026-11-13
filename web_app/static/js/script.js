// =========================
// TOAST NOTIFICATION
// =========================
    function showToast(message, category = "success") {

    const toast = document.createElement("div");

    toast.className = `toast-message ${category}`;

    toast.innerHTML = `
        <span class="toast-text"></span>
        <button class="toast-close" type="button">&times;</button>
    `;

    // Safely display message as text
    toast.querySelector(".toast-text").textContent = message;

    document.body.appendChild(toast);

    toast.querySelector(".toast-close").addEventListener("click", () => {
        toast.remove();
    });

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// =========================
// EXISTING PROJECT SCRIPTS
// =========================

document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // SIDEBAR MENU
    // =========================

    const menuBtn = document.getElementById("menuBtn");
    const sidebar = document.getElementById("sidebar");

    if (menuBtn && sidebar) {

        menuBtn.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });

    }


    // =========================
    // SALES MANAGEMENT
    // =========================

    const addButton = document.getElementById("add-book");
    const saleItems = document.getElementById("sale-items");

    if (addButton && saleItems) {

        // Add another book row
        addButton.addEventListener("click", function () {

            const firstRow = saleItems.querySelector(".sale-item-row");

            const newRow = firstRow.cloneNode(true);

            // Reset selected book and quantity
            newRow.querySelector("select").value = "";
            newRow.querySelector("input").value = "";

            saleItems.appendChild(newRow);

        });


        // Remove book row
        saleItems.addEventListener("click", function (event) {

            if (event.target.classList.contains("remove-item")) {

                const rows = saleItems.querySelectorAll(".sale-item-row");

                if (rows.length > 1) {

                    event.target.closest(".sale-item-row").remove();

                } else {

                    alert("At least one book is required!");

                }

            }

        });

    }
});
