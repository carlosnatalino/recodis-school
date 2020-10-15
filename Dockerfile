FROM igormaraujo/lpsolve-python3

USER root

RUN conda install --yes networkx

USER $NB_UID

WORKDIR /home/$NB_USER/recodis-school/

# CMD ["./scripts/entrypoint.sh"]
CMD ["jupyter", "lab", "--config", "./conf/jupyter.py"]
