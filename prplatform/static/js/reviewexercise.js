
// THIS IS A TOTAL HACK
// will be replaced with Vue.JS <3
// *another comment 10 months later: will it?*

window.onload = function() {

  // this will listen on changes of the Type option field
  // and hide expiry hours field if the type changes to something
  // else than RANDOM. RANDOM is the only type that supports
  // expiry hours.

  function handleChange(event) {
    var expiry_hours = document.getElementById('div_id_reviewlock_expiry_hours');
    if (event.target.value === 'RANDOM') {
      expiry_hours.style.display = '';
    } else {
      expiry_hours.style.display = 'none';
    }
  }

  document.getElementById('id_type')
    .addEventListener('change', handleChange);
}
