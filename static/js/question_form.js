document.addEventListener("DOMContentLoaded", function () {
  var typeSelect = document.getElementById("id_question_type");

  var fibField = document.getElementById("fib-field");
  var openEndedField = document.getElementById("open-ended-field");
  var choicesSection = document.getElementById("choices-section");
  var matchingSection = document.getElementById("matching-section");

  function toggleFields() {
    var value = typeSelect.value; // "mc", "tf", "fib", "matching", "open_ended"

    var isChoiceType = value === "mc" || value === "tf";
    var isMatching = value === "matching";
    var isFib = value === "fib";
    var isOpenEnded = value === "open_ended";

    choicesSection.style.display = isChoiceType ? "block" : "none";
    matchingSection.style.display = isMatching ? "block" : "none";
    fibField.style.display = isFib ? "block" : "none";
    openEndedField.style.display = isOpenEnded ? "block" : "none";
  }

  typeSelect.addEventListener("change", toggleFields);
  toggleFields(); // sayfa yüklenirken (özellikle edit sayfasında) doğru başlangıç durumu
});