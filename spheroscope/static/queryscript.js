var runTest = document.querySelectorAll(".run-test");
var editQuery = document.querySelectorAll(".edit-test");
var newQuery = document.querySelectorAll("#new-test");
var tableResult = document.getElementById("#query-results");

$(document).ready(function(){

   $(runTest).click(function(){
       $('#show-query-results').load($(this).attr('href'));
       return false;
   });

});



$(document).ready(function(){

   $(editQuery).click(function(){
       $('#editing-window').load($(this).attr('href'));
       return false;
   });
});

$(document).ready(function(){

   $(newQuery).click(function(){
       $('#editing-window').load($(this).attr('href'));
       return false;
   });

});




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