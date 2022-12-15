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

function textarea_sans() {
    var textarea = document.getElementById("big_text");
    textarea.className = "txt_sans";
}

function textarea_mono() {
    var textarea = document.getElementById("big_text");
    textarea.className = "txt_mono";
}

function textarea_serif() {
    var textarea = document.getElementById("big_text");
    textarea.className = "txt_serif";
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


function image_edit_frame_show() {
    var fr = document.getElementById("ul_image_div");
    fr.style.display = "";
}

function image_edit_frame_hide() {
    var fr = document.getElementById("ul_image_div");
    fr.style.display = "none";
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
        var d = document.getElementById('big_text');
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
        document.getElementById('big_text').focus();
    }
}

function page_load(context)
{
    if (context == 'list')
    {
        display_compact();
    }

    if (context == "edit")
    {
        document.getElementById('big_text').addEventListener('keydown', text_area_listener);
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

function compare(v1, v2, recordkeeper)
{
    if (recordkeeper == 'count_order')
    {
        i1 = parseInt(v1);
        i2 = parseInt(v2);
        //alert("v1 = " + v1 + "   v2 = " + v2)
        if (i1 > i2) { return 1; }
        if (i1 < i2) { return -1; }
        return 0;
    }
    else
    {
        return v1.localeCompare(v2);
    }
}


function table_sort(table_id, tbody_id, recordkeeper)
{
    var table = $('#' + table_id);
    var tbody = $('#' + tbody_id);

    sort_order_element = table_id + '_' + recordkeeper;
    sort_order = document.getElementById(sort_order_element).value;
    var idx = 'first';
    if (recordkeeper == 'count_order') {
        idx = 'last';
    }

    tbody.find('tr').sort(
        function(a, b)
        {
            var at = $('td:'+idx, a).text();
            var bt = $('td:'+idx, b).text();

            if (sort_order == 'asc')
            {
                return compare(at, bt, recordkeeper);
            }
            else
            {
                return compare(bt, at, recordkeeper);
            }
        }
    ).appendTo(tbody);

    if(sort_order == "asc") {
        document.getElementById(table_id + '_' + recordkeeper).value = "desc";
    } else {
        document.getElementById(table_id + '_' + recordkeeper).value = "asc";
    }
}

function submit_list_form()
{
    frm = document.getElementById('list_form');
    frm.submit();
}

// by default a new search should sort by decreasing relevance
function new_search() {
    srch = document.getElementById('input_search').value;
    if (srch.length > 0) {
        var v = document.getElementById('input_sk');
        v.value = 'relevance';
        var w = document.getElementById('input_so');
        w.value = 'desc';
    }
    submit_list_form();
}

function go_to_page(pg_num)
{
    var v = document.getElementById('input_pg');
    v.value = pg_num;
    submit_list_form();
}