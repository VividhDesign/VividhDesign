FROM ann-benchmarks

RUN apt-get update && apt-get install -y --no-install-recommends cmake g++ git && rm -rf /var/lib/apt/lists/*
RUN pip install numpy
RUN pip install "git+https://github.com/VividhDesign/strata"

RUN python3 -c 'import strata; print(strata.simd_backend())'
