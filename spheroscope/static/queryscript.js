const table = document.querySelector("#query-results");

// data from backend
const tooltipString = document.querySelector("#extra-information");
const tooltipTables = JSON.parse(tooltipString.innerText);
const metaDataString = document.querySelector("#meta-data");
const metaDataTables = JSON.parse(metaDataString.innerText);
// these tables are only a single row

const freqTables = document.querySelectorAll(".freq-table")

const listFreqTableWrapper = document.querySelector("#freq-table-wrapper");

// pagination
// function called before page finishes loading
$(function(){

    const pages = freqTables.length;

    for (let page = 1; page <= pages; page++) {
        listFreqTableWrapper.innerHTML += `<div class="freq-table-page">Frequency Table (Anchors ${page-1}-${page})</div>`;
    }

    const freqTablePages = document.querySelectorAll(".freq-table-page");
    for (let i = 0; i < freqTablePages.length; i++){
        freqTablePages[i].appendChild(freqTables[i]);
    }

    for (let page of freqTablePages){

        page.addEventListener("click", function() {

            if(page.firstElementChild.style.display === "block"){
               page.firstElementChild.style.display = "none";
            }else{
               page.firstElementChild.style.display = "block";
            }

        })

    }

});

// rename columns of frequency tables

const fTcols = document.querySelectorAll(".freq-table thead tr th");
for(let i = 0; i<fTcols.length; i++){
	if(i%2===0){
		fTcols[i].innerText = "match region";
	}else{
		fTcols[i].innerText = "frequency in corpus";
	}
}

for(let row in metaDataTables){

    // find div with this class
    // (should to be id, but since I made two versions of the same visualization
    // I'm going to use a class)
    let contentDiv = document.getElementsByClassName(`${row}`);

    // place table inside div
    for(let content of contentDiv){
        content.innerHTML = metaDataTables[row];
    }

}

// show meta data pop up window version:

const openPuwButtons = document.querySelectorAll("[data-puw-target]");
const closePuwButtons = document.querySelectorAll("[data-close-button]");
const overlay = document.querySelector("#overlay");

openPuwButtons.forEach(button => {
    button.addEventListener("click", () => {
        const puw = document.querySelector(button.dataset.puwTarget);
        openPuW(puw);
    })
});

closePuwButtons.forEach(button => {
    button.addEventListener("click", () => {
        const puw = button.closest(".pop-up-window")
        closePuW(puw);
    })
});

const openPuW = (puw) => {
    if(puw == null){
        return
    }else{
        puw.classList.add("active");
        overlay.classList.add("active");
    }
}
const closePuW = (puw) => {
    if(puw == null){
        return
    }else{
        puw.classList.remove("active");
        overlay.classList.remove("active");
    }
}

// show meta data collapsible version:
// match row with meta data table
// e.g. metaDataTables["(372795, 372805)"]

let collapsible = document.getElementsByClassName("collapsible");

for (let i = 0; i < collapsible.length; i++) {
  collapsible[i].addEventListener("click", function() {
    this.classList.toggle("coll-active");
    let content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}

// bootstrap collapsible: <button class ="btn btn-primary" type="button" data-toggle="collapse" data-target="#collapseExample" aria-expanded="false" aria-controls="collapseExample">


// show meta data pop-up version:

// div with class "overlay" needs to be placed after puw-window div



// div with class tooltip around all metadata tables (hide tooltip)
// div with class tooltip area around all tweets
/*
let tooltipId = 1;
for(let tbl in tooltipTables){
    let tooltip = document.createElement("div")
    tooltip.classList.add("tooltip");
    tooltip.id = tooltipId;
    tooltip.innerHTML = tooltipTables[tbl];
    //tooltip.style.display = "none";
    document.body.appendChild(tooltip);
    tooltipId += 1;
}*/

//document.querySelectorAll(".md-tbl").style.display = "none";
/*
let tweetId = 0;

try{

    for(let row in queryText){

      let tooltipContainer = document.createElement("div");

      tooltipContainer.classList.add("tooltip-area");

      // put text inside div for every row
      let innerHtml = queryText[row].innerHTML;

      queryText[row].innerHTML = "";
      queryText[row].appendChild(tooltipContainer);

      tooltipContainer.innerHTML = innerHtml;
      tooltipContainer.id = tweetId;

      tweetId += 1;

    }

}catch{

}
*/
// show tooltip with extra information for every row
// implementing tooltip
/*
const tooltip = document.querySelectorAll(".tooltip");

//tooltipArea[0].id, $(".tooltip-area#1")
// display tooltip on hover for every tweet

$(function() {

    // mouse hover
    for(let i = 0; i<=tweetId; i++){
        //console.log($(`.tooltip-area#${i}`));

        // mouse hover
        $(`.tooltip-area#${i}`).hover(function() {

            let offset = $(`.tooltip-area#${i}`).offset();

            $(`.tooltip:hidden`).eq(i).css({
                top: offset.top - 130,
                left: offset.left - 62,
                display: "block"
            })

            $(`.tooltip:hidden`).eq(i).animate({ opacity: 1.0 }, 0);
            // move away mouse
        },  function(){
            $(`.tooltip`).eq(i).animate({ opacity: 0.0 }, 200);
            $(`.tooltip`).eq(i).css({ display: "none" });
        })

    }


});*/
