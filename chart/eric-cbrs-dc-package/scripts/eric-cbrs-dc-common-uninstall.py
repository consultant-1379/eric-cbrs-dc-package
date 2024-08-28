#!/usr/bin/env python3
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from http.client import NOT_FOUND
from json import loads
from typing import List
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SERVICE_HOST_ENV_NAME = 'KUBERNETES_SERVICE_HOST'
SERVICE_PORT_ENV_PORT = 'KUBERNETES_SERVICE_PORT'
SA_DIR = '/var/run/secrets/kubernetes.io/serviceaccount'
SERVICE_TOKEN_FILENAME = f'{SA_DIR}/token'
SERVICE_CERT_FILENAME = f'{SA_DIR}/ca.crt'
NAMESPACE_FILENAME = f'{SA_DIR}/namespace'


class KubernetesAPI:
    """
    Simple class to access the kuberneted REST API
    See https://kubernetes.io/docs/reference/kubernetes-api/
    """

    def __init__(self) -> None:
        super().__init__()
        self.__debug = True
        with open(NAMESPACE_FILENAME) as _r:
            self.__namespace = _r.readline()
        self.__host = os.environ[SERVICE_HOST_ENV_NAME]
        self.__port = os.environ[SERVICE_PORT_ENV_PORT]
        with open(SERVICE_TOKEN_FILENAME) as _r:
            self.__authorization = f'Bearer {_r.read()}'
        self.__headers = {
            'Accept': 'application/json',
            'User-Agent': 'OpenAPI-Generator/18.20.0/python',
            'authorization': self.__authorization
        }

    def debug(self, message):
        if self.__debug:
            print(message)

    def api_internalcertificates(self):
        """
        Kubernetes internalcertificates API endpoint
        """
        return f'apis/siptls.sec.ericsson.com/v1/namespaces/' \
               f'{self.__namespace}/internalcertificates'

    def api_persistentvolumeclaims(self, name=''):
        """
        Kubernetes persistentvolumeclaim API endpoint
        """
        return f'api/v1/namespaces/' \
               f'{self.__namespace}/persistentvolumeclaims/{name}'

    def api_rolebindings(self):
        """
        Kubernetes rolebinding API endpoint
        """
        return f'apis/rbac.authorization.k8s.io/v1/namespaces/' \
               f'{self.__namespace}/rolebindings'

    def api_roles(self):
        """
        Kubernetes role API endpoint
        """
        return f'apis/rbac.authorization.k8s.io/v1/namespaces/' \
               f'{self.__namespace}/roles'

    def api_serviceaccounts(self):
        """
        Kubernetes serviceaccount API endpoint
        """
        return f'api/v1/namespaces/{self.__namespace}/serviceaccounts'

    def api_configmaps(self):
        """
        Kubernetes configmaps API endpoint
        """
        return f'api/v1/namespaces/{self.__namespace}/configmaps'

    def api_secrets(self):
        """
        Kubernetes secrets API endpoint
        """
        return f'api/v1/namespaces/{self.__namespace}/secrets'

    def _request(self, q_path: str, method: str, selector: str = None) -> str:
        """
        Execute a REST request
        :param q_path: The REST point to call
        :param method: HTTP method
        :param selector: Kubernetes item selector
        :returns: List of found items
        """
        params = {}
        if selector:
            params['labelSelector'] = selector
        q_url = f'https://{self.__host}:{self.__port}/{q_path}'
        if params:
            q_params = urlencode(params)
            q_url = f'{q_url}?{q_params}'
        self.debug(f'{method}: {q_url} -->')
        _request = Request(q_url, method=method, headers=self.__headers)
        try:
            response = urlopen(_request, cafile=SERVICE_CERT_FILENAME)
            self.debug(f'{method}: {q_url} <-- ({response.getcode()})')
            return response.read()
        except HTTPError as error:
            self.debug(f'{method}: {q_url} <-- ({error.code})')

    def _get_resources(self, query_path: str, selector: str = None) -> list:
        """
        Get a list of resources
        :param query_path:
        :param selector:
        :return:
        """
        _data = self._request(query_path, method='GET', selector=selector)
        _json = loads(_data)
        return _json['items']

    def _delete_resource(self, path: str):
        """
        Delete a resource
        :param path:
        :return:
        """
        try:
            self._request(path, method='DELETE')
        except HTTPError as error:
            if error.code != NOT_FOUND:
                raise error

    def delete_resources(self, api, excluded=None):
        """
        Delete a set of resources in a namespace.

        :param api: resource kind API url
        :param excluded: Names of resources to exclude.
        """
        if not excluded:
            excluded = []
        print(f'Delete resource exclude: "{excluded}"')
        resources = self._get_resources(api)
        for resource in resources:
            _name = resource['metadata']['name']
            if _name not in excluded:
                _url = f'{api}/{_name}'
                self._delete_resource(_url)

    def persistentvolumeclaims(self, selector: str = None) -> list:
        """
        Get a list of PVC, optionally based on a label selector.
        :param selector: The selector key=value
        :returns: List of PVCs
        """
        return self._get_resources(self.api_persistentvolumeclaims(), selector)

    def delete_persistentvolumeclaims(self, release_name: str):
        """
        Delete all PVCs belonging to a helm release
        :param release_name: The helm release name e.g. eric-cbrs-dc-common
        """
        all_pvcs = self.persistentvolumeclaims(
            selector=f'app.kubernetes.io/instance={release_name}')
        all_pvcs.extend(
            self.persistentvolumeclaims(selector=f'release={release_name}')
        )
        for pvc in all_pvcs:
            _name = pvc['metadata']['name']
            print(f'Deleting PVC {_name}')
            if _name == 'backup-data-eric-ctrl-bro-0':
                pass
            else :
                self._delete_resource(self.api_persistentvolumeclaims(_name))

    def delete_internalcertificates(self):
        """
        Delete all internalcertificate in a namespace
        """
        self.delete_resources(self.api_internalcertificates())

    def delete_rolebindings(self, excluded):
        """
        Delete all rolebindings in a namespace
        """
        self.delete_resources(self.api_rolebindings(), excluded=excluded)

    def delete_serviceaccounts(self, excluded):
        """
        Delete all serviceaccounts in a namespace
        """
        self.delete_resources(self.api_serviceaccounts(), excluded=excluded)

    def delete_roles(self, excluded):
        """
        Delete all roles in a namespace
        """
        self.delete_resources(self.api_roles(), excluded=excluded)

    def delete_configmaps(self, excluded):
        """
        Delete all configmaps in a namespace
        """
        self.delete_resources(self.api_configmaps(), excluded=excluded)

    def delete_secrets(self):
        """
        Delete all Opaque secrets in a namespace
        """
        print(f'Deleting secrets')
        for secret in self._get_resources(self.api_secrets()):
            _name = secret['metadata']['name']
            _type = secret['type']
            # Deleting 200+ secrets here, see improvement TORF-614389 to addresss
            if 'Opaque' == _type or 'kubernetes.io/tls' == _type:
                print(f'Deleting secret: "{_name}" with type "{_type}"')
                self._delete_resource(f'{self.api_secrets()}/{_name}')
            else:
                print(f'NOT deleting secret: "{_name}" with type "{_type}"')

