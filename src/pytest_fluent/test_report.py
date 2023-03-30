"""Extract result information."""
# The MIT License (MIT)

# Copyright (c) 2019 Israel Fruchter

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Adopted from https://github.com/fruch/pytest-elk-reporter

import typing

import pytest
import six


class LogReport(object):
    def __init__(self, config):
        self.config = config
        super(LogReport, self).__init__()

    def __call__(self, report: pytest.TestReport):
        """Prepare result report for broadcasting."""
        # pylint: disable=too-many-branches
        results: typing.Dict[typing.Any, typing.Any] = {}

        worker_id = self.get_worker_id()
        # wait until workers are senting back their results.
        # See https://pytest-xdist.readthedocs.io/en/latest/how-it-works.html
        if worker_id not in ["master", "default"]:
            return results
        data = None

        if report.passed:
            if report.when == "call":
                data = self.create_report_with_verdict(
                    report,
                    lambda x: hasattr(x, "wasxfail"),
                    "xpassed",
                    "passed",
                )
        elif report.failed:
            if report.when == "call":
                verdict = "failed"
                if hasattr(report, "longrepr"):
                    import _pytest

                    if isinstance(
                        report.longrepr, _pytest._code.code.ExceptionChainRepr
                    ):
                        verdict = "error"
                data = self.create_report(report, verdict)
            elif report.when == "setup":
                data = self.create_report(report, "error")
        elif report.skipped:
            data = self.create_report_with_verdict(
                report, lambda x: hasattr(x, "wasxfail"), "xfailed", "skipped"
            )

        if data:
            results.update(data)
        return results

    def create_report_with_verdict(
        self,
        report: pytest.TestReport,
        predicate: typing.Callable,
        if_val: str,
        else_val: str,
    ) -> dict:
        if predicate(report):
            return self.create_report(report, if_val)
        else:
            return self.create_report(report, else_val)

    def create_report(
        self,
        item_report: pytest.TestReport,
        verdict: str,
    ):
        """Create test report dataset."""
        test_data = dict(
            item_report.user_properties,
            name=item_report.nodeid,
            outcome=verdict,
            duration=item_report.duration,
            markers=item_report.keywords,
        )
        message = self.get_failure_messge(item_report)
        if message:
            test_data.update(failure_message=message)
        return test_data

    def get_worker_id(self):
        """Extract the worker id"""
        worker_id = "default"
        if hasattr(self.config, "workerinput"):
            worker_id = self.config.workerinput["workerid"]
        if (
            not hasattr(self.config, "workerinput")
            and getattr(self.config.option, "dist", "no") != "no"
        ):
            worker_id = "master"
        return worker_id

    @staticmethod
    def get_failure_messge(item_report):
        """Extract error message."""
        if item_report.passed:
            return ""
        if hasattr(item_report, "longreprtext"):
            message = item_report.longreprtext
        elif hasattr(item_report.longrepr, "reprcrash"):
            message = item_report.longrepr.reprcrash.message
        elif isinstance(item_report.longrepr, six.string_types):
            message = item_report.longrepr
        else:
            message = str(item_report.longrepr)
        return message
