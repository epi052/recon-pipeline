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
            f"bash -c 'if [[ -d /usr/share/seclists ]]; then ln -s /usr/share/seclists {defaults.get('tools-dir')}/seclists; elif [[ -d {defaults.get('tools-dir')}/seclists ]] ; then cd {defaults.get('tools-dir')}/seclists && git fetch --all && git pull; else git clone https://github.com/danielmiessler/SecLists.git {defaults.get('tools-dir')}/seclists; fi'"
        ],
    },
    "searchsploit": {
        "installed": False,
        "dependencies": None,
        "shell": True,
        "commands": [
            f"bash -c 'if [[ -d /usr/share/exploitdb ]]; then ln -s /usr/share/exploitdb {defaults.get('tools-dir')}/exploitdb && sudo ln -s $(which searchsploit) {defaults.get('tools-dir')}/exploitdb/searchsploit; elif [[ -d {Path(tool_paths.get('searchsploit')).parent} ]]; then cd {Path(tool_paths.get('searchsploit')).parent} && git fetch --all && git pull; else git clone https://github.com/offensive-security/exploitdb.git {defaults.get('tools-dir')}/exploitdb; fi'",
            f"bash -c 'if [[ -f {Path(tool_paths.get('searchsploit')).parent}/.searchsploit_rc ]]; then cp -n {Path(tool_paths.get('searchsploit')).parent}/.searchsploit_rc {Path.home().resolve()}; fi'",
            f"bash -c 'if [[ -f {Path.home().resolve()}/.searchsploit_rc ]]; then sed -i 's#/opt#{defaults.get('tools-dir')}#g' {Path.home().resolve()}/.searchsploit_rc; fi'",
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
            "bash -c 'if [[ ! $(which unzip) ]]; then sudo apt install -y zip; fi'",
            "unzip /tmp/aquatone/aquatone.zip -d /tmp/aquatone"
            f"mv /tmp/aquatone/aquatone {tool_paths.get('aquatone')}",
            "rm -rf /tmp/aquatone",
            "bash -c 'found=false; for loc in {/usr/bin/google-chrome,/usr/bin/google-chrome-beta,/usr/bin/google-chrome-unstable,/usr/bin/chromium-browser,/usr/bin/chromium}; do if [[ $(which $loc) ]]; then found=true; break; fi ; done; if [[ $found = false ]]; then sudo apt install -y chromium-browser ; fi'",
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
