// Enable/Disable Record Session input overlay
function overlayOn() {
    document.getElementById("overlay").style.display = "flex";
}
function overlayOff() {
    document.getElementById("overlay").style.display = "none";
}

function playOverlayOn(tile) {
    overlayOn();
    document.getElementById("overlay-title").innerHTML = tile.name
    document.getElementById("overlay-date").innerHTML = tile.time
    document.getElementById("overlay-result").innerHTML = tile.result
    document.getElementById("overlay-note").innerHTML = tile.note
}

// Function to convert HTML unicode characters
function HTMLconvert(str) {
str = str.replace(/&amp;#10;/g, "<br>");
str = str.replace(/&amp;quot;/g, '"');
return str;
}


// Add/remove/accept/reject friend buttons
function updateFriend(action, user2) {
    var req = new XMLHttpRequest();

    var url = `/updatefriend?action=${action}&user2=${user2}`;

    req.open("GET", url, false)
    req.send()

    location.reload()
}


// Updating user profile icons
function updateIcon(input) {
    button = document.getElementById("icon-submit");
    button.setAttribute("onclick", `sendIconUpdate(${input})`);
}

function sendIconUpdate(input) {
    var req = new XMLHttpRequest();

    var url = `/updateicon?input=${input}`;

    req.open("GET", url, false);
    req.send();

    if (req.status == "200") {
        location.reload()
    }
}