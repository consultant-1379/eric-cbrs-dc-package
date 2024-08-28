import sys
import os
from io import StringIO
from unittest import TestCase, mock
from mock import patch, mock_open
from pathlib import Path

path = Path(os.path.dirname(os.path.abspath(__file__)))
root_folder = os.path.dirname(os.path.dirname(os.path.dirname(path)))
print(root_folder)
os.chdir(root_folder+'/chart/eric-cbrs-dc-package/scripts/k8shealthcheck')
print(os.getcwd())
sys.path.append(str(os.getcwd()))

class Testk8shealthcheck(TestCase):

    def setUp(self):
        self.target = __import__('k8shealthcheck')
        self.logger = __import__('logger')
        self.info_log_prefix = self.logger.BOLD + self.logger.BLUE + self.logger.INFO
        self.warning_log_prefix = self.logger.BOLD + self.logger.YELLOW + \
                                        self.logger.WARNING
        self.error_log_prefix = self.logger.BOLD + self.logger.RED + self.logger.ERROR
        self.print_log_suffix = self.logger.END + self.logger.END
        self.test_k8s_name_space = 'cbrs'

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_line_break_to_print_breakLine(self, mock_out):
        expected_output = '==========================================================================================\n'
        self.target.print_line_break()
        self.assertEqual(mock_out.getvalue(), expected_output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_execute_command_zero_exit_code(self, mock_out):
        command = ['echo', 'header\nrecord1\nrecord2\nrecord3']
        header, records = self.target.execute_command(command)
        self.assertTrue(header == 'header')
        self.assertTrue(len(records) == 3)

    @patch('sys.stdout', new_callable=StringIO)
    def test_execute_command_non_zero_exit_code(self, mock_out):
        command = ['kubectl', 'get', 'test']
        header, records = self.target.execute_command(command)
        self.assertEqual(header, '')
        self.assertListEqual(records, [])

    @patch('sys.stdout', new_callable=StringIO)
    def test_validate_resource_status_all_ready_nodes(self, mock_out):
        header = 'NAME                                      STATUS   ROLES    AGE   VERSION'
        nodes = ['master-0-ccd-c12a008                      Ready    master   35d   v1.17.3',
                 'master-1-ccd-c12a008                      Ready    master   35d   v1.17.3']
        validated_records = self.target.validate_resource_status(header, nodes, 'STATUS', 'Ready')
        self.assertEqual(len(validated_records['good_records']), 2)
        self.assertEqual(len(validated_records['failed_records']), 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_validate_resource_status_no_resources_found(self, mock_out):
        no_resource = 'No resources found in ' + self.test_k8s_name_space + ' namespace.'
        target_ret = 'No resources found in ' + self.test_k8s_name_space + ' namespace.'
        validated_records = self.target.validate_resource_status(no_resource, '', '', '')
        self.assertEqual(len(validated_records['good_records']),0)
        from pprint import pprint
        pprint(validated_records['failed_records'])
        self.assertEqual(len(validated_records['failed_records']),0)


    @patch('sys.stdout', new_callable=StringIO)
    def test_validate_resource_status_nodes_not_ready(self, mock_out):
        header = 'NAME                                      STATUS   ROLES    AGE   VERSION'
        nodes = ['master-0-ccd-c12a008                      NotReady    master   35d   v1.17.3',
                 'master-1-ccd-c12a008                      Ready    master   35d   v1.17.3']
        validated_records = self.target.validate_resource_status(header, nodes, 'STATUS', 'Ready')
        self.assertEqual(len(validated_records['good_records']), 1)
        self.assertEqual(len(validated_records['failed_records']), 1)

    @patch('sys.stdout', new_callable=StringIO)
    def test_validate_resource_status_nodes_empty_header_empty_records(self, mock_out):
        header = ""
        records = []
        validated_records = self.target.validate_resource_status(header, records, 'STATUS', 'Ready')
        self.assertEqual(len(validated_records['good_records']), 0)
        self.assertEqual(len(validated_records['failed_records']), 0)

    @patch('k8shealthcheck.check_service', return_value=0)
    @patch('k8shealthcheck.check_pvc', return_value=0)
    @patch('k8shealthcheck.run_ingress_health_checks', return_value=0)
    @patch('k8shealthcheck.check_jobs', return_value=0)
    @patch('k8shealthcheck.check_pods', return_value=0)
    @patch('k8shealthcheck.check_deployments', return_value=0)
    @patch('k8shealthcheck.check_k8s_nodes', return_value=0)
    @patch('k8shealthcheck.check_statefulsets', return_value=0)
    @patch('k8shealthcheck.get_cronjobs')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_section_args(self,  mock_get_cronjobs, mock_out, mock_check_statefulsets,
                                    mock_check_k8s_nodes,
                                    mock_check_deployments,
                                    mock_check_pods, mock_check_jobs, mock_check_ingress,
                                    mock_check_pvc, mock_check_service):



        args_role_list = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', "statefulsets"])
        self.target.main(args_role_list)
        mock_check_statefulsets.assert_called()

        args_role_ingress = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', 'ingress'])
        self.target.main(args_role_ingress)
        mock_check_ingress.assert_called()

        args_role_jobs = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', 'jobs'])
        self.target.main(args_role_jobs)
        mock_check_jobs.assert_called()

        args_role_pvc = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', 'pvc'])
        self.target.main(args_role_pvc)
        mock_check_pvc.assert_called()

        args_role_deployments = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', 'deployments'])
        self.target.main(args_role_deployments)
        mock_check_deployments.assert_called()

        args_role_pods = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', 'pods'])
        self.target.main(args_role_pods)
        mock_check_pods.assert_called()

        args_role_nodes = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', 'nodes'])
        self.target.main(args_role_nodes)
        mock_check_k8s_nodes.assert_called()

        args_role_service = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', 'service'])
        self.target.main(args_role_service)
        mock_check_service.assert_called()

        # Extract to separate test method
        args_role_list = self.target.get_arguments(['-n', self.test_k8s_name_space, '-r', "deployments", "ingress",
                                                    "jobs", "nodes", "pods", "pvc", "service"])
        self.target.main(args_role_list)
        mock_check_deployments.assert_called()
        mock_check_ingress.assert_called()
        mock_check_jobs.assert_called()
        mock_check_k8s_nodes.assert_called()
        mock_check_pods.assert_called()
        mock_check_pvc.assert_called()
        mock_check_service.assert_called()

    @patch('k8shealthcheck.check_service', return_value=0)
    @patch('k8shealthcheck.check_pvc', return_value=0)
    @patch('k8shealthcheck.check_ingress')
    @patch('k8shealthcheck.check_jobs', return_value=0)
    @patch('k8shealthcheck.check_pods', return_value=0)
    @patch('k8shealthcheck.check_deployments', return_value=0)
    @patch('k8shealthcheck.check_statefulsets', return_value=0)
    @patch('k8shealthcheck.check_k8s_nodes', return_value=0)
    @patch('k8shealthcheck.print_line_break')
    @patch('k8shealthcheck.get_cronjobs')
    def test_main_with_args(self, mock_get_cronjobs, mock_print_line_break, mock_check_k8s_nodes,
                  mock_check_statefulsets, mock_check_deployments,
                  mock_check_pods, mock_check_jobs, mock_check_ingress,
                  mock_check_pvc, mock_check_service):

        args = self.target.get_arguments(['-n', self.test_k8s_name_space, '-v'])

        self.target.main(args)
        self.assertEqual(mock_print_line_break.call_count, 2)
        mock_check_k8s_nodes.assert_called_once()
        mock_check_statefulsets.assert_called_once()
        mock_check_deployments.assert_called_once()
        mock_check_pods.assert_called_once()
        mock_check_jobs.assert_called_once()
        mock_check_ingress.assert_called()
        mock_check_pvc.assert_called_once()
        mock_get_cronjobs.assert_called_once()
        mock_check_service.assert_called_once()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.print_summary')
    @patch('k8shealthcheck.validate_resource_status', return_value = ('',[]))
    @patch('k8shealthcheck.execute_command', return_value = ('yes',[]))
    def test_check_k8s_nodes_methods_invoked(self, mock_execute_command, mock_validate_resource_status,
                                             mock_print_summary, mock_out):
        mock_validate_resource_status.return_value = {'failed_records': []}
        self.target.check_k8s_nodes()
        check_permissions_command = ['kubectl', 'auth', 'can-i' , 'get', 'nodes']
        get_command = ['kubectl', 'get', 'nodes']
        top_command = ['kubectl', 'top', 'nodes', '--use-protocol-buffers']
        mock_execute_command.assert_has_calls([mock.call(check_permissions_command, silent=True),
                                               mock.call(get_command), mock.call(top_command)], any_order=True)
        mock_print_summary.assert_called_once()
        mock_validate_resource_status.assert_called_once()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    def test_check_statefulsets_execute_command_invoked(self, mock_execute_command, mock_out):
        mock_execute_command.return_value = ('NAME              READY   AGE',
                                            ['statefulset-1     1/1     2d',
                                             'statefulset-2     1/1     2d',
                                             'statefulset-3     1/1     2d',
                                             'statefulset-4     0/1     2d',
                                             'statefulset-5     0/1     2d',]
                                             )
        self.target.check_statefulsets(self.test_k8s_name_space, True)
        mock_execute_command.assert_called()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    def test_check_statefulsets_verify_error_message(self, mock_execute_command, mock_out):
        error_message = self.error_log_prefix + 'Health check failed.Detected incorrect status for 2 StatefulSets'\
                        + self.print_log_suffix
        mock_execute_command.return_value = ('NAME              READY   AGE',
                                            ['statefulset-1     1/1     2d',
                                             'statefulset-2     1/1     2d',
                                             'statefulset-3     1/1     2d',
                                             'statefulset-4     0/1     2d',
                                             'statefulset-5     0/1     2d',]
                                             )
        self.target.check_statefulsets(self.test_k8s_name_space, True)
        mock_execute_command.assert_called()
        self.assertIn(error_message, mock_out.getvalue().strip())


    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    def test_check_deployments_execute_command_invoked(self, mock_execute_command, mock_out):
        mock_execute_command.return_value = ('NAME              READY   AGE',
                                            ['deployment-1      2/2     2d',
                                             'deployment-2      2/2     2d',
                                             'deployment-3      2/2     2d',
                                             'deployment-4      2/2     2d',
                                             'deployment-5      2/2     2d',]
                                             )
        self.target.check_deployments(self.test_k8s_name_space)
        mock_execute_command.assert_called_once()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    def test_check_pods_with_error_and_warning_observed(self, mock_execute_command, mock_out):
        error_message = self.error_log_prefix + 'Health check failed. Detected incorrect status for 5 Pods'\
                        + self.print_log_suffix
        warning_message = self.warning_log_prefix + 'Detected restarts of 2 Pods' + self.print_log_suffix
        mock_execute_command.return_value = ('NAME      READY   STATUS             RESTARTS   AGE',
                                            ['Pod-1     2/2     Running            0          2d',
                                             'Pod-2     2/2     Running            22         2d',
                                             'Pod-3     1/1     Pending            0          2d',
                                             'Pod-4     2/2     Pending            0          2d',
                                             'Pod-5     0/2     Pending            0          2d',
                                             'Pod-6     0/2     Terminating        0          2d',
                                             'Pod-7     2/2     CrashLoopBackOff   11         2d']
                                             )
        self.target.check_pods(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'pods', '-n', self.test_k8s_name_space]
        top_command = ['kubectl', 'top', 'pods', '-n', self.test_k8s_name_space, '--use-protocol-buffers']
        mock_execute_command.assert_has_calls([mock.call(get_command), mock.call(top_command)], any_order=True)
        self.assertIn(error_message, mock_out.getvalue().strip())
        self.assertIn(warning_message, mock_out.getvalue().strip())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    def test_check_pods_all_running_restarts_observed(self, mock_execute_command, mock_out):
        warning_message = self.warning_log_prefix + 'Detected restarts of 2 Pods' + self.print_log_suffix
        mock_execute_command.return_value = ('NAME      READY   STATUS             RESTARTS   AGE',
                                            ['Pod-1     2/2     Running            0          2d',
                                             'Pod-2     2/2     Running            1          2d',
                                             'Pod-3     1/1     Running            23         2d']
                                             )
        self.target.check_pods(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'pods', '-n', self.test_k8s_name_space]
        top_command = ['kubectl', 'top', 'pods', '-n', self.test_k8s_name_space, '--use-protocol-buffers']
        mock_execute_command.assert_has_calls([mock.call(get_command), mock.call(top_command)], any_order=True)
        self.assertIn(warning_message, mock_out.getvalue().strip())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    def test_check_pods_all_running_no_restarts_observed(self, mock_execute_command, mock_out):
        warning_message = self.info_log_prefix + 'Health check OK. All Pods are in correct state'\
                          + self.print_log_suffix
        mock_execute_command.return_value = ('NAME      READY   STATUS             RESTARTS   AGE',
                                             ['Pod-1     2/2     Running            0          2d',
                                              'Pod-2     2/2     Running            0          2d',
                                              'Pod-3     1/1     Running            0         2d']
                                             )
        self.target.check_pods(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'pods', '-n', self.test_k8s_name_space]
        top_command = ['kubectl', 'top', 'pods', '-n', self.test_k8s_name_space, '--use-protocol-buffers']
        mock_execute_command.assert_has_calls([mock.call(get_command), mock.call(top_command)], any_order=True)
        self.assertIn(warning_message, mock_out.getvalue().strip())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    def test_run_user_selected_health_checks_check_selected_resource_and_pods(self, mock_execute_command, mock_out):
        warning_message = self.info_log_prefix + 'Health check OK. All Pods are in correct state'\
                          + self.print_log_suffix
        mock_execute_command.return_value = ('NAME      READY   STATUS             RESTARTS   AGE',
                                            ['Pod-1     2/2     Running            0          2d',
                                             'Pod-2     2/2     Running            0          2d',
                                             'Pod-3     1/1     Running            0         2d']
                                             )
        self.target.check_pods(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'pods', '-n', self.test_k8s_name_space]
        top_command = ['kubectl', 'top', 'pods', '-n', self.test_k8s_name_space, '--use-protocol-buffers']
        mock_execute_command.assert_has_calls([mock.call(get_command), mock.call(top_command)], any_order=True)
        self.assertIn(warning_message, mock_out.getvalue().strip())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command', return_value = ('',[]))
    @patch('k8shealthcheck.validate_resource_status', return_value ={'failed_records': []})
    @patch('k8shealthcheck.print_summary')
    def test_check_jobs_methods_invoked(self, mock_execute_command, mock_validate_resource_status, mock_print_summary,
                                        mock_out):
        self.target.check_jobs(self.test_k8s_name_space)
        mock_execute_command.assert_called_once()
        mock_validate_resource_status.assert_called_once()
        mock_print_summary.assert_called_once()

    @patch('k8shealthcheck.show_ingress')
    @patch('k8shealthcheck.print_line_break')
    @patch('sys.stdout', new_callable=StringIO)
    def test_check_ingress_show_ingress_invoked(self, mock_out, mock_print_line_break, mock_show_ingress):
        expected_output1 = self.info_log_prefix + 'Getting CBRS ingress...' + self.print_log_suffix
        self.target.check_ingress(self.test_k8s_name_space, True)
        mock_show_ingress.assert_called_once_with(self.test_k8s_name_space, True)
        self.assertIn(expected_output1, mock_out.getvalue().strip())

    @patch('k8shealthcheck.execute_command')
    @patch('sys.stdout', new_callable=StringIO)
    def test_check_service_invoked(self, mock_out, mock_execute_command):
        header ='NAME                                                  TYPE           CLUSTER-IP       EXTERNAL-IP'
        service = ['cbrs-ingress-controller-nx                            ClusterIP      10.107.254.143   <none>']
        mock_execute_command.return_value = (header, service)
        self.target.check_service(self.test_k8s_name_space, True)
        mock_execute_command.assert_called_once()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command', return_value = ('',[]))
    @patch('k8shealthcheck.print_summary')
    def test_check_pvc_methods_invoked(self, mock_execute_command, mock_print_summary, mock_out):
        command = ['kubectl', 'get', 'pvc', '-n', self.test_k8s_name_space]
        mock_execute_command.return_value = command, []
        self.target.check_pvc(self.test_k8s_name_space, True)
        mock_execute_command.assert_called_once()
        mock_print_summary.assert_called_once()

    @patch('sys.stdout', new_callable=StringIO)
    def test_validate_resource_status_all_bound_pvc(self, mock_out):
        header = 'NAME                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE'
        pvc = ['amos                  Bound    pvc-cba2c749-8845-49b7-90a7-120eaf959868   5Gi        RWX            nfs-CBRS92       2d17h',
               'autoprovisioning      Bound    pvc-006a6d96-0cae-42f2-a944-87ba52f6d8f0   5Gi        RWX            nfs-CBRS92       2d17h']
        validated_records = self.target.validate_resource_status(header, pvc, 'STATUS', 'Bound')
        self.assertEqual(len(validated_records['good_records']), 2)
        self.assertEqual(len(validated_records['failed_records']), 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_validate_resource_status_pvc_not_bound(self, mock_out):
        header = 'NAME                STATUS        VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE'
        pvc = ['amos                  Terminating   pvc-cba2c749-8845-49b7-90a7-120eaf959868   5Gi        RWX            nfs-CBRS92       2d17h',
               'autoprovisioning      Bound         pvc-006a6d96-0cae-42f2-a944-87ba52f6d8f0   5Gi        RWX            nfs-CBRS92       2d17h']
        validated_records = self.target.validate_resource_status(header, pvc, 'STATUS', 'Bound')
        self.assertEqual(len(validated_records['good_records']), 1)
        self.assertEqual(len(validated_records['failed_records']), 1)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command', return_value = ('',[]))
    @patch('k8shealthcheck.print_summary')
    def test_run_ingress_health_checks_methods_called(self, mock_execute_command, mock_print_summary,
                                                                  mock_out):
        self.target.run_ingress_health_checks(self.test_k8s_name_space, True)
        self.assertEqual(mock_execute_command.call_count, 1)
        self.assertEqual(mock_print_summary.call_count, 1)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    @patch('k8shealthcheck.cronjobs', ['Cron-Pod'])
    def test_check_pods_no_error_for_cronjob(self, mock_execute_command, mock_out):
        error_message = self.error_log_prefix + 'Health check failed. Detected incorrect status for 2 Pods'\
                        + self.print_log_suffix
        warning_message = self.warning_log_prefix + 'Detected restarts of 1 Pods' + self.print_log_suffix
        mock_execute_command.return_value = ('NAME        READY   STATUS             RESTARTS   AGE',
                                            ['Pod-1       2/2     Running            1          2d',
                                             'Pod-2       0/2     CrashLoopBackOff   0          2d',
                                             'Pod-2       0/2     ContainerCreating  0          2d',
                                             'Cron-Pod-X  0/2     ContainerCreating  0          2d']
                                             )
        self.target.check_pods(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'pods', '-n', self.test_k8s_name_space]
        top_command = ['kubectl', 'top', 'pods', '-n', self.test_k8s_name_space, '--use-protocol-buffers']
        mock_execute_command.assert_has_calls([mock.call(get_command), mock.call(top_command)], any_order=True)
        self.assertIn(error_message, mock_out.getvalue().strip())
        self.assertIn(warning_message, mock_out.getvalue().strip())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    @patch('k8shealthcheck.cronjobs', ['Cron-Pod'])
    def test_check_pods_has_error_for_cronjob(self, mock_execute_command, mock_out):
        error_message = self.error_log_prefix + 'Health check failed. Detected incorrect status for 3 Pods'\
                        + self.print_log_suffix
        warning_message = self.warning_log_prefix + 'Detected restarts of 1 Pods' + self.print_log_suffix
        mock_execute_command.return_value = ('NAME        READY   STATUS             RESTARTS   AGE',
                                             ['Pod-1       2/2     Running            1          2d',
                                              'Pod-2       0/2     CrashLoopBackOff   0          2d',
                                              'Pod-2       0/2     ContainerCreating  0          2d',
                                              'Cron-Pod-X  0/2     OOMKilled          0          2d']
                                             )
        self.target.check_pods(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'pods', '-n', self.test_k8s_name_space]
        top_command = ['kubectl', 'top', 'pods', '-n', self.test_k8s_name_space, '--use-protocol-buffers']
        mock_execute_command.assert_has_calls([mock.call(get_command), mock.call(top_command)], any_order=True)
        self.assertIn(error_message, mock_out.getvalue().strip())
        self.assertIn(warning_message, mock_out.getvalue().strip())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('k8shealthcheck.execute_command')
    @patch('k8shealthcheck.cronjobs', ['Cron-Job'])
    def test_check_jobs_warning_for_cronjob(self, mock_execute_command, mock_out):
        error_message = self.error_log_prefix + 'Health check failed.Detected incorrect status for 1 Jobs'\
                        + self.print_log_suffix
        warning_message = self.info_log_prefix + 'Detected 1 Active CronJobs' + self.print_log_suffix
        mock_execute_command.return_value = ('NAME        COMPLETIONS   DURATION  AGE',
                                            ['Job-1       1/1           12s       2d',
                                             'Job-2       1/1           12s       2d',
                                             'Job-2       0/1           12s       2d',
                                             'Cron-Job-X  0/1           12s       2d']
                                             )
        self.target.check_jobs(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'jobs', '-n', self.test_k8s_name_space]
        mock_execute_command.assert_has_calls([mock.call(get_command)], any_order=True)
        self.assertIn(error_message, mock_out.getvalue().strip())
        self.assertIn(warning_message, mock_out.getvalue().strip())

    @patch('k8shealthcheck.execute_command')
    def test_get_cronjobs(self, mock_execute_command):
        mock_execute_command.return_value = ('NAME        SCHEDULE      SUSPEND  ACTIVE  LAST SCHEDULE  AGE',
                                            ['Cron-Job-1  */1 * * * *   False    0       8m53s          22h',
                                             'Cron-Job-2  */1 * * * *   False    0       1m22s          22h'])
        self.target.get_cronjobs(self.test_k8s_name_space)
        get_command = ['kubectl', 'get', 'cronjobs', '-n', self.test_k8s_name_space]
        mock_execute_command.assert_has_calls([mock.call(get_command)], any_order=True)
        self.assertEqual(self.target.cronjobs, ['Cron-Job-1', 'Cron-Job-2'])
