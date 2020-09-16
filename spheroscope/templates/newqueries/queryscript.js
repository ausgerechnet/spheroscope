var runTest = document.querySelectorAll("#run-test");


for(var i=0; i < runTest.length; i++){

    runTest[i].addEventListener("click", function(){
        console.log("yes");
        $("#show-query-results").load("{{ url_for('newqueries.run_cmd', cwb_id=cwb_id, id=query['id']) }}");
    });

}
