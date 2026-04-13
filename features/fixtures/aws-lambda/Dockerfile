ARG PYTHON_TEST_VERSION
ARG SAM_CLI_VERSION
FROM python:${PYTHON_TEST_VERSION}

# disable SAM telemetry
ENV SAM_CLI_TELEMETRY=0

# ensure system packages and CA certs are present so pip can reach PyPI,
# then install aws-sam-cli. Allow optional version via build-arg.
RUN apt-get update && apt-get install -y --no-install-recommends \
		ca-certificates curl unzip build-essential && \
		rm -rf /var/lib/apt/lists/* && \
		python -m pip install --upgrade pip && \
		if [ -n "${SAM_CLI_VERSION}" ]; then \
			pip install --no-cache-dir "aws-sam-cli==${SAM_CLI_VERSION}"; \
		else \
			pip install --no-cache-dir aws-sam-cli; \
		fi

COPY temp-bugsnag-python/ /usr/src/bugsnag

WORKDIR /usr/src/app
