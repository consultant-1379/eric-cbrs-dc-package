#!/bin/bash

_BASE_="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

DOT_TS=${HOME}/.terminal_server
TS_PORT=40022
TS_USER=eccd
TS_SOURCE=${_BASE_}

if [[ -f ${DOT_TS} ]] ; then
  TS=$( cat ${DOT_TS} )
else
  echo "No TerminalServer address set"
  echo -e "\techo TS_IP > ${DOT_TS}"
  exit 1
fi

_USER_=${USER}
_TS_IDENTITY_=${HOME}/cenm/eccd-keypair_ALL.pem
while getopts "u:i:" _o_; do
  case "${_o_}" in
    u)
      _USER_="${OPTARG}";;
    i)
      _TS_IDENTITY_="${OPTARG}";;
    h|*)
        exit 2
        ;;
  esac
done

TS_TARGET=/home/eccd/${_USER_}/
rsync -av -e "ssh -i ${_TS_IDENTITY_} -p ${TS_PORT}" --exclude '__*' --exclude .git --delete-before ${TS_SOURCE} ${TS_USER}@${TS}:${TS_TARGET}
