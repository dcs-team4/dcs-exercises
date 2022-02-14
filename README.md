# DCS Team 4 Exercises

Repository for code related to exercises in _Design of Communicating Systems_.

## Project Setup

1. Clone the repo:

```
git clone https://github.com/dcs-team4/dcs-exercises.git
```

2. Navigate to the right folder:

```
cd dcs-exercises
```

3. Verify your Python installation:

```
python3 --version
```

Output should be `Python 3.x.x` (ideally 3.10+). If not, get the latest version here: https://www.python.org/downloads/

4. Install project dependencies:

```
pip install -r requirements.txt
```

5. Enable Jupyter widgets:

```
jupyter nbextension enable --py widgetsnbextension
```

Open the notebooks (`.ipynb` files) in VSCode, or your favorite Jupyter notebook editor.

## VSCode Setup

1. Install VSCode<br>https://code.visualstudio.com/

2. Install Python extension (includes Jupyter)<br>https://marketplace.visualstudio.com/items?itemName=ms-python.python

3. Install Live Share extension<br>https://marketplace.visualstudio.com/items?itemName=MS-vsliveshare.vsliveshare

4. Log in to VSCode with GitHub (bottom left corner of VSCode window)

Now you should be able to open Jupyter notebooks and run code within them.

To check that it works:

1. Go to `File -> Open Folder` in VSCode
2. Find and open the `dcs-exercises` folder from earlier (should be in `[your-username]/dcs-exercises`)
3. Click one of the `.ipynb` files under one of the `unitX` folders now on the left in VSCode
4. Try running one of the code blocks in the notebook
