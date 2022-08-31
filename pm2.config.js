function generate(name, script) {
    return {
        name: name,
        autorestart: false,
        script: script,
        cwd: "/home/kae/MarriageBot",
    }
}


const SHARD_COUNT = 720;
const CLUSTER_COUNT = 10;


function generateStatus(index) {
    let min = index * (SHARD_COUNT / CLUSTER_COUNT);
    let max = ((index + 1) * (SHARD_COUNT / CLUSTER_COUNT)) - 1;
    return generate(
        `status${index}`,
        `.venv/bin/vbu run-bot --no-startup --min ${min} --max ${max} --shardcount ${SHARD_COUNT}`,
    )
}


let statusApps = [];
for(let i of Array(CLUSTER_COUNT).keys()) {
    statusApps.push(generateStatus(i))
}


module.exports = {
    apps: [
        generate("mb", ".venv/bin/vbu run-interactions --port 8001 --path /"),
        // ...statusApps,
        generate("gold", ".venv/bin/vbu run-bot . config/gold.toml --shardcount 1"),
        generate("web", ".venv/bin/vbu run-website --port 8000"),
        generate("sharder", ".venv/bin/vbu run-sharder --loglevel debug --port 8888 --concurrency 16"),
    ]
}


console.log(module.exports.apps);
