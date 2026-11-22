#!/bin/bash
# usage: run2.sh outdir crawl file...  (2 in parallel; parse+aggregate gz straight to per-site totals)
out=$1; crawl=$2; shift 2
todo=(); for f in "$@"; do b=$(basename $f .gz); [ -s $out/$b.json ] || todo+=($f); done
printf '%s\n' "${todo[@]:0:${N:-2}}" | xargs -P${N:-2} -I{} sh -c 'b=$(basename {} .gz); python3 '$HOME'/main/agg.py {} '$out'/$b.tmp '$crawl' >/dev/null 2>&1 && mv '$out'/$b.tmp '$out'/$b.json'
ls $out/*.json 2>/dev/null | wc -l
