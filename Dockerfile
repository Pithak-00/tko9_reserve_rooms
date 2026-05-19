FROM registry.access.redhat.com/ubi10/python-312-minimal

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

USER root
WORKDIR /workspace

RUN microdnf install -y \
        openssh-server \
        shadow-utils \
        sudo \
        git \
        which \
        findutils \
        procps-ng \
        hostname \
        tar \
    && microdnf clean all

RUN mkdir -p /var/run/sshd /home/vscode/.ssh /workspace

RUN useradd -m -s /bin/bash vscode \
    && echo "vscode:vscode" | chpasswd \
    && usermod -aG wheel vscode \
    && echo "%wheel ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    echo "AllowUsers vscode" >> /etc/ssh/sshd_config

RUN ssh-keygen -A

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r /tmp/requirements.txt
COPY . /workspace
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN chown -R vscode:vscode /workspace /home/vscode && \
    chmod 700 /home/vscode/.ssh

EXPOSE 22 8000

CMD ["/entrypoint.sh"]
