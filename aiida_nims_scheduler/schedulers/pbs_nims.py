# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import logging
from aiida.common.escaping import escape_for_bash
from aiida.schedulers.plugins.pbsbaseclasses import PbsBaseClass
from aiida.schedulers import SchedulerError

_LOGGER = logging.getLogger(__name__)


class PbsNimsScheduler(PbsBaseClass):
    """

    Written based on aiida-cx1scheduler

    """

    def _get_submit_script_header(self, job_tmpl):
        """

        Parameters in job_resource are defined at NodeNumberJobResource in
        aiida-core as follows:

            _default_fields = (
                'num_machines',
                'num_mpiprocs_per_machine',
                'num_cores_per_machine',
                'num_cores_per_mpiproc',
            )

        With these parameters, the header part is given by

        #QSUB2 core {num_machines * num_cores_per_machine}
        #QSUB2 mpi {num_machines * num_mpiprocs_per_machine}
        #QSUB2 smp {num_cores_per_mpiproc}

        When 'num_cores_per_machine' is unspecified, 'num_mpiprocs_per_machine'
        is used instead of 'num_cores_per_machine'.

        Be sure 'tot_num_mpiprocs' can be used to specify
        'num_mpiprocs_per_machine' indirectly as
            num_mpiprocs_per_machine = tot_num_mpiprocs // num_machines

        """

        import re
        import string

        empty_line = ''

        lines = []
        if job_tmpl.queue_name:
            lines.append('#QSUB2 queue {}'.format(job_tmpl.queue_name))

        resource_lines = self._get_resource_lines(
            num_machines=job_tmpl.job_resource.num_machines,
            num_mpiprocs_per_machine=job_tmpl.job_resource.num_mpiprocs_per_machine,
            num_cores_per_machine=job_tmpl.job_resource.num_cores_per_machine,
            num_cores_per_mpiproc=job_tmpl.job_resource.num_cores_per_mpiproc,
            max_wallclock_seconds=job_tmpl.max_wallclock_seconds
        )
        lines += resource_lines

        if job_tmpl.job_name:
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.job_name)
            if not job_title or (job_title[0] not in
                                 string.ascii_letters + string.digits):
                job_title = 'j' + job_title
            job_title = job_title[:15]
            lines.append('#PBS -N {}'.format(job_title))

        if job_tmpl.sched_join_files:
            lines.append('#PBS -j oe')
            if job_tmpl.sched_error_path:
                _LOGGER.info(
                    'sched_join_files is True, but sched_error_path is set in '
                    'PBSPro script; ignoring sched_error_path')

        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)

        if job_tmpl.job_environment:
            lines.append(empty_line)
            lines.append('# ENVIRONMENT VARIABLES BEGIN ###')
            if not isinstance(job_tmpl.job_environment, dict):
                raise ValueError(
                    'If you provide job_environment, it must be a dictionary')
            for key, value in job_tmpl.job_environment.items():
                lines.append('export {}={}'.format(
                    key.strip(), escape_for_bash(value)))
            lines.append('# ENVIRONMENT VARIABLES  END  ###')
            lines.append(empty_line)

        lines.append("cd $PBS_O_WORKDIR")
        lines.append(empty_line)

        return '\n'.join(lines)

    def _get_submit_command(self, submit_script):
        submit_command = 'qsub2 {}'.format(submit_script)

        _LOGGER.info('submitting with: {}'.format(submit_command))

        return submit_command

    def _get_resource_lines(self,
                            num_machines,
                            num_mpiprocs_per_machine,
                            num_cores_per_machine,
                            num_cores_per_mpiproc,
                            max_wallclock_seconds):
        return_lines = []

        # #QSUB2 core
        if num_cores_per_machine is None:
            qsub2_core = num_machines * num_mpiprocs_per_machine
        elif num_cores_per_machine < 1:
            raise ValueError("num_cores_per_machine is not defined.")
        else:
            qsub2_core = num_machines * num_cores_per_machine
        return_lines.append('#QSUB2 core {}'.format(qsub2_core))

        # #QSUB2 mpi
        qsub2_mpi = num_machines * num_mpiprocs_per_machine
        return_lines.append("#QSUB2 mpi {}".format(qsub2_mpi))

        # #QSUB2 smp
        if num_cores_per_mpiproc is not None:
            if num_cores_per_mpiproc > 0:
                qsub2_smp = num_cores_per_mpiproc
                return_lines.append('#QSUB2 smp {}'.format(qsub2_smp))
            else:
                raise ValueError("num_cores_per_mpiproc is wrongly set.")
        else:
            return_lines.append('#QSUB2 smp 1')

        if max_wallclock_seconds is not None:
            try:
                tot_secs = int(max_wallclock_seconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError('max_wallclock_seconds must be '
                                 'a positive integer (in seconds)! '
                                 "It is instead '{}'"
                                 ''.format(max_wallclock_seconds))
            hours = tot_secs // 3600
            tot_minutes = tot_secs % 3600
            minutes = tot_minutes // 60
            seconds = tot_minutes % 60
            return_lines.append(
                '#QSUB2 wtime {:02d}:{:02d}:{:02d}'.format(
                    hours, minutes, seconds))

        return return_lines

    def _parse_submit_output(self, retval, stdout, stderr):
        if retval != 0:
            _LOGGER.error(
                'Error in _parse_submit_output: retval={}; '
                'stdout={}; stderr={}'.format(retval, stdout, stderr)
            )
            raise SchedulerError(
                'Error during submission, retval={}\n'
                'stdout={}\nstderr={}'.format(retval, stdout, stderr)
            )

        if stderr.strip():
            _LOGGER.warning('in _parse_submit_output there was some text in stderr: {}'.format(stderr))

        # return stdout.strip().splitlines()[-1].split('.')[0]
        return stdout.strip().splitlines()[-1]

    def _parse_joblist_output(self, retval, stdout, stderr):
        # _LOGGER.warning("--- PbsNimsScheduler ---")
        # _LOGGER.warning(stdout)
        # _LOGGER.warning("--- PbsNimsScheduler ---")
        return super(PbsNimsScheduler, self)._parse_joblist_output(retval, stdout, stderr)
