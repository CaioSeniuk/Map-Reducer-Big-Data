FROM python:3.11-slim-bookworm

ARG HADOOP_VERSION=3.4.1
ARG TARGETARCH

ENV HADOOP_VERSION=${HADOOP_VERSION} \
    HADOOP_HOME=/opt/hadoop \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${TARGETARCH} \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:${PATH}

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl openjdk-17-jre-headless procps \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSLo /tmp/hadoop.tar.gz \
       "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" \
    && curl -fsSLo /tmp/hadoop.tar.gz.sha512 \
       "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz.sha512" \
    && echo "$(awk '{print $4}' /tmp/hadoop.tar.gz.sha512)  /tmp/hadoop.tar.gz" | sha512sum --check - \
    && tar -xzf /tmp/hadoop.tar.gz -C /opt \
    && mv "/opt/hadoop-${HADOOP_VERSION}" "${HADOOP_HOME}" \
    && rm /tmp/hadoop.tar.gz /tmp/hadoop.tar.gz.sha512

WORKDIR /workspace
ENTRYPOINT ["hadoop"]
CMD ["version"]
