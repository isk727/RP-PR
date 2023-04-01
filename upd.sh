#!/bin/bash
if [ $# -ne 1 ]; then
  echo 'usage : upd.sh [version]' 1>&2
  exit 1
fi
base='/usr/share/webiopi/'
path=(${base}'python/' ${base}'htdocs/' ${base}'htdocs/js/' ${base}'htdocs/css/')
files=('script.py' 'play.html' 'script.js' 'style.css')
url='https://raw.githubusercontent.com/isk727/RP-PR/main/'
today=`date "+%Y%m%d%H%M%S"`
i=0
for f in ${files[@]}
do
  if [ -e ${f} ]; then
    sudo rm ${f}
  fi
  wget ${url}$1/${f}
  chmod 755 ${f}
  sudo mv ${path[i]}${f} ${path[i]}${f}.${today}
  sudo mv ${f} ${path[i]}.
  i=$(expr $i + 1)
done
echo 'Update to ver '$1' is completed!'
