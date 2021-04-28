const table = document.querySelector("#query-results");

const metaDataString = document.querySelector("#meta-data");
const metaDataTables = JSON.parse(metaDataString.innerText);
// these tables are only a single row

const freqTables = document.querySelectorAll(".freq-table")

const listFreqTableWrapper = document.querySelector("#freq-table-wrapper");

// extra information for every anchor x_lemma
const tooltipTableString = document.querySelector("#extra-information");
const tooltipTables = JSON.parse(tooltipTableString.innerText);

// pagination
// function called before page finishes loading
$(function(){

    const fTables = freqTables.length;

    for (let fTable = 1; fTable <= fTables; fTable++) {
        listFreqTableWrapper.innerHTML += `<div class="freq-table-show">Frequency Table (Anchors ${fTable-1}-${fTable})</div>`;
    }

    const fTablesDisplay = document.querySelectorAll(".freq-table-show");
    for (let i = 0; i < fTablesDisplay.length; i++){
        fTablesDisplay[i].appendChild(freqTables[i]);
    }

    for (let fTable of fTablesDisplay){

        fTable.addEventListener("click", function() {

            if(fTable.firstElementChild.style.display === "block"){
               fTable.firstElementChild.style.display = "none";
            }else{
               fTable.firstElementChild.style.display = "block";
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

// th = column
// td = row

// overwrite function for Object prototype
Object.size = function(obj) {
  let size = 0,
      key;
  for (key in obj) {
    if (obj.hasOwnProperty(key)) size++;
  }
  return size;
};

for(let r in metaDataTables){

    //console.log(r);
    let contentDivColl = document.querySelectorAll(`.coll-${r}`);
    let contentDivPuw = document.querySelectorAll(`.puw-${r}`);

    // place table inside div
    for(let content of contentDivColl){
        content.innerHTML = metaDataTables[r];
    }

    const oldTable = document.querySelector(`#md-${r}`);

    let newTable = document.createElement("table");

    const newRowValuesD = {};
    const newRowValuesV = {};

    for(let i = 0; i<oldTable.rows[0].cells.length; i++) {
        newRowValuesD[i] = oldTable.rows[0].cells[i].innerText;
        newRowValuesV[i] = oldTable.rows[1].cells[i].innerText;
    }

    for(let j = 0; j<Object.size(newRowValuesD); j++){

        let tr = document.createElement("tr");
        let de = document.createElement("td");
        let val = document.createElement("td");

        de.innerText = newRowValuesD[j];
        val.innerText = newRowValuesV[j];

        tr.appendChild(de);
        tr.appendChild(val);

        newTable.appendChild(tr);
    }


    // make new table:

    oldTable.innerHTML = "";
    oldTable.innerHTML = newTable.innerHTML;
    oldTable.style.width="100%";

    // make a duplicate table
    // insert into pop up window div
    // assign a different id
    for(let content of contentDivPuw){
        let puwTable = document.createElement("table");
        puwTable.innerHTML = oldTable.innerHTML;
        puwTable.id = `puw-md-${r}`;
        content.appendChild(puwTable);
    }


}

const allMetaTables = document.querySelectorAll('*[id^="md-t"]');


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

// div with class tooltip around all tables (hide tooltip)
// div with class tooltip area around all tweets

tooltipCounter = 0
for(let tbl in tooltipTables){
    let tooltip = document.createElement("div")
    tooltip.classList.add("tooltip");
    tooltip.classList.add(`row-${tbl}`);
    tooltip.innerHTML = tooltipTables[tbl];
    tooltip.style.display = "none";
    document.body.appendChild(tooltip);
    tooltipCounter += 1;
}

// show tooltip with extra information for every row
// implementing tooltip

const tooltipCheckBox = document.querySelector("#tooltip-on");


function enableTooltip(){

    if(tooltipCheckBox.checked === true){
    // mouse hover
        for(let i = 0; i<=tooltipCounter; i++){
            //console.log($(`.tooltip-area#${i}`));
            console.log(`row-${i}`);

            // mouse hover
            $(`.match-highlight.row-${i}`).hover(function() {

                let offset = $(`.match-highlight.row-${i}`).offset();

                $(`.tooltip.row-${i}`).css({
                    top: offset.top - 130,
                    right: offset.right - 20,
                    display: "block"
                })

                $(`.match-highlight.row-${i}`).css({ cursor: "help" });

                $(`.tooltip.row-${i}`).animate({ opacity: 1.0 }, 0);
                // move away mouse
            },  function(){
                $(`.tooltip.row-${i}`).animate({ opacity: 0.0 }, 200);
                $(`.tooltip.row-${i}`).css({ display: "none" });
            })

        }
    }else{

        for(let i = 0; i<=tooltipCounter; i++){
                $(`.match-highlight.row-${i}`).hover(function() {
                    $(`.tooltip.row-${i}`).animate({ opacity: 0.0 }, 200);
                    $(`.tooltip.row-${i}`).css({ display: "none" });
                    $(`.match-highlight.row-${i}`).css({ cursor: "default" });
                // move away mouse
                },  function(){
                    $(`.tooltip.row-${i}`).animate({ opacity: 0.0 }, 200);
                    $(`.tooltip.row-${i}`).css({ display: "none" });
                })
        }

    }
}


