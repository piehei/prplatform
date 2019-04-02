(function () {
  // this is shown on page initially -> click reveals confirmation box
  var submit_button_fake = document.getElementById('review-submit');
  // actual button that will submit
  var submit_button_real = document.getElementById('review-submit-real-button');

  // if no submission can be made, don't do anything at all
  if (submit_button_fake.hasAttribute('disabled') && !submit_button_fake.hasAttribute('embedded')) {
    return;
  }

  submit_button_fake.addEventListener('click', handleClick);

  var form = document.getElementById('review-form');
  var submit_confirmation_box = document.getElementById('review-submit-confirmation-container');

  function handleClick() {

    // if required fields have not been filled
    for (var i=0; i < form.elements.length; i += 1){
      if (form.elements[i].value === '' && form.elements[i].hasAttribute('required')) {
        // don't continue
        return;
      }
    }

    // this will show a real submit button with a confirmation text
    submit_confirmation_box.style.display = '';
    submit_button_real.addEventListener('click', disableMultipleSubmits);
  }

  var submit_count = 0;
  function disableMultipleSubmits(evt) {
    if (submit_count > 0) {
      evt.preventDefault();
    }
    submit_count += 1;
    submit_button_real.innerText = 'To submit another peer-review, refresh the page first.';
  }
}());
