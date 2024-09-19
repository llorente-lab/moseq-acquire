# moseq-acquire
Very simple GUI-based MoSeq data acquisition code based on https://github.com/dattalab/orbbec-acquire/

To install and run, please follow the following steps:

## Step 1: Install `git`

```bash
sudo apt update
sudo apt install git
```

## Step 2: Set up pyorbbecsdk
```bash
sudo apt-get install python3-dev python3-venv python3-pip python3-opencv
cd pyorbbecsdk
python3 -m venv ./venv
source venv/bin/activate
pip3 install -r requirements.txt
mkdir build
cd build
cmake -Dpybind11_DIR=`pybind11-config --cmakedir` ..
make -j4
make install
```

## Step 3: Clone moseq-acquire
```bash
cd .. # make sure you're in pyorbbecsdk directory
git clone https://github.com/athp18/moseq-acquire.git
```

To run, try: 
```python
cd /path/to/pyorbbecsdk
source venv/bin/activate
cd moseq-acquire
python3 gui.py
```
