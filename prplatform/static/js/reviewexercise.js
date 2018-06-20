
// THIS IS A TOTAL HACK
// will be replaced with Vue.JS <3
//
//
//

window.onload = function() {


  var PREFIX = "#id_form";

  var TOTAL_FORMS = parseInt($(PREFIX + '-TOTAL_FORMS').val());
  console.log("TOTAL_FORMS: ", TOTAL_FORMS);

  var INITIAL_FORMS = parseInt($(PREFIX + '-INITIAL_FORMS').val());
  console.log("INITIAL_FORMS: ", INITIAL_FORMS);

  // these are all the questions in the formset
  // there will be a total of 10 extra empty questions that might be taken into use
  var multiFields = Array.prototype.slice.call(document.querySelectorAll('.multiField'));

  // iterate over the fields and hide all *unused* fields from the view
  multiFields.forEach(function(elem, index) {
    console.log(elem, index)
    if (index >= INITIAL_FORMS) {
      elem.style.display = "none";
    }
  })

  // if no questions has been added, show the first empty question
  if (INITIAL_FORMS === 0) {
    multiFields[0].style.display = "";
    document.querySelector(PREFIX + '-0-ORDER').value = 1;
  }

  $('#add-new-question').on('click', function() {
    console.log('add-new-question clicked');

    // when the add new question button is clicked
    // find the first *unused* hidden question field and show it
    for (var i = 0; i < multiFields.length; i += 1) {
      if (multiFields[i].style.display === "none") {
        multiFields[i].style.display = "";
        document.querySelector(PREFIX + '-' + i + '-ORDER').value = i + 1;
        break;
      }
    }

  })

  // when the form submit button is pressed
  // go through all added questions and make sure their ORDER value is ""
  // if text value is ""
  // --> if this is not done backend thinks that a new question with order but WITHOUT text
  //     was tried to be added
  $('#create-review-exercise').on('click', function() {
    for (var i = 0; i < multiFields.length; i += 1) {
        var textInputField = document.querySelector(PREFIX + '-' + i + '-text');
        if (textInputField.value === "") {
          document.querySelector(PREFIX + '-' + i + '-ORDER').value = "";
        }
    }
  })
}
