document.addEventListener("DOMContentLoaded", function () {
  const payButton = document.getElementById("payButton");
  payButton.addEventListener("click", payWithPaystack, false);
});

function payWithPaystack(e) {
  e.preventDefault();
  let handler = PaystackPop.setup({
    key: "pk_test_de43b037d93eee9a134a3fe2b2d0e4b30c53b2ea", // Replace with your PUBLIC key
    email: document.getElementById("email-address").value,
    amount: document.getElementById("amount").value * 100,
    currency: "GHS",
    ref: "" + Math.floor(Math.random() * 1000000000 + 1),
    callback: function (response) {
      var reference = response.reference;
      console.log("Payment complete! Reference: " + reference);
      verifyPayment(reference);
    },
    onClose: function () {
      console.log("Transaction was not completed, window closed.");
    },
  });
  handler.openIframe();
}

function verifyPayment(reference) {
  const courseId = getCourseId();
  console.log("Verifying payment with reference: " + reference); // Log reference

  fetch(`/course/${courseId}/enroll`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `payment_reference=${reference}`,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        document.getElementById("paymentResponse").innerHTML =
          '<p class="alert alert-success">Enrollment successful! Redirecting...</p>';
        setTimeout(() => {
          window.location.href = data.redirect_url;
        }, 2000);
      } else {
        document.getElementById(
          "paymentResponse"
        ).innerHTML = `<p class="alert alert-danger">${data.message}</p>`;
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      document.getElementById("paymentResponse").innerHTML =
        '<p class="alert alert-danger">An error occurred. Please try again or contact support.</p>';
    });
}

function getCourseId() {
  const pathParts = window.location.pathname.split("/");
  return pathParts[pathParts.indexOf("course") + 1];
}
