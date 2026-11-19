#!/bin/sh
cd "$(dirname "$0")"
N=${N:-60}
for img in vuln fix-resolver; do
  for vm in "seq-nosplit none" "seq-split none" "freeze-nosplit-dnsfirst sigstop" "freeze-split-dnsfirst sigstop" "freeze-split-rstfirst sigstop" "freeze-split-dnsfirst pause"; do
    set -- $vm
    echo "== $img $1 $2"; ./run_resolver.sh $img $1 $2 $N > out/res-$img-$1-$2.log 2>&1; tail -1 out/res-$img-$1-$2.log
  done
done
