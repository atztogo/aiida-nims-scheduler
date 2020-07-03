[![Build Status](https://github.com/atztogo/aiida-nims-scheduler/workflows/ci/badge.svg?branch=master)](https://github.com/atztogo/aiida-nims-scheduler/actions)
[![Coverage Status](https://coveralls.io/repos/github/atztogo/aiida-nims-scheduler/badge.svg?branch=master)](https://coveralls.io/github/atztogo/aiida-nims-scheduler?branch=master)

# aiida-nims-scheduler

AiiDA plugin of NIMS supercomputer scheduler

## Installation

```shell
git clone https://github.com/atztogo/aiida-nims-scheduler .
cd aiida-nims-scheduler
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
verdi daemon restart
verdi plugin list aiida.schedulers  # should now show pbs_nims scheduler
```

## Usage

Parameters in job_resource are defined at NodeNumberJobResource in
aiida-core as follows:
```
_default_fields = (
    'num_machines',
    'num_mpiprocs_per_machine',
    'num_cores_per_machine',
    'num_cores_per_mpiproc',
)
```

With these parameters, header part of a job script is given by
```
#QSUB2 core {num_machines * num_cores_per_machine}
#QSUB2 mpi {num_machines * num_mpiprocs_per_machine}
#QSUB2 smp {num_cores_per_mpiproc}
```

When `num_cores_per_machine` is unspecified,
`num_mpiprocs_per_machine` is used instead of `num_cores_per_machine`.
`#QSUB2 smp` line becomes blank unless specified `num_cores_per_mpiproc`.

For example, job resources are set by
```
builder.options = Dict(dict={'resources': {'num_machines': '1',
                                           'num_mpiprocs_per_machine': 48},
                             'max_wallclock_seconds': 3600 * 10})
```

## Repository contents

* [`.github/`](.github/): [Github Actions](https://github.com/features/actions) configuration
  * [`ci.yml`](.github/workflows/ci.yml): runs tests, checks test coverage and builds documentation at every new commit
  * [`publish-on-pypi.yml`](.github/workflows/publish-on-pypi.yml): automatically deploy git tags to PyPI - just generate a [PyPI API token](https://pypi.org/help/#apitoken) for your PyPI account and add it to the `pypi_token` secret of your github repository
* [`aiida_nims_scheduler/`](aiida_nims_scheduler/): The main source code of the plugin package
  * [`data/`](aiida_nims_scheduler/data/): A new `DiffParameters` data class, used as input to the `DiffCalculation` `CalcJob` class
  * [`calculations.py`](aiida_nims_scheduler/calculations.py): A new `DiffCalculation` `CalcJob` class
  * [`cli.py`](aiida_nims_scheduler/cli.py): Extensions of the `verdi data` command line interface for the `DiffParameters` class
  * [`helpers.py`](aiida_nims_scheduler/helpers.py): Helpers for setting up an AiiDA code for `diff` automatically
  * [`parsers.py`](aiida_nims_scheduler/parsers.py): A new `Parser` for the `DiffCalculation`
* [`tests/`](tests/): Basic regression tests using the [pytest](https://docs.pytest.org/en/latest/) framework (submitting a calculation, ...). Install `pip install -e .[testing]` and run `pytest`.
* [`.coveragerc`](.coveragerc): Configuration of [coverage.py](https://coverage.readthedocs.io/en/latest) tool reporting which lines of your plugin are covered by tests
* [`.gitignore`](.gitignore): Telling git which files to ignore
* [`.pre-commit-config.yaml`](.pre-commit-config.yaml): Configuration of [pre-commit hooks](https://pre-commit.com/) that sanitize coding style and check for syntax errors. Enable via `pip install -e .[pre-commit] && pre-commit install`
* [`LICENSE`](LICENSE): License for your plugin
* [`MANIFEST.in`](MANIFEST.in): Configure non-Python files to be included for publication on [PyPI](https://pypi.org/)
* [`README.md`](README.md): This file
* [`conftest.py`](conftest.py): Configuration of fixtures for [pytest](https://docs.pytest.org/en/latest/)
* [`pytest.ini`](pytest.ini): Configuration of [pytest](https://docs.pytest.org/en/latest/) test discovery
* [`setup.json`](setup.json): Plugin metadata for registration on [PyPI](https://pypi.org/) and the [AiiDA plugin registry](https://aiidateam.github.io/aiida-registry/) (including entry points)
* [`setup.py`](setup.py): Installation script for pip / [PyPI](https://pypi.org/)

## License

MIT


## Contact

atz.togo@gmail.com
