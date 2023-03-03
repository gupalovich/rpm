let burger = document.getElementById("burger");
let sidenav = document.getElementById("sidenav");
let main = document.getElementById("main")


function close_menu(){
    sidenav.classList.remove('_active')
}

main.onclick = close_menu

if (burger && sidenav){
    burger.addEventListener("click", function(e){
        sidenav.classList.toggle('_active');

    })
}
