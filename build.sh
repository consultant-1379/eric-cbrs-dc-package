#!/bin/bash

_BASE_="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
_LATEST_DROP_="https://ci-portal.seli.wh.rnd.internal.ericsson.com//api/product/ENM/latestdrop/"
CHART_ERIC_CBRS_DC_APPLICATION="eric-cbrs-dc-package"

HELM=helm
VERBOSE=0

_lint() {
  local _chart_=$1
  pushd ${_BASE_}/chart > /dev/null
  if [[ -s $2 ]] ; then
    _values_="--values $2"
  fi
  _cmd_="${HELM} lint ${_chart_} ${_values_}"
  if [[ ${VERBOSE} -eq 1 ]] ; then
    echo "DEBUG: ${_cmd_}"
  fi
  ${_cmd_} || exit $?
  popd > /dev/null
}

_clean(){
  local _chart_=$1
  echo "Cleaning chart/${_chart_}"
  pushd ${_BASE_} > /dev/null
  rm -rf chart/${_chart_}/charts
  rm -f chart/${_chart_}/Chart.lock
  rm -rf CRDS
  _pkg_="${_chart_}-*.tgz"
  rm -f ${_pkg_}
  popd > /dev/null
}

_helm_dependency(){
  local _chart_=$1
  echo "Updating dependencies for chart/${_chart_}"
  pushd ${_BASE_} > /dev/null
  _cmd_="${HELM} dependency update ${_SKIP_REFRESH_} chart/${_chart_}"
  if [[ ${VERBOSE} -eq 1 ]] ; then
    echo "DEBUG: ${_cmd_}"
  fi
  ${_cmd_} || exit $?
  popd > /dev/null
}

_helm_template(){
  local _chart_=$1
  local _set_=$3
  echo "Templating chart/${_chart_}"
  pushd ${_BASE_} > /dev/null
  if [[ -s $2 ]] ; then
    _values_="--values $2"
  fi
  _cmd_="${HELM} template chart/${_chart_} ${_values_} ${_set_}"
  if [[ ${VERBOSE} -eq 1 ]] ; then
    echo "DEBUG: ${_cmd_}"
  fi
  ${_cmd_} || exit $?
  popd > /dev/null
}

_helm_package() {
  local _chart_=$1
  local _update_=$2
  echo "Creating helm package for chart/${_chart_}"
  if [[ ${_update_} -eq 1 ]] ; then
    _helm_dependency ${_chart_}
  fi
  pushd ${_BASE_} > /dev/null
  find . -name "${_chart_}-*.tgz" -exec rm {} \;

  _drop_=$(wget -q -O - --no-check-certificate ${_LATEST_DROP_} |  jq '.drop' | tr -d '"')
  _prod_date_=$(date +%FT%TZ --utc)

  _values_="chart/${_chart_}/values.yaml"
  cp "${_values_}" "${_values_}.orig"
  sed -i "s/SPRINT_TAG/${_drop_}/g" ${_values_}
  sed -i "s/PRODUCTION_DATE/${_prod_date_}/g" ${_values_}

  _cmd_="${HELM} package --destination ${_BASE_} chart/${_chart_} --debug"
  if [[ ${VERBOSE} -eq 1 ]] ; then
    echo "${_cmd_}"
  fi
  ${_cmd_}
  _rc_=$?
  mv "${_values_}.orig" "${_values_}"
  if [[ ${_rc_} -ne 0 ]] ; then
    exit ${_rc_}
  fi

  _file_=$(find . -maxdepth 1 -name "${_chart_}-*.tgz")
  rm -rf CRDS
  mkdir -p CRDS

  for _crd_ in $(tar tvf ${_file_} | grep eric-crd | awk '{print $6}'); do
      tar xmf "${_file_}" -C CRDS/ "${_crd_}"
      mv "CRDS/${_crd_}" CRDS/
      rm -rf CRDS/$(echo "${_crd_}" | cut -d "/" -f1)
  done
  ls -1 CRDS
  popd > /dev/null
}

usage(){
  echo "$0 <option> [arg]"
  echo -e "\t-C: Chart to build, defaults to ${CHART_ERIC_CBRS_DC_APPLICATION}"
  echo -e "\t-c: Clean any build output artifacts"
  echo -e "\t-d: Update helm dependencies"
  echo -e "\t-p: Build the helm package for this chart"
  echo -e "\t-s: Skip helm repository refresh"
  echo -e "\t-t: helm template"
  echo -e "\t-S: --set value"
  echo -e "\t-l: helm lint"
  echo -e "\t-f: integration values file"
  echo -e "\t-V: verbose"

  exit 2
}

_LINT_=0
_CLEAN_=0
_DEPENDENCIES_=0
_PACKAGE_=0
_TEMPLATE_=0
_SKIP_REFRESH_=
_SET_=()
_VALUES_=NULL
_CHART_=${CHART_ERIC_CBRS_DC_APPLICATION}

if [[ $# -eq 0 ]] ; then
  usage
  exit 2
fi

while getopts "lcdpstf:C:S:V" o; do
  case "${o}" in
    C)
      _CHART_=${OPTARG};;
    l)
      _LINT_=1;;
    c)
      _CLEAN_=1;;
    d)
      _DEPENDENCIES_=1;;
    p)
      _PACKAGE_=1;;
    t)
      _TEMPLATE_=1;;
    f)
      _VALUES_=$( realpath ${OPTARG} );;
    s)
      _SKIP_REFRESH_="--skip-refresh";;
    S)
      _SET_+=("--set ${OPTARG}");;
    V)
      VERBOSE=1;;
    h|*)
        usage;;
  esac
done

if [[ ${_CLEAN_} -eq 1 ]] ; then
  _clean ${_CHART_}
fi

if [[ "${_VALUES_}" != "NULL" ]] && [[ ! -f ${_VALUES_} ]]; then
    echo "File ${_VALUES_} not found!"
    exit 1
  fi

if [[ ${_LINT_} -eq 1 ]] ; then
  _lint ${_CHART_} ${_VALUES_}
fi

if [[ ${_PACKAGE_} -eq 1 ]] ; then
  _helm_package ${_CHART_} ${_DEPENDENCIES_}
elif [[ ${_DEPENDENCIES_} -eq 1 ]] ; then
  _helm_dependency ${_CHART_}
elif [[ ${_TEMPLATE_} -eq 1 ]] ; then
  _set_=""
  if (( ${#_SET_[@]} )) ; then
    _set_="${_SET_[*]}"
  fi
  _helm_template ${_CHART_} ${_VALUES_} "${_set_}"
fi

