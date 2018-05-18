
// THIS IS A TOTAL HACK
// will be replaced with Vue.JS <3
//
//
//

window.onload = function() {

  var TOTAL_FORMS = parseInt($('#id_questions-TOTAL_FORMS').val());
  //console.log(TOTAL_FORMS);

  var INITIAL_FORMS = parseInt($('#id_questions-INITIAL_FORMS').val());
  //console.log(INITIAL_FORMS);

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


  $('#add-new-question').on('click', function() {
    console.log('add-new-question clicked');

    // when the add new question button is clicked
    // find the first *unused* hidden question field and show it
    for (var i = 0; i < multiFields.length; i += 1) {
      if (multiFields[i].style.display === "none") {
        multiFields[i].style.display = "";
        break;
      }
    }

  })

}
