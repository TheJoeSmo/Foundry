How To Contribute
=================

Thank you for considering to contribute to ``Foundry``!
People like yourself are the lifeblood of the community and this tool.

The purpose of this document is to codify the processes required to contribute to this
project to empower yourself and the community to contribute.

Support
-------

If GitHub is overwhelming, but still want to help the community: help fellow developers
on StackOverflow [1]_.

The official tag is ``python-foundry`` and support enables us to improve ``Foundry`` instead.

Also, if development is not your forte, you can also help the `game design community <https://discord.gg/MMExJKExGG>`_ 
over at Discord [2]_.

Getting Started
---------------

You will need a working version of Python between the versions specified inside the
`toml file <https://github.com/TheJoeSmo/Foundry/blob/master/pyproject.toml>`_.
To install the remaining dependencies, simply write the following:

.. code-block:: console

    $ git clone git@github.com:TheJoeSmo/Foundry.git
    $ cd Foundry
    $ pip install -r requirements-dev.txt
    $ python -m foundry.main

This will install the remaining dependencies.  It is recommended to run this command after
each fetch or update to the project's dependencies, as it ensures the continuos integration
environment is equivalent to your local one.  

If everything worked, you should be able to run the following and see that every test passed:

.. code-block:: console

    $ python -m pytest

Workflow
--------

- No contribution is too small!  Fixes to typos and grammar are welcome.
- Try to limit each pull request to a single change.
- Always add tests and documentation for your code.
  We recommend using test driven development to develop your software [4]_.
  It helps divide the program into smaller parts, which helps both yourself and the reviewer.  
  If either tests or documentation are not provided, your code will be ineligible to be merged.
- Make sure that your new tests would otherwise fail without your change.
- Ensure that your new test and the remaining tests pass using PyTest.
  When making a pull request, Github will automatically run these tests.  We will not provide
  feedback until all tests pass or explicitly asked. 
- Once you've addressed review feedback, make sure to bump the pull request with a small note
  so we know you have finished.

Code
----
- Obey `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ and 
  `Numpy Docs style guide <https://numpydoc.readthedocs.io/en/latest/format.html>`_ [5]_ [6]_.
  We use ``"""`` for on separate lines for doc-strings.

  .. code-block:: python

      from typing import ClassVar
      
      from attr import attrs

      @attrs(slots=True, auto_attribs=True, eq=True, hash=True, frozen=True)
      class Example:
          """
          This is an example class to showcase the documentation style guidelines as defined by the
          Numpy Doc style guide [1]_.

          This is the extended summary.  We try to avoid this, but it acceptable under some 
          circumstances.  Instead you should use `Notes` to write specific implementation details 
          and so on.  This section should only be used if there is some erroneous details about 
          *functionality* that need to be clarified.

          Attributes
          ----------
          example: str
              An example attribute.
          version: ClassVar[int]
              The amount of times this class has been updated.

          Methods
          -------
          example_method(x: int, y: int = 2) -> str:
              A method to showcase the documentation style guidelines for a function or method.

          See Also
          --------
          example_function: This is `example_method` reincarnated as a function, from the same module.
          module.ExtendedExample: This is `Example` but extended into a novel, inside a sub-module.
          foundry.module.ExtendedExtendedExample: Provide the entire path for a different module.

          Notes
          -----
          Please notice that `example_method` does not include `self` under `Methods`.

          It is advised to only explain private methods this section and any other specific implementation
          detail.

          History of the class or method should go here.

          References
          ----------
          .. [1] The NumpyDoc style guide: `NumpyDocs <https://numpydoc.readthedocs.io/en/latest/format.html>`_
          """

          example: str

          version: ClassVar[int] = 2

          def example_method(self, x: int, y: int = 2) -> str:
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

              Raises
              ------
              Sadness
                  When someone does not document.

              Examples
              --------
              >>> Example().example_method(0)
              This is an example

              Brace yourself for the second example...  You won't expect it.

              >>> Example().example_method(1)
              The Spanish Inquisition
              """
              pass

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
  fixes for ``bash`` and ``zsh`` [7]_.

  Bash: Add ``source ~/.profile`` inside ``~/.bashrc``.
  
  ZHS: Add ``[[ -e ~/.profile ]] && emulate sh -c 'source ~/.profile'`` inside ``~/.zshrc``.

Tests
-----

- Tests should write the asserts as ``expected == actual``, to provide easier readability
- To run the test suite, simply write the following in your console:
  
  .. code-block:: console

    $ python -m pytest

References
----------

.. [1] StackOverflow: https://stackoverflow.com/questions/tagged/python-nametable
.. [2] SMB3 Prime Discord Server: https://discord.gg/MMExJKExGG
.. [3] Poetry Installation Guide: https://python-poetry.org/docs/
.. [4] Test Driven Development Guide: https://www.youtube.com/watch?v=yfP_v6qCdcs
.. [5] PEP 8: https://www.python.org/dev/peps/pep-0008
.. [6] NumpyDoc Guide: https://numpydoc.readthedocs.io/en/latest/format.html
.. [7] ZSH and Poetry Guide: https://superuser.com/questions/187639/zsh-not-hitting-profile
