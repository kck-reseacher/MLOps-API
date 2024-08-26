#!/bin/bash

#aiops 계정인지 확인(root 계정 실행 차단)
if [ $(whoami) != "aiops" ]; then
        echo '실행이 허용되지 않는 계정입니다.'
        echo '계정 변경 후 다시 시도하세요.'
        exit
fi

source ~/.bash_profile

input=$1
actor=""
if [ -z "$2" ]; then
  actor="aiops"
else
  actor="$2"
fi

module_dir=$AIMODULE_PATH

command_list=('partial_start' 'partial_stop' 'partial_restart' 'all_start' 'all_stop' 'all_restart' 'status' 'exit' 'log')
log_options=('mlc' 'mls' 'srs' 'nginx' 'redisai')

function partial_start() {
    cd $module_dir
    docker-compose -f docker-compose-partial.yml up -d
}

function partial_stop() {
    cd $module_dir
    docker-compose -f docker-compose-partial.yml stop mlc mls srs
    docker-compose -f docker-compose-partial.yml rm mlc mls srs --force
}

function partial_restart() {
    partial_stop
    sleep 3
    partial_start
}

function all_start() {
    cd $module_dir
    docker-compose -f docker-compose-all.yml up -d
}

function all_stop() {
    cd $module_dir
    docker-compose -f docker-compose-all.yml stop
    docker-compose -f docker-compose-all.yml rm --force
}

function all_restart() {
    all_stop
    sleep 3
    all_start
}

function status() {
    docker ps
}

function exit() {
    exit 0
}

function mlc_log() {
    docker logs -n 100 -f mlc
}

function mls_log() {
    docker logs -n 100 -f mls
}

function srs_log() {
    docker logs -n 100 -f srs
}

function nginx_log() {
    docker logs -n 100 -f nginx
}

function redisai_log() {
    docker logs -n 100 -f redisai
}

while :
do
        echo '-----------------------------------------------------------'
        #명령어를 입력하지 않는 경우 선택지 기능 실행
        if [ -z ${input} ]; then
                echo "${command_list[@]} 중 하나를 선택하세요."
                PS3=">>> "

                select command in ${command_list[@]}
                do
                        input=${command}
                        break
                done
        fi

        #잘못된 명령어인지 확인
        if ! printf '%s\0' "${command_list[@]}" | grep -Fxqz -- "${input}"; then
                echo '지원하지 않는 명령어입니다.'
                input=''
                continue
        fi

        #명령어 실행
        cd $exe_dir
        echo "${input} 명령을 실행합니다."

        case $input in
                partial_start)
                        partial_start
                        break
                        ;;
                partial_stop)
                        partial_stop
                        break
                        ;;
                partial_restart)
                        partial_restart
                        break
                        ;;
                all_start)
                        all_start
                        break
                        ;;
                all_stop)
                        all_stop
                        break
                        ;;
                all_restart)
                        all_restart
                        break
                        ;;
                status)
                        status
                        break
                        ;;
                exit)
                        exit
                        break
                        ;;
                log)
                        while :
                        do
                            echo "${log_options[@]} 중 로그를 확인할 서비스를 선택하세요."
                            PS3=">>> "

                            select service in "${log_options[@]}"
                            do
                                case $service in
                                        mlc)
                                                mlc_log
                                                ;;
                                        mls)
                                                mls_log
                                                ;;
                                        srs)
                                                srs_log
                                                ;;
                                        nginx)
                                                nginx_log
                                                ;;
                                        redisai)
                                                redisai_log
                                                ;;
                                        *)
                                                echo "$service 는 지원하지 않는 서비스입니다."
                                                ;;
                                esac
                                break
                            done
                        done
                        ;;
        esac
        input=''
done

echo '-----------------------------------------------------------'