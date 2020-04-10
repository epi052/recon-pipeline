from pathlib import Path

from .config import tool_paths, defaults

# tool definitions for recon-pipeline's auto-installer
tools = {
    "luigi-service": {
        "installed": False,
        "dependencies": None,
        "commands": [
            f"sudo cp {str(Path(__file__).parents[2] / 'luigid.service')} /lib/systemd/system/luigid.service",
            f"sudo cp $(which luigid) /usr/local/bin",
            "sudo systemctl daemon-reload",
            "sudo systemctl start luigid.service",
            "sudo systemctl enable luigid.service",
        ],
        "shell": True,
    },
    "seclists": {
        "installed": False,
        "dependencies": None,
        "shell": True,
        "commands": [
            f"bash -c 'if [[ -d {defaults.get('tools-dir')}/seclists ]] ; then cd {defaults.get('tools-dir')}/seclists && git fetch --all && git pull; else git clone https://github.com/danielmiessler/SecLists.git {defaults.get('tools-dir')}/seclists; fi'"
        ],
    },
    "searchsploit": {
        "installed": False,
        "dependencies": None,
        "shell": True,
        "commands": [
            f"bash -c 'if [[ -d {Path(tool_paths.get('searchsploit')).parent} ]] ; then cd {Path(tool_paths.get('searchsploit')).parent} && git fetch --all && git pull; else git clone https://github.com/offensive-security/exploitdb.git {defaults.get('tools-dir')}/exploitdb; fi'",
            f"cp -n {Path(tool_paths.get('searchsploit')).parent}/.searchsploit_rc {Path.home().resolve()}",
            f"sed -i 's#/opt#{defaults.get('tools-dir')}#g' {Path.home().resolve()}/.searchsploit_rc",
        ],
    },
    "masscan": {
        "installed": False,
        "dependencies": None,
        "commands": [
            "git clone https://github.com/robertdavidgraham/masscan /tmp/masscan",
            "make -s -j -C /tmp/masscan",
            f"mv /tmp/masscan/bin/masscan {tool_paths.get('masscan')}",
            "rm -rf /tmp/masscan",
            f"sudo setcap CAP_NET_RAW+ep {tool_paths.get('masscan')}",
        ],
    },
    "amass": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            f"{tool_paths.get('go')} get -u github.com/OWASP/Amass/v3/...",
            f"cp ~/go/bin/amass {tool_paths.get('amass')}",
        ],
        "shell": True,
        "environ": {"GO111MODULE": "on"},
    },
    "aquatone": {
        "installed": False,
        "dependencies": None,
        "shell": True,
        "commands": [
            "mkdir /tmp/aquatone",
            "wget -q https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /tmp/aquatone/aquatone.zip",
            "unzip /tmp/aquatone/aquatone.zip -d /tmp/aquatone",
            f"mv /tmp/aquatone/aquatone {tool_paths.get('aquatone')}",
            "rm -rf /tmp/aquatone",
        ],
    },
    "corscanner": {
        "installed": False,
        "dependencies": None,
        "shell": True,
        "commands": [
            f"bash -c 'if [[ -d {Path(tool_paths.get('CORScanner')).parent} ]] ; then cd {Path(tool_paths.get('CORScanner')).parent} && git fetch --all && git pull; else git clone https://github.com/chenjj/CORScanner.git {Path(tool_paths.get('CORScanner')).parent}; fi'",
            f"pip install -r {Path(tool_paths.get('CORScanner')).parent / 'requirements.txt'}",
            "pip install future",
        ],
    },
    "gobuster": {
        "installed": False,
        "dependencies": ["go", "seclists"],
        "commands": [
            f"{tool_paths.get('go')} get github.com/OJ/gobuster",
            f"(cd ~/go/src/github.com/OJ/gobuster && {tool_paths.get('go')} build && {tool_paths.get('go')} install)",
        ],
        "shell": True,
    },
    "tko-subs": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            f"{tool_paths.get('go')} get github.com/anshumanbh/tko-subs",
            f"(cd ~/go/src/github.com/anshumanbh/tko-subs && {tool_paths.get('go')} build && {tool_paths.get('go')} install)",
        ],
        "shell": True,
    },
    "subjack": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            f"{tool_paths.get('go')} get github.com/haccer/subjack",
            f"(cd ~/go/src/github.com/haccer/subjack && {tool_paths.get('go')} install)",
        ],
        "shell": True,
    },
    "webanalyze": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            f"{tool_paths.get('go')} get github.com/rverton/webanalyze/...",
            f"(cd ~/go/src/github.com/rverton/webanalyze && {tool_paths.get('go')} build && {tool_paths.get('go')} install)",
        ],
        "shell": True,
    },
    "recursive-gobuster": {
        "installed": False,
        "dependencies": ["gobuster", "seclists"],
        "shell": True,
        "commands": [
            f"bash -c 'if [[ -d {Path(tool_paths.get('recursive-gobuster')).parent} ]] ; then cd {Path(tool_paths.get('recursive-gobuster')).parent} && git fetch --all && git pull; else git clone https://github.com/epi052/recursive-gobuster.git {Path(tool_paths.get('recursive-gobuster')).parent}; fi'"
        ],
    },
    "go": {
        "installed": False,
        "dependencies": None,
        "commands": [
            "wget -q https://dl.google.com/go/go1.13.7.linux-amd64.tar.gz -O /tmp/go.tar.gz",
            "sudo tar -C /usr/local -xvf /tmp/go.tar.gz",
            f'bash -c \'if [[ ! $(echo "${{PATH}}" | grep $(dirname {tool_paths.get("go")})) ]]; then echo "PATH=${{PATH}}:/usr/local/go/bin" >> ~/.bashrc; fi\'',
        ],
    },
}
