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


async function updatePreview(submitButton) {
    let form = submitButton;
    while (form.nodeName !== "FORM") {
        form = form.parentNode;
    }
    let urlParams = new URLSearchParams(new FormData(form));
    let iframe = document.getElementById('preview-iframe');
    iframe.contentWindow.location = "/tree_preview?" + urlParams.toString();
}


function adjustIframeHeight(frame) {
    if(frame.contentWindow.document.getElementById("preview").scrollHeight > 200) {
        frame.style.height = `${frame.contentWindow.document.body.scrollHeight}px`;
    }
    else {
        frame.style.height = "auto";
    }
}
