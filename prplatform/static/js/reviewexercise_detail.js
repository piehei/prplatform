
(function () {
  window.addEventListener('load', function() {
    var submit_button = document.getElementById('review-submit');

    // if no submission can be made, don't do anything at all
    if (submit_button.hasAttribute('disabled')) {
      return;
    }

    submit_button.addEventListener('click', handleClick);

    var form = document.getElementById('review-form');
    var submit_real = document.getElementById('review-submit-real-controls');

    function handleClick(evt) {

      // if required fields have not been filled
      for (var i=0; i < form.elements.length; i += 1){
        if (form.elements[i].value === '' && form.elements[i].hasAttribute('required')) {
          // don't continue
          return;
        }
      }

      // this will show a real submit button with a confirmation text
      submit_real.style.display = '';
    }

  })
}())
