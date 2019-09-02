# recon-pipeline

## Command Execution

### PYTHONPATH
To run the pipelines, you need to set your `PYTHONPATH` environment variable to the path of this project on disk.  This can be accomplished in a few ways, two solutions are offered.  

1. Prepend PYTHONPATH=/path/to/recon-pipline to any luigi pipeline command being run.
2. Add `export PYTHONPATH=/path/to/recon-pipeline` to your `.bashrc`   

### Scheduler

Either add `--local-scheduler` to your `luigi` command on the command line or run `systemctl start luigid` before attempting to run any `luigi` commands.

#### Systemd service file for luigid
``` 
cat >> /lib/systemd/system/luigid.service << EOF 
[Unit]
Description=Spotify Luigi server
Documentation=https://luigi.readthedocs.io/en/stable/
Requires=network.target remote-fs.target
After=network.target remote-fs.target
[Service]
Type=simple
ExecStart=/usr/local/bin/luigid --background --pidfile /var/run/luigid.pid --logdir /var/log/luigi
[Install]
WantedBy=multi-user.target
EOF
```