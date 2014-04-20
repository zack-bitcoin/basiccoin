import networking, tools, custom
networking.send_command(['localhost', 8900], {'type':'blockCount', 'version':custom.version})
