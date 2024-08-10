module.exports = {
    apps: [{
        name: 'oxy',
        script: 'main.py',
        cwd: '/home/oxy/oxy_v2',
        interpreter: '/usr/bin/python3.12',
        env: {
            "PATH": process.env.PATH + ":/usr/bin"
        }
    }]
};