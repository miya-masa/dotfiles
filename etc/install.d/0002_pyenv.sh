#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'


PYENV_ROOT=~/.pyenv
if [ ! -d ${PYENV_ROOT} ]; then
  curl https://pyenv.run | bash
fi
PYENV_SHIMS=${PYENV_ROOT}/shims
PYTHON_VERSION=3.10.1

${PYENV_ROOT}/bin/pyenv install --skip-existing ${PYTHON_VERSION}
${PYENV_ROOT}/bin/pyenv global ${PYTHON_VERSION}
${PYENV_SHIMS}/python -V
${PYENV_SHIMS}/python -m pip install --upgrade pip

export PATH=${PYENV_SHIMS}:${PATH}
