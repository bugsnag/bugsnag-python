
Contributing
------------

-   [Fork](https://help.github.com/articles/fork-a-repo) the [notifier on github](https://github.com/bugsnag/bugsnag-python)
-   Commit and push until you are happy with your contribution
-   Run the tests
-   [Make a pull request](https://help.github.com/articles/using-pull-requests)
-   Thanks!

Running the tests
-----------------

-   Install [nosetests](https://nose.readthedocs.org/) with `pip install nose`
-   Run the tests:

    ```bash
    ./setup.py test
    ```

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

## Doing a release

* Update the version number in setup.py
* Update the CHANGELOG.md, and README.md if necessary
* Commit

    ```
    git commit -am v2.x.x 
    ```

* Tag the release in git

    ```
    git tag v2.x.x
    ```

* Push to git

    ```
    git push origin master && git push --tags
    ```

* Push the release to PyPI

    ```
    python setup.py sdist upload
    ```


