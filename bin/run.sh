#!/bin/env bash
# jupyter nbconvert --execute --to python RSS-Posts-Gießen.ipynb &&
python3.10 RSS-Posts-Gießen.py -s && xmllint --format atom.xml > test.xml && mv test.xml atom.xml
