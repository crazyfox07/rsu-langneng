FROM ubuntu
WORKDIR /home/pkg
ADD ./pkg/pycryptodome-3.9.9-cp38-cp38-manylinux2014_aarch64.whl .
RUN apt update && \
    apt install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt install -y python3.8 && \
    apt install -y python3-pip && \
    apt install -y vim && \
    pip3 install fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install func_timeout -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install SQLAlchemy -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install pymysql -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install apscheduler -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install pyyaml -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install /home/pkg/pycryptodome-3.9.9-cp38-cp38-manylinux2014_aarch64.whl