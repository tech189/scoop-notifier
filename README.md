# Scoop Notifier
 Automatic update checker for apps installed with Scoop written in Python

![Screenshot showing example notification informing that updates are available](<media/screenshot.png>)

## Installation

First make sure you have Python installed, e.g. with `scoop install python` or with `pyenv`

Then install [`poetry`](https://python-poetry.org/), a package/dependency manager for Python:
```
scoop install poetry
```

Then clone this repository somewhere and navigate to it:

```
git clone https://github.com/tech189/scoop-notifier/
cd scoop-notifier
```

Install the necessary dependencies with Poetry:

```
poetry install
```

Finally, run the program with the newly set up environment. The following command sets up a scheduled update check every three hours (180 minutes):
```
poetry run python scoop_notifier\notifier.py --install 180
```

Now, every three hours Scoop will be updated and a notification will display if any of your apps have updates available.