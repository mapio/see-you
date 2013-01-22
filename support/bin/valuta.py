#!/bin/bash

uid="$1"
timestamp="$2"

export MAKEFILES="$(pwd)/Makefile-student $(pwd)/Makefile-minos"
touch esercizio-*/output-*txt
make -k rdiffs >/dev/null 2>&1
if [ "$(echo ./esercizio-*/eval.txt)" != './esercizio-*/eval.txt' ]; then
	for es in ./esercizio-*/eval.txt; do
		n=$(echo $es | sed 's|.*-\(.*\)/.*|\1|' )
		sed -n "s| *\(.*\) diffs-\(.*\).txt|"$n" \2 \1|p" < $es
	done
fi
