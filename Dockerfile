FROM registry.access.redhat.com/ubi8/ubi

ENV APP_HOME="/home/app"

RUN yum module list && \
    yum -y module install python38 && \
    pip3.8 install --upgrade pip


RUN useradd app --user-group --uid 1001 --create-home && \
    mkdir -p $APP_HOME/.local/bin && \
    chown -R app:app $APP_HOME/


USER app

COPY setup $APP_HOME

RUN export PATH=$PATH:$APP_HOME/.local/bin && \
    pip3.8 install --user -r $APP_HOME/requirements.txt && \
    rm -f $APP_HOME/requirements.txt
