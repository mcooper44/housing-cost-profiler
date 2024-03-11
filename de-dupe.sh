#!/usr/bin/bash
# https://unix.stackexchange.com/questions/30173/how-to-remove-duplicate-lines-inside-a-text-file
awk -i inplace '!seen[$0]++' housing_list.csv
