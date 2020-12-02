var runTest = document.querySelectorAll(".run-test");
var editQuery = document.querySelectorAll(".edit-test");
var newQuery = document.querySelectorAll("#new-test");
//var showMetaCurrent = document.querySelectorAll('.show-meta')
// var tableResult = document.getElementById("#query-results");

// displaying

function pageEvents(){
    $(document).ready(function(){

       $(runTest).click(function(){
           $('#show-query-results').load($(this).attr('href'), useTableMeta);
           return false;
       });

    });

    $(document).ready(function(){

       $(editQuery).click(function(){
           $('#more-window').load($(this).attr('href'));
           return false;
       });
    });

    $(document).ready(function(){

       $(newQuery).click(function(){
           $('#more-window').load($(this).attr('href'));
           return false;
       });

    });
};
// hier wird alles NACH dem Laden der HTML Datei ausgeführt


window.onload = function(){
    pageEvents();
};



/*

$(document).ready(function(){

   $(editQuery).click(function(){
       $('#more-window').load($(this).attr('href'));
       return false;
   });
});
*/



/*








function tableSelector(){

    for (var i = 0; i < showMetaCurrent.length; i++){
        showMetaCurrent[i].addEventListener("click", function() {
        //showMetaCurrent[i].classList.add("active");
        var tweets = document.getElementById("#query-results")

        for (var j = 0, row; row = tweets.rows[j]; j++){
            // row
            console.log(row);
            for (var k = 0, col; col = row.cells[k]; k++){
                // col
            }
        }

        });
    }
};
*/







// interacting: show metadata table for selected tweet

// there must be an interaction between showtabletest.html and this script
// maybe an interaction between the python script and this script would be better?

/*for (var i = 0; i < showMetaCurrent.length; i++){
    showMetaCurrent[i].addEventListener("click", function() {
        //showMetaCurrent[i].classList.add("active");
        var tweets = document.getElementById("#query-results")

        for (var j = 0, row; row = tweets.rows[j]; j++){
            // row
            console.log(row);
            for (var k = 0, col; col = row.cells[k]; k++){
                // col
    }
}

    });
}

$(document).ready(function(){

   $(showMetaCurrent).click(function(){
       $('#more-window').load($(this).attr('href'));
       return false;
   });

});*/


//

// delegated event handler

/*
$("#table-window").on("change", "div",function(){
   //var tbl = $(this);
   console.log("yes");
});*/


/*
for (var i = 0, row; row = tableResult.rows[i]; i++){
    // row
    console.log(row);
    for (var j = 0, col; col = row.cells[j]; j++){
        // col
    }
}

*/