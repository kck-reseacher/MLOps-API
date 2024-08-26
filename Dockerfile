FROM aiops/mlc:backbone

COPY ./ /root/ai-module/mlops-mlc

WORKDIR /root/ai-module/mlops-mlc
RUN chmod -R 777 ./*
