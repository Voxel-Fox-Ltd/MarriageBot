async function updateGuildPrefix(submitButton) {
    // Get the form node
    let form = submitButton;
    while (form.nodeName !== "FORM") {
        form = form.parentNode;
    }

    // Send the web request
    response = await fetch("/set_prefix", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(Object.fromEntries(URLSearchParams(new FormData(form)))),
    });
    if(response.ok) {
        alert("Yo it worked sick");
    }
    else {
        alert("AAAAAAA ERROR");
    }
}
