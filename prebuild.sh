#! /bin/sh
(cd docs && make clean)
poetry run sphinx-apidoc -feTM --remove-old -odocs/api aim