function openModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("open");
  }
}

function closeModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("open");
  }
}

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function showToast(message, type) {
  if (type === undefined) {
    type = "success";
  }
  var container = document.getElementById("toast-container");
  var toast = document.createElement("div");
  toast.className = "toast toast-" + type;
  var icon = type === "success" ? "\u2713" : "\u2717";
  toast.innerHTML = '<span class="toast-icon">' + icon + "</span> " + message;
  container.appendChild(toast);

  setTimeout(function () {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(function () {
      toast.remove();
    }, 300);
  }, 4000);
}

function togglePasswordVisibility(inputId, toggleButton) {
  var input = document.getElementById(inputId);
  if (!input) return;
  var isPassword = input.type === "password";
  input.type = isPassword ? "text" : "password";
  var icon = toggleButton.querySelector("i");
  if (icon) {
    icon.className = isPassword ? "bi bi-eye-slash-fill" : "bi bi-eye-fill";
  }
}

function printApplication(applicationId) {
  if (!applicationId) {
    showToast("Unable to print: application id is missing.", "error");
    return;
  }
  openPrintPopup(null, applicationId);
}

function openPrintPopup(element, applicationId) {
  applicationId =
    applicationId ||
    (element && element.dataset ? element.dataset.applicationId : null);
  if (!applicationId) {
    showToast("Unable to print: application id is missing.", "error");
    return;
  }

  var printUrl = "/application/" + applicationId + "/print/";
  var popup = window.open(
    printUrl,
    "printApplication" + applicationId,
    "toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=900,height=700",
  );
  if (!popup) {
    window.location.href = printUrl;
    return;
  }
  popup.focus();
}

function printProfile() {
  window.location.href = "/profile/print/";
}

function copyToClipboard(text, friendlyName) {
  navigator.clipboard
    .writeText(text)
    .then(function () {
      showToast("Copied " + friendlyName + " path to clipboard!", "success");
    })
    .catch(function (err) {
      console.error("Failed to copy path: ", err);
      showToast("Failed to copy path to clipboard.", "error");
    });
}
