import sys

import boto3

if sys.argv[1:] == ["--version"]:
    print("mi-cli 1.0 · boto3 cargado:", "boto3" in sys.modules)
    sys.exit(0)

print(boto3.__version__)
