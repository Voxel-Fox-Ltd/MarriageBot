async function setBeforeButton(origin, guildId) {
    document.getElementById("before-guild-input").value = guildId;
    let base = document.getElementById("before-guilds");
    for(const button of base.getElementsByClassName("button")) {
        button.disabled = false;
    }
    base = document.getElementById("after-guilds");
    for(const button of document.getElementsByClassName("button")) {
        button.disabled = false;
    }
    origin.disabled = true;
}


async function setAfterButton(origin, guildId) {
    document.getElementById("after-guild-input").value = guildId;
    let base = document.getElementById("after-guilds");
    for(const button of document.getElementsByClassName("button")) {
        button.disabled = false;
    }
    await sendPostRequest();
}


async function sendPostRequest() {
    let base = document.getElementById("before-guilds");
    for(const button of base.getElementsByClassName("button")) {
        button.disabled = true;
    }
    base = document.getElementById("after-guilds");
    for(const button of document.getElementsByClassName("button")) {
        button.disabled = true;
    }
    fetch("/change_gold_guild", {
        method: "POST",
        body: JSON.stringify({
            before: document.getElementById("before-guild-input").value,
            after: document.getElementById("after-guild-input").value,
        }),
    }).then((response) => {
        return response.json();
    }).then((data) => {
        if(data.error) {
            return alert(data.error);
        }
        else {
            setTimeout(location.reload.bind(location), 100);
        }
    });
}
