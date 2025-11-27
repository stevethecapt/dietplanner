document.addEventListener("DOMContentLoaded", () => {
  const userBtn = document.getElementById("userBtn");
  const userPopup = document.getElementById("userPopup");

  if (!userBtn || !userPopup) return;

  async function fetchInfo() {
    try {
      const res = await fetch("/user_info");
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  function clamp(v, a, b) {
    return Math.max(a, Math.min(b, v));
  }

  async function showPopup() {
    const data = await fetchInfo();
    if (data) {
      const name = data.fullname || data.username || "";
      document.getElementById("popupFullname").innerText = name;
      document.getElementById("popupEmail").innerText = data.email || "";
      document.getElementById("popupJoined").innerText = data.created_at || "";
      // optional fields: bmi, goal_calories, goal_key, progress_percent
      if (data.bmi) document.getElementById("popupBMI").innerText = data.bmi;
      if (data.goal_calories)
        document.getElementById("popupCalories").innerText =
          data.goal_calories + " kcal";
      if (data.goal_key)
        document.getElementById("popupGoal").innerText =
          data.goal_key === "gain"
            ? "Menaikkan"
            : data.goal_key === "maintain"
            ? "Mempertahankan"
            : "Menurunkan";
      if (typeof data.progress_percent !== "undefined") {
        var pct = Math.max(
          0,
          Math.min(100, Number(data.progress_percent) || 0)
        );
        document.getElementById("popupProgressFill").style.width = pct + "%";
        document.getElementById("popupProgressText").innerText = pct + "%";
      }
    }
    // Make popup measurable: show it but keep it invisible so layout can compute
    userPopup.style.visibility = "hidden";
    userPopup.classList.remove("hidden");

    // start polling for updates while popup is open
    if (!userPopup._polling) {
      userPopup._polling = true;
      userPopup._pollInterval = setInterval(async () => {
        try {
          const newData = await fetchInfo();
          if (newData) {
            // update only the dynamic parts to avoid layout jumps
            if (newData.bmi)
              document.getElementById("popupBMI").innerText = newData.bmi;
            if (newData.goal_calories)
              document.getElementById("popupCalories").innerText =
                newData.goal_calories + " kcal";
            if (newData.goal_key)
              document.getElementById("popupGoal").innerText =
                newData.goal_key === "gain"
                  ? "Menaikkan"
                  : newData.goal_key === "maintain"
                  ? "Mempertahankan"
                  : "Menurunkan";
            if (typeof newData.progress_percent !== "undefined") {
              var pct = Math.max(
                0,
                Math.min(100, Number(newData.progress_percent) || 0)
              );
              document.getElementById("popupProgressFill").style.width =
                pct + "%";
              document.getElementById("popupProgressText").innerText =
                pct + "%";
            }
          }
        } catch (e) {
          // ignore polling errors silently
        }
      }, 10000); /* 10s */
    }

    // now measure
    const rect = userBtn.getBoundingClientRect();
    const popupRect = userPopup.getBoundingClientRect();

    // desired top just below button, but clamp within viewport vertically
    const desiredTop = rect.bottom + window.scrollY + 8;
    const maxTop = window.scrollY + window.innerHeight - popupRect.height - 12;
    const top = clamp(
      desiredTop,
      window.scrollY + 8,
      Math.max(window.scrollY + 8, maxTop)
    );

    // center horizontally near the button if possible, clamp within viewport horizontally
    const popupWidth = popupRect.width;
    const desiredLeft =
      rect.left + window.scrollX + rect.width / 2 - popupWidth / 2;
    const minLeft = window.scrollX + 8;
    const maxLeft = window.scrollX + window.innerWidth - popupWidth - 8;
    const left = clamp(desiredLeft, minLeft, Math.max(minLeft, maxLeft));

    userPopup.style.top = top + "px";
    userPopup.style.left = left + "px";
    userPopup.style.right = "auto";

    // reveal popup
    userPopup.style.visibility = "visible";
  }

  function hidePopup() {
    userPopup.classList.add("hidden");
    // stop polling when popup hidden
    if (userPopup._polling) {
      clearInterval(userPopup._pollInterval);
      userPopup._polling = false;
      userPopup._pollInterval = null;
    }
  }

  userBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (userPopup.classList.contains("hidden")) showPopup();
    else hidePopup();
  });

  document.addEventListener("click", (e) => {
    if (
      !userPopup.classList.contains("hidden") &&
      !userPopup.contains(e.target) &&
      e.target !== userBtn
    ) {
      hidePopup();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !userPopup.classList.contains("hidden"))
      hidePopup();
  });

  window.addEventListener("resize", () => {
    if (!userPopup.classList.contains("hidden")) showPopup();
  });
});
