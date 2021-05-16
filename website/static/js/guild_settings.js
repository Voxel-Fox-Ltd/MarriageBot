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
        alert("Preifx updated.");
    }
    else {
        let data = await response.json();
        alert(data.error);
    }
}
