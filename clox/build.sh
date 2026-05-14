#!/bin/env bash
set -euo pipefail

rm -rf build
cmake -S . -B build
cmake --build build