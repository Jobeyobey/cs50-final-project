// Enable/Disable Record Session input overlay
function overlayOn() {
    document.getElementById("overlay").style.display = "flex";
}
function overlayOff() {
    document.getElementById("overlay").style.display = "none";
}

function tileOverlayOn(tile) {
    overlayOn();
    document.getElementById("overlay-title").innerHTML = tile.name
    document.getElementById("overlay-date").innerHTML = tile.time
    document.getElementById("overlay-result").innerHTML = tile.result
    document.getElementById("overlay-note").innerHTML = tile.note
    console.log(document.getElementById("input-title").innerHTML)
}

// Function to convert HTML unicode characters
function HTMLconvert(str)
{
str = str.replace(/&amp;#10;/g, "<br>");
str = str.replace(/&amp;quot;/g, '"');
return str;
}