function expand_delete() {
    d = document.getElementById("delete_form");
    d.style.display = "inline";
}

function expand_messages() {
    var messages = document.querySelectorAll(".msg_body");
    for (var i = 0; i < messages.length; i++) {
        messages[i].style.display = "inline";
    }
}

function collapse_messages() {
    var messages = document.querySelectorAll(".msg_body");
    for (var i = 0; i < messages.length; i++) {
        messages[i].style.display = "none";
    }
}

// adapted from: https://stackoverflow.com/questions/6637341/use-tab-to-indent-in-textarea
function text_area_listener(e)
{
    if (e.key == 'Tab')
    {
        e.preventDefault();
        var start = this.selectionStart;
        var end = this.selectionEnd;

        // set textarea value to: text before caret + tab + text after caret
        this.value = this.value.substring(0, start) + "    " + this.value.substring(end);

        // put caret at right position again
        this.selectionStart = this.selectionEnd = start + 4;
    }

    if (e.key == 'Backspace')
    {
        var start = this.selectionStart;
        var end = this.selectionEnd;

        if (this.value.substring(start - 4, start) == "    ")
        {
            e.preventDefault();
            this.value = this.value.substring(0, start - 4) + this.value.substring(end);
            this.selectionStart = this.selectionEnd = start - 4;
        }
    }

    if (e.key == '@')
    {
        e.preventDefault();
        show_people_autocomplete();
    }
}

function people_autocomplete_listener(e)
{
    if (e.key == 'Enter')
    {
        // insert the name into the textarea
        var d = document.getElementById('text');
        var start = d.selectionStart;
        var end = d.selectionEnd;

        var v = document.getElementById("people_autocomplete_text_field").value;
        d.value = d.value.substring(0, start) + v + " " + d.value.substring(end);
        d.selectionStart = d.selectionEnd = start + v.length + 1;
    }

    if (e.key == 'Escape' || e.key == 'Enter')
    {
        // hide and go back
        document.getElementById("people_autocomplete_div").style.display = "none";
        document.getElementById('text').focus();
    }
}

function page_load(context)
{
    if (context == "edit")
    {
        document.getElementById('text').addEventListener('keydown', text_area_listener);
        document.getElementById('people_autocomplete_text_field').addEventListener('keyup',
            people_autocomplete_listener);
    }
}

$( function() {
    var availablePeople = ["PEOPLE_LIST_GOES_HERE"];

    $( "#people_autocomplete_text_field" ).autocomplete(
        {
            source: availablePeople
        }
    );
}
);

function show_people_autocomplete()
{
    var d = document.getElementById("people_autocomplete_text_field");
    d.value = "@";
    l = d.value.length;
    d.setSelectionRange(l, l);

    document.getElementById("people_autocomplete_div").style.display = "inline";
    d.focus();
}
