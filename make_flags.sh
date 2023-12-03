#!/usr/bin/env bash

curl -sS https://raw.githubusercontent.com/linuxmint/hypnotix/master/usr/share/hypnotix/countries.list -o ./countries.list
echo "FO:Faroe Islands" >> ./countries.list

for country in `cat ./flag_order.txt | grep -v "^$" | grep -v "#"`; do
    country_name=`echo "$country"|sed -e "s/_/ /g"`

    [[ "$country_name" == "korea" ]] && country_name="south korea"
    [[ "$country_name" == "uk" ]] && country_name="united kingdom"

    country_code_line=`cat ./countries.list|grep -m 1 -i "$country_name"`

    if [[ -z "$country_code_line" ]]; then
        echo "MISSING COUNTRY CODE FOR: $country"
        exit 1
    elif [[ -n "$country_code_line" ]]; then
        IFS=':'; country_code_arr=($country_code_line); unset IFS
        country_code="${country_code_arr[0],,}"
    fi

    echo "[<img src=\"https://hatscripts.github.io/circle-flags/flags/$country_code.svg\" width=\"24\">](lists/$country.md)"
done

rm ./countries.list
