# Bugsnag Python demo (no framework)

This application demonstrates how to use Bugsnag with basic Python.

## Setup

Try this out with [your own Bugsnag account](https://app.bugsnag.com/user/new)! You'll be able to see how the errors are reported in the dashboard, how errors are grouped and how they relate to the original source.

Most of our python example apps serve a basic web app, but this example, to remain framework-agnostic, runs simply in terminal.

To get set up, follow the instructions below. Don't forget to replace the placeholder API token with your own!

1. Clone the repo and `cd` into this directory:
  ```sh
  git clone https://github.com/bugsnag/bugsnag-python.git
  cd bugsnag-python/example/plain
  ```

1. Before testing it, open up the `app.py` file and configure your API key.

1. Install dependencies
  ```shell
  pip install -r requirements.txt
  ```

1. Run the application in your terminal.
  ```shell
  python -i app.py
  ```

1. View the resulting error reports in your [Bugsnag dashboard](https://app.bugsnag.com/).

For more information, see our documentation:
https://docs.bugsnag.com/platforms/python/
