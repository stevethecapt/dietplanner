document.addEventListener("DOMContentLoaded", () => {
  const userBtn = document.getElementById("userBtn");
  const userPopup = document.getElementById("userPopup");

  if (!userBtn) return;

  userBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    // Ambil data
    const response = await fetch("/user_info");
    const data = await response.json();

    // Isi popup
    document.getElementById("popupFullname").innerText = data.fullname;
    document.getElementById("popupEmail").innerText = data.email;
    document.getElementById("popupJoined").innerText = data.created_at;

    // Toggle popup
    userPopup.classList.toggle("hidden");
  });

  // Klik di luar popup = tutup
  document.addEventListener("click", (e) => {
    if (!userPopup.contains(e.target) && e.target !== userBtn) {
      userPopup.classList.add("hidden");
    }
  });
});
