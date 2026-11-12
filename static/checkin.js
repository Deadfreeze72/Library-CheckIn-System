// Check-in pop-up: Student, Staff or Community member.
(function () {
    var dialog = document.getElementById('checkin-dialog');
    if (!dialog) { return; }

    var openButton = document.getElementById('open-checkin');
    var cancelButton = document.getElementById('cancel-checkin');
    var studentFields = document.getElementById('student-fields');
    var visitorFields = document.getElementById('visitor-fields');
    var radios = dialog.querySelectorAll('input[name="visitor_type"]');

    function selectedType() {
        for (var i = 0; i < radios.length; i++) {
            if (radios[i].checked) { return radios[i].value; }
        }
        return 'Student';
    }

    // Only the fields for the chosen type are shown, required and sent.
    function setGroup(group, active) {
        group.hidden = !active;
        var inputs = group.querySelectorAll('input');
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].disabled = !active;
            inputs[i].required = active;
        }
    }

    function update() {
        var isStudent = selectedType() === 'Student';
        setGroup(studentFields, isStudent);
        setGroup(visitorFields, !isStudent);
    }

    function openDialog() {
        if (typeof dialog.showModal === 'function') {
            dialog.showModal();
        } else {
            dialog.setAttribute('open', '');
        }
        var firstField = dialog.querySelector('[id$="-fields"]:not([hidden]) input');
        if (firstField) { firstField.focus(); }
    }

    function closeDialog() {
        if (typeof dialog.close === 'function') {
            dialog.close();
        } else {
            dialog.removeAttribute('open');
        }
    }

    for (var i = 0; i < radios.length; i++) {
        radios[i].addEventListener('change', update);
    }
    openButton.addEventListener('click', openDialog);
    cancelButton.addEventListener('click', closeDialog);

    update();
    if (dialog.getAttribute('data-open') === 'true') { openDialog(); }
})();
