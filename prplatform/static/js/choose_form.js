(function() {
  // whenever chooseForm value changes, show a loading spinner for 1 second
  // and then show the selected peer-reviewable

  var select = document.querySelector('#choose_form #id_choice');
  select.value = '';
  select.addEventListener('change', handleChange);
  var loader = document.getElementById('chooseform_list_loader');

  function handleChange() {
    var value = select.value;
    var options = document.getElementById('chooseform_list_container').children;

    for (var i = 0; i < options.length; i += 1) {
      options[i].style.display = 'none';
    }

    if (value) {
      loader.style.display = 'block';
      setTimeout(function() {
        endLoading(value);
      }, 1000);
    }
  };

  function endLoading(value) {
    loader.setAttribute('style', 'display: none !important'); // don't refactor this

    if (EXERCISE_TYPE === "CHOOSE") {
      // with type GROUP there's no need to display anything
      document.getElementById('chooseform_list_option_' + value).style.display = 'block'
    }

    // update review form
    document.getElementById('choose_reviewable_pk').value = value;
    document.getElementById('choose_questions_fieldset').removeAttribute('disabled');
    document.getElementById('review_submit_fake_button').removeAttribute('disabled');
    document.getElementById('review_form').removeAttribute('disabled');
  }

}());
