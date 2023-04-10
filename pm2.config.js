function generate(name, script) {
    return {
        name: name,
        autorestart: false,
        script: script,
        cwd: "/home/kae/MarriageBot",
    }
}


module.exports = {
    apps: [
        generate("mb", ".venv/bin/vbu run-interactions --port 8001 --path /"),
        generate("gold", ".venv/bin/vbu run-bot . config/gold.toml --shardcount 1"),
        generate("web", ".venv/bin/vbu run-website --port 8000"),
        generate("sharder", ".venv/bin/vbu run-sharder --loglevel debug --port 8888 --concurrency 16"),
    ]
}


console.log(module.exports.apps);
