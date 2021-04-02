===============
Troubleshooting
===============

This troubleshooting guide includes common issues users have faced and tips for dealing with them.

If you don't find answers to your problems here, be sure to check out ``betterproto``'s `Slack`!

Upgrading betterproto in a poetry environment
=============================================

It seems like in some situations, installing and then updating ``betterproto`` in ``poetry`` environments doesn't work. If, after updating ``betterproto``, you're not getting the new features you wanted, in might be because of the current virtual environment ``poetry`` has created. While there's probably a "surgical" fix, we've found that removing the venv and re-installing it works.

To do that, run ``poetry env info`` to see the venv path:

```sh
❯ poetry env info

Virtualenv
Python:         3.8.7
Implementation: CPython
Path:           /home/username/.cache/pypoetry/virtualenvs/project-name-random-py3.8  # <-- THIS PATH
Valid:          True
```

Then just ``rm -rf`` that path to delete the venv, and re-create the env using `poetry shell` and `poetry install`.

.. _Slack: https://join.slack.com/t/betterproto/shared_invite/zt-f0n0uolx-iN8gBNrkPxtKHTLpG3o1OQ

