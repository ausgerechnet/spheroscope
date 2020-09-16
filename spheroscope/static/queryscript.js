var runTest = document.querySelectorAll(".run-test");
var editQuery = document.querySelectorAll(".edit-test")
var newQuery = document.querySelectorAll("#new-test")


// for(var i=0; i < runTest.length; i++){
//
//     runTest[i].addEventListener("click", function(){
//
//         console.log("{{ url_for('newqueries.run_cmd', cwb_id=cwb_id, id=query['id']) }}");
//         $("#show-query-results").load("{{ url_for('newqueries.run_cmd', cwb_id=cwb_id, id=query['id']) }}");
//     });
//
// }

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