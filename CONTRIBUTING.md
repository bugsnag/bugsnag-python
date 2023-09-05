
Contributing
------------

-   [Fork](https://help.github.com/articles/fork-a-repo) the [notifier on github](https://github.com/bugsnag/bugsnag-python)
-   Commit and push until you are happy with your contribution
-   Run the tests
-   [Make a pull request](https://help.github.com/articles/using-pull-requests)
-   Thanks!

Running the tests
-----------------

The quickest way to get feedback is to run the unit tests.

1.  Install the development dependencies:

    ```
    pip install -r dev_requirements.txt
    ```

2.  Run the unit tests

    ```
    py.test tests --ignore=tests/integrations
    ```

3.  Lint changes

    ```
    flake8 bugsnag tests
    ```

The integration environments are managed via [tox](https://tox.readthedocs.io/).
Some of the integration tests require conflicting dependencies, so the
environment matrix ensures each set is tested. Running `tox` will run every
configuration, or individual environments can be specified to run python version
+ configuration pairs. The complete list of configurations is available in
`tox.ini`.

Examples:

```sh
# Run the unit tests and linter on python 3.8
tox -e py38-tests,py38-lint

# Run the Flask integration tests on python 3.5
tox -e py35-flask

# Run async support tests
tox -e py38-asynctests
```

Running the example django app
------------------------------

-  Install bugsnag somewhere the example app can read from it.

    python setup.py install

- Install the rest of the app requirements

    cd example/django
    pip install -r requirements.txt

- Boot django

    python manage.py runserver

Releasing a new version
-----------------------

If you're on the core team, you can release Bugsnag as follows:

## Prerequisites

* Create a PyPI account
* Get someone to add you as contributer on bugsnag-python in PyPI
* Create or edit the file ~/.pypirc

    ```
    [server-login]
    username: your-pypi-username
    password: your-pypi-password
    ```

* Install the distribution dependencies

      pip install -r dev_requirements.txt

## Making a release

* Create branch for the release

    ```
    git checkout -b release/v4.x.x
    ```

* Update the version number in [`setup.py`](./setup.py) and `bugsnag/notifier.py`(./bugsnag/notifier.py)
* Update the CHANGELOG.md and README.md if necessary
* Commit and open a pull request into `master`
* Merge the PR when it's been reviewed
* Create a release on GitHub, tagging the new version `v4.x.x`
* Push the release to PyPI

    ```
    git fetch --tags && git checkout tags/v4.x.x
    python setup.py sdist bdist_wheel
    twine upload dist/*
    ```

## Update docs.bugsnag.com

Update the setup guides for Python (and its frameworks) with any new content.

