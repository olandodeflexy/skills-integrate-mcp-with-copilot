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
  const organizerForm = document.getElementById("organizer-form");
  const organizerList = document.getElementById("organizer-activities-list");
  const organizerMessageDiv = document.getElementById("organizer-message");
  const managedActivityIdInput = document.getElementById("managed-activity-id");
  const managedNameInput = document.getElementById("managed-name");
  const managedDescriptionInput = document.getElementById("managed-description");
  const managedScheduleInput = document.getElementById("managed-schedule");
  const managedLocationInput = document.getElementById("managed-location");
  const managedCategoryInput = document.getElementById("managed-category");
  const managedCapacityInput = document.getElementById("managed-capacity");
  const managedActiveInput = document.getElementById("managed-active");
  const organizerSubmitButton = document.getElementById("organizer-submit");
  const organizerResetButton = document.getElementById("organizer-reset");
  const defaultSelectMarkup =
    '<option value="">-- Select an activity --</option>';
  const messageTimeouts = new Map();
  let organizerActivities = [];

  function showMessage(target, text, type) {
    target.textContent = text;
    target.className = type;
    target.classList.remove("hidden");

    globalThis.clearTimeout(messageTimeouts.get(target));
    const timeoutId = globalThis.setTimeout(() => {
      target.classList.add("hidden");
    }, 5000);
    messageTimeouts.set(target, timeoutId);
  }

  function resetOrganizerForm() {
    organizerForm.reset();
    managedActivityIdInput.value = "";
    managedActiveInput.checked = true;
    organizerSubmitButton.textContent = "Create Activity";
    organizerResetButton.classList.add("hidden");
  }

  function fillOrganizerForm(activity) {
    managedActivityIdInput.value = String(activity.id);
    managedNameInput.value = activity.name;
    managedDescriptionInput.value = activity.description;
    managedScheduleInput.value = activity.schedule_text;
    managedLocationInput.value = activity.location || "";
    managedCategoryInput.value = activity.category;
    managedCapacityInput.value = String(activity.max_participants);
    managedActiveInput.checked = activity.is_active;
    organizerSubmitButton.textContent = "Save Changes";
    organizerResetButton.classList.remove("hidden");
    organizerForm.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function findOrganizerActivity(activityId) {
    return organizerActivities.find(
      (activity) => String(activity.id) === String(activityId)
    );
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

  async function fetchOrganizerActivities() {
    try {
      const activitiesResponse = await fetchJson("/api/management/activities");
      const activities = activitiesResponse.activities;
      organizerActivities = activities;

      if (!activities.length) {
        organizerList.innerHTML = "<p>No activities have been created yet.</p>";
        return;
      }

      organizerList.innerHTML = '<div class="management-card-grid"></div>';
      const cardGrid = organizerList.firstElementChild;

      activities.forEach((activity) => {
        const card = document.createElement("article");
        card.className = activity.is_active
          ? "management-card"
          : "management-card inactive";
        const visibilityLabel = activity.is_active ? "Active" : "Archived";
        const toggleLabel = activity.is_active ? "Archive" : "Restore";
        card.innerHTML = `
          <span class="management-status ${activity.is_active ? "active" : "inactive"}">${visibilityLabel}</span>
          <div class="activity-heading">
            <h4>${activity.name}</h4>
            <span class="activity-category">${activity.category}</span>
          </div>
          <p>${activity.description}</p>
          <div class="management-meta">
            <p><strong>Schedule:</strong> ${activity.schedule_text}</p>
            <p><strong>Location:</strong> ${activity.location || "TBD"}</p>
            <p><strong>Capacity:</strong> ${activity.registered_count} / ${activity.max_participants}</p>
          </div>
          <div class="management-buttons">
            <button type="button" class="secondary-btn edit-activity-btn" data-activity-id="${activity.id}">Edit</button>
            <button type="button" class="secondary-btn toggle-activity-btn" data-activity-id="${activity.id}" data-next-state="${activity.is_active ? "archive" : "restore"}">${toggleLabel}</button>
          </div>
        `;
        cardGrid.appendChild(card);
      });
    } catch (error) {
      organizerList.innerHTML =
        "<p>Failed to load organizer activity management. Please try again later.</p>";
      console.error("Error fetching organizer activities:", error);
    }
  }

  async function refreshAllViews() {
    await Promise.all([fetchActivities(), fetchOrganizerActivities()]);
  }

  async function handleActivityVisibilityToggle(event) {
    const { activityId, nextState } = event.currentTarget.dataset;
    const endpoint = nextState === "archive" ? "archive" : "restore";

    try {
      const result = await fetchJson(
        `/api/management/activities/${encodeURIComponent(activityId)}/${endpoint}`,
        { method: "POST" }
      );
      showMessage(organizerMessageDiv, result.message, "success");
      await refreshAllViews();
    } catch (error) {
      showMessage(
        organizerMessageDiv,
        error.message || "Failed to update activity visibility.",
        "error"
      );
      console.error("Error updating activity visibility:", error);
    }
  }

  async function handleUnregister(event) {
    const button = event.currentTarget;
    const { activityId, registrationId } = button.dataset;

    try {
      const result = await fetchJson(
        `/api/activities/${encodeURIComponent(
          activityId
        )}/registrations/${encodeURIComponent(registrationId)}`,
        { method: "DELETE" }
      );
      showMessage(messageDiv, result.message, "success");
      fetchActivities();
    } catch (error) {
      showMessage(
        messageDiv,
        error.message || "Failed to unregister. Please try again.",
        "error"
      );
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
      showMessage(messageDiv, result.message, "success");
      signupForm.reset();
      fetchActivities();
    } catch (error) {
      showMessage(
        messageDiv,
        error.message || "Failed to sign up. Please try again.",
        "error"
      );
      console.error("Error signing up:", error);
    }
  });

  organizerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activityId = managedActivityIdInput.value;
    const payload = {
      name: managedNameInput.value,
      description: managedDescriptionInput.value,
      schedule_text: managedScheduleInput.value,
      location: managedLocationInput.value,
      category: managedCategoryInput.value,
      max_participants: Number(managedCapacityInput.value),
      is_active: managedActiveInput.checked,
    };
    const isEditing = Boolean(activityId);
    const endpoint = isEditing
      ? `/api/management/activities/${encodeURIComponent(activityId)}`
      : "/api/management/activities";
    const method = isEditing ? "PUT" : "POST";

    try {
      const result = await fetchJson(endpoint, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      showMessage(organizerMessageDiv, result.message, "success");
      resetOrganizerForm();
      await refreshAllViews();
    } catch (error) {
      showMessage(
        organizerMessageDiv,
        error.message || "Failed to save activity changes.",
        "error"
      );
      console.error("Error saving activity:", error);
    }
  });

  organizerResetButton.addEventListener("click", () => {
    resetOrganizerForm();
  });

  organizerList.addEventListener("click", (event) => {
    const clickedElement = event.target;
    if (!(clickedElement instanceof HTMLElement)) {
      return;
    }

    const editButton = clickedElement.closest(".edit-activity-btn");
    if (editButton instanceof HTMLElement) {
      const activity = findOrganizerActivity(editButton.dataset.activityId);
      if (activity) {
        fillOrganizerForm(activity);
      }
      return;
    }

    const toggleButton = clickedElement.closest(".toggle-activity-btn");
    if (toggleButton instanceof HTMLElement) {
      handleActivityVisibilityToggle({ currentTarget: toggleButton });
    }
  });

  resetOrganizerForm();
  refreshAllViews();
});
