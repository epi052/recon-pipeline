.. _scheduler-ref-label:

Using a Scheduler
=================

The backbone of this pipeline is spotify's `luigi <https://github.com/spotify/luigi>`_ batch process management framework. Luigi uses the concept of a
scheduler in order to manage task execution. Two types of scheduler are available, a **local** scheduler and a
**central** scheduler. The local scheduler is useful for development and debugging while the central scheduler
provides the following two benefits:

- Make sure two instances of the same task are not running simultaneously
- Provide :ref:`visualization <visualization-ref-label>` of everything that’s going on

While in the ``recon-pipeline`` shell, running ``install luigi-service`` will copy the ``luigid.service``
file provided in the repo to its appropriate systemd location and start/enable the service. The result is that the
central scheduler is up and running easily.

The other option is to add ``--local-scheduler`` to your :ref:`scan_command` command from within the ``recon-pipeline`` shell.


