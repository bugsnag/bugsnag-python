
Contributing
------------

-   [Fork](https://help.github.com/articles/fork-a-repo) the [notifier on github](https://github.com/bugsnag/bugsnag-python)
-   Commit and push until you are happy with your contribution
-   Run the tests
-   [Make a pull request](https://help.github.com/articles/using-pull-requests)
-   Thanks!

Running the tests
-----------------

- Install the development dependencies:

      pip install -r dev_requirements.txt

- Run the tests:

      tox


- Lint the changes:

      flake8 bugsnag


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

* Update the version number in setup.py
* Update the CHANGELOG.md, and README.md if necessary
* Commit

    ```
    git commit -am v3.x.x
    ```

* Tag the release in git

    ```
    git tag v3.x.x
    ```

* Push to git

    ```
    git push origin master && git push --tags
    ```

* Push the release to PyPI

      python setup.py sdist bdist_wheel
      twine upload dist/*

## Update docs.bugsnag.com

Update the setup guides for Python (and its frameworks) with any new content.

