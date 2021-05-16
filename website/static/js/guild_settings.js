async function updateGuildPrefix(submitButton) {

    // Get the form node
    let form = submitButton;
    while (form.nodeName !== "FORM") {
        form = form.parentNode;
    }

    // Send the web request
    let response = await fetch("/set_prefix", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(Object.fromEntries(new URLSearchParams(new FormData(form)))),
    });

    // Tell the user what happened
    if(response.ok) {
        alert("The bot prefix for your guild has been updated.");
    }
    else {
        let data = await response.json();
        alert(data.error);
    }
}


async function updateGuildGifsEnabled(submitButton) {

    // Get the form node
    let form = submitButton;
    while (form.nodeName !== "FORM") {
        form = form.parentNode;
    }

    // Send the web request
    let response = await fetch("/set_gifs_enabled", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(Object.fromEntries(new URLSearchParams(new FormData(form)))),
    });

    // Tell the user what happened
    if(response.ok) {
        alert("Gifs for your guild are now updated.");
    }
    else {
        let data = await response.json();
        alert(data.error);
    }
}



async function updateGuildIncestEnabled(submitButton) {

    // Get the form node
    let form = submitButton;
    while (form.nodeName !== "FORM") {
        form = form.parentNode;
    }

    // Send the web request
    let response = await fetch("/set_incest_enabled", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(Object.fromEntries(new URLSearchParams(new FormData(form)))),
    });

    // Tell the user what happened
    if(response.ok) {
        alert("Incest for your guild is now updated.");
    }
    else {
        let data = await response.json();
        alert(data.error);
    }
}
