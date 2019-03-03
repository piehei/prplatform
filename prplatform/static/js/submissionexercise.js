
// THIS IS A TOTAL HACK
// will be replaced with Vue.JS <3
//
//
//

window.onload = function() {

  var typeChanger = document.getElementById('id_type');

  var aplus_course_id = document.getElementById('div_id_aplus_course_id');
  var aplus_exercise_id = document.getElementById('div_id_aplus_exercise_id');
  var accepted_filetypes = document.getElementById('div_id_accepted_filetypes');

  function hide(items) {
    if (items.constructor !== Array) {
      items = [items];
    }
    items.forEach(function(item) {
      item.style.display = "none";
    })
  }

  function show(items) {
    if (items.constructor !== Array) {
      items = [items];
    }
    items.forEach(function(item) {
      item.style.display = "block";
    })
  }

  function toggle(type) {
    if (type === 'TEXT') {
      hide([aplus_course_id, aplus_exercise_id, accepted_filetypes]);
    } else if (type === 'FILE_UPLOAD') {
      hide([aplus_course_id, aplus_exercise_id])
      show(accepted_filetypes)
    } else if (type === 'APLUS') {
      show([aplus_course_id, aplus_exercise_id]);
      hide(accepted_filetypes)
    } else if (type === 'GROUP_NO_SUBMISSION') {
      hide([aplus_course_id, aplus_exercise_id, accepted_filetypes])
    } else {
      // this only happens when a new type is added and this JS file
      // is not updated ...
      show([aplus_course_id, aplus_exercise_id, accepted_filetypes]);
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
    var parents = [aplus_course_id, aplus_exercise_id, accepted_filetypes];
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
