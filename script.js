function toggleLanguage() {
  const html = document.documentElement;
  const isEnglish = html.getAttribute("dir") !== "rtl";
  const newLang = isEnglish ? "ar" : "en";

  // Change text direction
  html.setAttribute("dir", isEnglish ? "rtl" : "ltr");

  // Toggle button text
  document.getElementById("langToggle").textContent = isEnglish ? "English" : "عربي";

  // Update all elements with data-en/data-ar
  const translatables = document.querySelectorAll("[data-en][data-ar]");
  translatables.forEach(el => {
    const newText = el.getAttribute(`data-${newLang}`);
    if (el.tagName === "SPAN") {
      el.textContent = newText;
    } else if (el.classList.contains("whatsapp-btn")) {
      const span = el.querySelector("span");
      if (span) span.textContent = newText;
    } else {
      el.textContent = newText;
    }
  });
}
fetch('http://localhost:5000/api/orders', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name, phone, address, services: selectedServices })
});

// ✅ Call this separately — don’t mix with toggleLanguage
function fetchProducts() {
  fetch('https://localhost:5001/api/products') // or http://localhost:5000 depending on backend
    .then(response => response.json())
    .then(data => {
      console.log('Received:', data);
      // TODO: Update UI with product data
    })
    .catch(error => {
      console.error('Error connecting to server:', error);
    });
}
