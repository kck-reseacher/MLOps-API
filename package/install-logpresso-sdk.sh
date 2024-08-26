#!/bin/bash
# install 1 : conda dependency
# please check requirements : gcc, gcc-c++
if [[ -z $AIMODULE_PATH ]]; then
    echo "plz export $AIMODULE_PATH"
    exit 2
fi

PYTHON_VERSION="3.6"
CONDA_NAME="ai-module"

cd $AIMODULE_PATH/package
eval "$(conda shell.bash hook)"
conda activate $CONDA_NAME

# Install Logpresso Python SDK : requirements included in requirements-pip.txt
cp $AIMODULE_PATH/package/logpresso-sdk-python-master.tar $CONDA_PREFIX"/lib/python$PYTHON_VERSION/site-packages/"
cd $CONDA_PREFIX"/lib/python$PYTHON_VERSION/site-packages"
tar -xvf logpresso-sdk-python-master.tar
cd src
python setup.py develop
# copy logpresso client jar file.
cp $AIMODULE_PATH/package/araqne-logdb-client-1.7.1-package.jar $CONDA_PREFIX"/lib/python$PYTHON_VERSION/site-packages/src/logpresso/"
cd $AIMODULE_PATH/package

conda deactivate
if [ ! -d $AIMODULE_PATH/output ]; then
    mkdir $AIMODULE_PATH/output
fi