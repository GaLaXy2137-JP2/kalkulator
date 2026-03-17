let activeIndex = -1

function pokazListe(inputId, listaId){

let lista = document.getElementById(listaId)
lista.innerHTML=""
activeIndex = -1

profileList.forEach(function(p){

let div = document.createElement("div")
div.innerText = p

div.onclick=function(){

document.getElementById(inputId).value = p
document.getElementById(inputId+"_hidden").value = p
lista.innerHTML=""

}

lista.appendChild(div)

})

}

function filtruj(event,inputId, listaId){

if(event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Enter") return

let input = document.getElementById(inputId)
let lista = document.getElementById(listaId)
let text = input.value.toLowerCase()

lista.innerHTML=""
activeIndex = -1

profileList.forEach(function(p){

if(p.toLowerCase().includes(text)){

let div = document.createElement("div")
div.innerText = p

div.onclick=function(){

document.getElementById(inputId).value = p
document.getElementById(inputId+"_hidden").value = p
lista.innerHTML=""

}

lista.appendChild(div)

}

})

}

function klawisze(event,inputId, listaId){

let lista = document.getElementById(listaId)
let items = lista.getElementsByTagName("div")

if(items.length === 0) return

if(event.key === "ArrowDown"){

event.preventDefault()
activeIndex++
if(activeIndex >= items.length) activeIndex = 0

}

if(event.key === "ArrowUp"){

event.preventDefault()
activeIndex--
if(activeIndex < 0) activeIndex = items.length-1

}

for(let i=0;i<items.length;i++){
items[i].style.background=""
}

if(items[activeIndex]){
items[activeIndex].style.background="#dfe6e9"
}

if(event.key === "Enter"){

event.preventDefault()

let selected = items[activeIndex]

if(selected){

document.getElementById(inputId).value = selected.innerText
document.getElementById(inputId+"_hidden").value = selected.innerText
lista.innerHTML=""

}

}

if(event.key === "Escape"){
lista.innerHTML=""
}

}