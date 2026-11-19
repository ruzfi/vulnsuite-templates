#!/bin/sh
cd "$(dirname "$0")"
N=${N:-60}
for img in vuln fix-mail; do
  for vm in "seq none" "seq-prime none" "seq-prime-delay1ms none" "freeze sigstop" "freeze-prime sigstop" "freeze-prime pause"; do
    set -- $vm
    echo "== $img $1 $2"; ./run_mail.sh $img $1 $2 $N > out/mail-$img-$1-$2.log 2>&1; tail -1 out/mail-$img-$1-$2.log
  done
done
