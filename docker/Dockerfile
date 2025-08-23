FROM continuumio/miniconda3

WORKDIR /app
COPY . /app

RUN conda env create -f environment.yml && conda clean -afy

SHELL ["conda", "run", "-n", "abzu", "/bin/bash", "-c"]
RUN python scripts/bootstrap.py

CMD ["bash"]