def get_parsed_args(args: List[str], arg_parser: ArgumentParser) -> Namespace:
    if len(args) == 0:
        print(arg_parser.format_help())
        raise SystemExit(2)
    return arg_parser.parse_args(args)

def main(sys_args):
    arg_parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    arg_parser.add_argument('-r', dest='release', required=True,
                            metavar='release', help='Helm release name.')
    arg_parser.add_argument('-s', dest='skip', required=True,
                            metavar='skip', help='Skip this.')
    arg_parser.add_argument('--keep-roles', action='store_false', dest='keep_roles', required=False,
                            help='Turn on/off RBAC roles and rolebindings')
    args = get_parsed_args(sys_args, arg_parser)
    kube = KubernetesAPI()

    _skip = args.skip.strip()
    _release = args.release.strip()

    print(f'Deleting PVCs for release "{_release}"')
    print(f'Skipping anything named "{_skip}"')

    kube.delete_persistentvolumeclaims(_release)
    kube.delete_internalcertificates()
    if args.keep_roles:
        print('Deleting RBAC roles and rolebindings')
        kube.delete_rolebindings([_skip])
        kube.delete_roles([_skip])
    kube.delete_serviceaccounts(['default', _skip])
    kube.delete_configmaps(['kube-root-ca.crt', _skip])
    kube.delete_secrets()


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:])
