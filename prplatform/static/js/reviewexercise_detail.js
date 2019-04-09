(function () {
  // this is shown on page initially -> click reveals confirmation box
  var submit_button_fake = document.getElementById('review_submit_fake_button');
  // actual button that will submit
  var submit_button_real = document.getElementById('review_submit_real_button');


  submit_button_fake.addEventListener('click', handleClick);

  var form = document.getElementById('review_form');
  var submit_confirmation_box = document.getElementById('review_submit_confirmation_container');

  function handleClick() {
    if (submit_button_fake.hasAttribute('disabled')) {
      return;
    }

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
