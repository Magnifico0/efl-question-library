document.addEventListener("DOMContentLoaded", function () {
  var kindSelect = document.getElementById("id_kind");
  var readingField = document.getElementById("reading-field");
  var listeningFields = document.getElementById("listening-fields");

  function toggleFields() {
    var value = kindSelect.value; // "reading" veya "listening"
    readingField.style.display = value === "reading" ? "block" : "none";
    listeningFields.style.display = value === "listening" ? "block" : "none";
  }

  kindSelect.addEventListener("change", toggleFields);
  toggleFields(); // sayfa yüklenirken doğru başlangıç durumu
});