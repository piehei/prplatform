
// THIS IS A TOTAL HACK
// will be replaced with Vue.JS <3
//
//
//

window.onload = function() {

  var typeChanger = document.getElementById('id_type');

  var aplus_course_id = document.getElementById('div_id_aplus_course_id');
  var aplus_exercise_id = document.getElementById('div_id_aplus_exercise_id');
  var accepted_file_types = document.getElementById('div_id_accepted_file_types');
  var upload_instructions = document.getElementById('div_id_upload_instructions');

  function toggle(type) {
    if (type === 'TEXT') {
      [aplus_course_id, aplus_exercise_id, accepted_file_types, upload_instructions].forEach(function(elem) {
        elem.style.display = "none";
      })
    } else if (type === 'FILE_UPLOAD') {
      [aplus_course_id, aplus_exercise_id].forEach(function(elem) {
        elem.style.display = "none";
      })
      accepted_file_types.style.display = "block";
      upload_instructions.style.display = "block";
    } else if (type === 'APLUS') {
      [aplus_course_id, aplus_exercise_id].forEach(function(elem) {
        elem.style.display = "block";
      })
      accepted_file_types.style.display = "none";
      upload_instructions.style.display = "none";
    }
  }

  // hide incompatible input fields based on the chosen type
  toggle(typeChanger.value);

  // if the user filled in something and then changed the type,
  // invalid form messages will appear after save/update.
  // in that case we should NOT hide the invalid input fields for this
  // particular type IF they have invalid-feedback classes.
  // --> show all invalid-feedback inputs even if not compatible with chosen type
  var invalids = document.querySelectorAll('.invalid-feedback');
  if (invalids) {
    var parents = [aplus_course_id, aplus_exercise_id, accepted_file_types, upload_instructions];
    invalids.forEach(function(invalid) {
      var index = parents.indexOf(invalid.parentElement.parentElement);
      if (index !== -1) {
        parents[index].style.display = "block";
      }
    })
  }

  // hide incompatible input fields when type is changed
  typeChanger.addEventListener('change', function(evt) {
    toggle(this.value);
  })

}
