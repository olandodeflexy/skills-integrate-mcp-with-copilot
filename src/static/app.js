async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.detail || payload.message || "Request failed");
  }

  return payload;
}

document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const fullNameInput = document.getElementById("full-name");
  const messageDiv = document.getElementById("message");
  const defaultSelectMarkup =
    '<option value="">-- Select an activity --</option>';
  let messageTimeoutId;

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    globalThis.clearTimeout(messageTimeoutId);
    messageTimeoutId = globalThis.setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  async function fetchActivities() {
    try {
      const activitiesResponse = await fetchJson("/api/activities");
      const activities = activitiesResponse.activities;
      const registrationResponses = await Promise.all(
        activities.map((activity) =>
          fetchJson(`/api/activities/${activity.id}/registrations`)
        )
      );

      activitiesList.innerHTML = "";
      activitySelect.innerHTML = defaultSelectMarkup;

      activities.forEach((activity, index) => {
        const registrations = registrationResponses[index].registrations.filter(
          (registration) => registration.status === "registered"
        );
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        const participantsHTML =
          registrations.length > 0
            ? `<div class="participants-section">
              <h5>Registered Students</h5>
              <ul class="participants-list">
                ${registrations
                  .map(
                    (registration) =>
                      `<li>
                        <div class="participant-copy">
                          <span class="participant-name">${registration.student.full_name}</span>
                          <span class="participant-email">${registration.student.email}</span>
                        </div>
                        <button class="delete-btn" data-activity-id="${activity.id}" data-registration-id="${registration.id}">Remove</button>
                      </li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No registered students yet</em></p>`;

        const availabilityText =
          activity.available_spots > 0
            ? `${activity.available_spots} spots left`
            : "Full";
        const waitlistMarkup =
          activity.waitlisted_count > 0
            ? `<p><strong>Waitlist:</strong> ${activity.waitlisted_count} students</p>`
            : "";
        const locationMarkup = activity.location
          ? `<p><strong>Location:</strong> ${activity.location}</p>`
          : "";

        activityCard.innerHTML = `
          <div class="activity-heading">
            <h4>${activity.name}</h4>
            <span class="activity-category">${activity.category}</span>
          </div>
          <p>${activity.description}</p>
          <p><strong>Schedule:</strong> ${activity.schedule_text}</p>
          ${locationMarkup}
          <p><strong>Availability:</strong> ${availabilityText}</p>
          <p><strong>Registered:</strong> ${activity.registered_count} / ${activity.max_participants}</p>
          ${waitlistMarkup}
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = String(activity.id);
        option.textContent = `${activity.name} (${availabilityText})`;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      activitySelect.innerHTML = defaultSelectMarkup;
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(event) {
    const button = event.target;
    const { activityId, registrationId } = button.dataset;

    try {
      const result = await fetchJson(
        `/api/activities/${encodeURIComponent(
          activityId
        )}/registrations/${encodeURIComponent(registrationId)}`,
        { method: "DELETE" }
      );
      showMessage(result.message, "success");
      fetchActivities();
    } catch (error) {
      showMessage(error.message || "Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const fullName = fullNameInput.value.trim();
    const activityId = document.getElementById("activity").value;

    try {
      const result = await fetchJson(
        `/api/activities/${encodeURIComponent(activityId)}/registrations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            full_name: fullName || null,
          }),
        }
      );
      showMessage(result.message, "success");
      signupForm.reset();
      fetchActivities();
    } catch (error) {
      showMessage(error.message || "Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  fetchActivities();
});
