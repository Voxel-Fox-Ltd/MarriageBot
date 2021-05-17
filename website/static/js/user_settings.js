async function updateBlockedUser(submitButton, userId) {

    // Send the web request
    let response = await fetch("/unblock_user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"user_id": userId}),
    });

    // Tell the user what happened
    if(response.ok) {
        submitButton.parentNode.removeChild(submitButton);
        alert("Unblocked user.");
    }
    else {
        let data = await response.json();
        alert(data.error);
    }
}


async function updateTreeColours(submitButton) {

    // Get the form node
    let form = submitButton;
    while (form.nodeName !== "FORM") {
        form = form.parentNode;
    }

    // Send the web request
    let response = await fetch("/colour_settings", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(Object.fromEntries(new URLSearchParams(new FormData(form)))),
    });

    // Tell the user what happened
    if(response.ok) {
        alert("Updated tree colours.");
    }
    else {
        let data = await response.json();
        alert(data.error);
    }
}

