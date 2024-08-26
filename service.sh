#!/bin/bash

service ntp start
cd /root/ai-module/mlops-mlc

mlc_log_dir=/root/ai-log/mlc/proc

if [ ! -d $mlc_log_dir ]
then
    mkdir -p $mlc_log_dir
fi

date_format=$(date '+%Y-%m-%d_%H:%M:%S')
mlc_log=${mlc_log_dir}/${date_format}_mlc.log


python setup.py develop

if [ "$1" == "--use-store" ]; then
    echo "Redis 캐싱 사용 옵션이 활성화되었습니다."
    python api/ml_controller/ml_controller.py --use-store >> $mlc_log 2>&1
else
    echo "기본 모드로 실행됩니다."
    python api/ml_controller/ml_controller.py >> $mlc_log 2>&1
fi

tail -f /dev/null

