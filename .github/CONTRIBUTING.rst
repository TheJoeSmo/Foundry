How To Contribute
=================

Thank you for considering to contribute to ``Foundry``!
People like yourself are the lifeblood of the community and this tool.

The purpose of this document is to codify the processes required to contribute to this
project to empower yourself and the community to contribute.

Support
-------

If GitHub is overwelming, but still want to help the community: help fellow developers
on `StackOverflow <https://stackoverflow.com/questions/tagged/python-nametable>`_.

The official tag is ``python-foundry`` and support enables us to improve ``Foundry`` instead.

Also, if development is not your forte, you can also help the game design community over
at `Discord <https://discord.gg/MMExJKExGG>`_.

Getting Started
---------------

You will need a working version of Python between the versions specified inside the
`toml file <https://github.com/TheJoeSmo/Foundry/blob/master/pyproject.toml>`_ and to install
`Poetry <https://pypi.org/project/poetry/>`_.
To install the remaining dependencies, simply write the following:

.. code-block:: console

    $ git clone git@github.com:TheJoeSmo/Foundry.git
    $ cd Foundry
    $ poetry install

This will install the remaining dependencies.  It is recommended to run this command after
each fetch or update to the project's dependencies, as it ensures the continous integration
environment is equivelent to your local one.  

If everything worked, you should be able to run the following and see that every test passed:

.. code-block:: console

    $ poetry run pytest tests/ --verbose --failed-first --ignore="tests/game/gfx/objects/" --ignore="tests/game/level/test_level_drawing.py" --ignore="tests/gui/test_world_map.py"

Workflow
--------

- No contribution is too small!  Fixes to typos and grammar are welcome.
- Try to limit each pull request to a single change.
- Always add tests and documentation for your code.
  We recommend using `test driven development <https://www.youtube.com/watch?v=yfP_v6qCdcs>`_
  to develop your software.  It helps divide the program into smaller parts, which helps both
  yourself and the reviewer.  If either tests or documentation are not provided, your code
  will be inelegiable to be merged.
- Make sure that your new tests would otherwise fail without your change.
- Ensure that your new test and the remaining tests pass using pytest.
  When making a pull request, Github will automatically run these tests.  We will not provide
  feedback until all tests pass or explicitly asked. 
- Once you've addressed review feedback, make sure to bump the pull request with a small note
  so we know you have finished.

Code
----
- Obey `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ and 
  `Numpy Docs style guide <https://numpydoc.readthedocs.io/en/latest/format.html>`_.
  We use ``"""`` for on seperate lines for docstrings.

  .. code-block:: python

      def func(x: int) -> str:
          """
          Do something.

          Parameters
          ----------
          x : int
              Description of parameter `x`.

          Returns
          -------
          str
              Description of the string return value.
          """
- We use `Black <https://pypi.org/project/black/>`_, 
  `Flake8 <https://pypi.org/project/flake8/>`_, and `Isort <https://pypi.org/project/isort/>`_
  as our linters.
  We recommend you set run the following commands before making a pull request.  Fortunately,
  we have set up a simple method to get everything running by default.  Simply run the
  following and these checks will be ran before every pull request.

  .. code-block:: console
    
    $ python -m pip install pre-commit
    $ pre-commit install

  or for Linux users:

  .. code-block:: console
    
    $ python3 -m pip install pre-commit
    $ pre-commit install

  You can also run them anytime using the following command:

  .. code-block:: console

    $ pre-commit run --all-files

  Notes:
  
  Depending on your shell you may run into a problem where ``pre-commit`` is not found.
  This is because the path is found inside ``~/.profile``.  We have provided the most common
  fixes for ``bash`` and ``zsh``.

  Bash: Add ``source ~/.profile`` inside ``~/.bashrc``.
  
  ZHS: Add ``[[ -e ~/.profile ]] && emulate sh -c 'source ~/.profile'`` inside ``~/.zshrc``.

  For more reading: `ZSH not hitting ~/.profile <https://superuser.com/questions/187639/zsh-not-hitting-profile>`_

Tests
-----

- Tests should write the asserts as ``expected == actual``, to provide easier readability
- To run the test suite, simply write the following in your console:
  
  .. code-block:: console

    $ poetry run pytest tests/ --verbose --failed-first --ignore="tests/game/gfx/objects/" --ignore="tests/game/level/test_level_drawing.py" --ignore="tests/gui/test_world_map.py"
