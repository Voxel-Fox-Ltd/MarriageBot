async function updateBlockedUser(userId) {

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
        alert("Unblocked user.");
    }
    else {
        let data = await response.json();
        alert(data.error);
    }
}
