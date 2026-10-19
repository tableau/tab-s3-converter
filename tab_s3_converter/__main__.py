# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

import sys

from .cli import run

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
