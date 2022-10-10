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


function display_helper(a, b) {
    var comp = document.querySelectorAll('.compact');
    for (var i = 0; i < comp.length; i++) {
        comp[i].style.display = a;
    }
    var comf = document.querySelectorAll('.comfortable');
    for (var i = 0; i < comf.length; i++) {
        comf[i].style.display = b;
    }

}


function display_compact()
{
    display_helper("", "none");
}

function display_comfortable()
{
    display_helper("none", "");
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
    if (context == 'list')
    {
        display_comfortable();
    }

    if (context == "edit")
    {
        document.getElementById('text').addEventListener('keydown', text_area_listener);
        document.getElementById('people_autocomplete_text_field').addEventListener('keyup',
            people_autocomplete_listener);
    }
}

$( function() {
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


function table_sort(table_id, tbody_id, recordkeeper)
{
    var table = $('#' + table_id);
    var tbody = $('#' + tbody_id);

    sort_order_element = table_id + '_' + recordkeeper;
    //alert("sort order element = " + sort_order_element);
    sort_order = document.getElementById(sort_order_element).value;

    //alert("sorting " + table_id + "-" + tbody_id + " by " + recordkeeper + " (" + sort_order + ")")

    tbody.find('tr').sort(
        function(a, b)
        {
            //alert("a = " + a + "   " + "b = " + b);
            if(sort_order == 'asc')
            {
                return $('td:first', a).text().localeCompare($('td:first', b).text());
            }
            else
            {
                return $('td:first', b).text().localeCompare($('td:first', a).text());
            }

        }
    ).appendTo(tbody);

    if(sort_order == "asc") {
        document.getElementById(table_id + '_' + recordkeeper).value = "desc";
    } else {
        document.getElementById(table_id + '_' + recordkeeper).value = "asc";
    }
}
