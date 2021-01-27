FROM tiangolo/uwsgi-nginx:python3.8
RUN pip install torch --no-cache-dir
ENV STATIC URL /static
ENV STATIC_PATH /Users/benjamin/PycharmProjects/APPLE/app/static
COPY ./requirements.txt /Users/benjamin/PycharmProjects/APPLE/requirements.txt
RUN pip install -r /Users/benjamin/PycharmProjects/APPLE/requirements.txt