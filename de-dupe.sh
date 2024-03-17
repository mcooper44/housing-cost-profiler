#!/usr/bin/bash
#https://unix.stackexchange.com/questions/171091/remove-lines-based-on-duplicates-within-one-column-without-sort
awk -i inplace -F',' '!seen[$1]++' housing_list.csv
