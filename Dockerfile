FROM igormaraujo/lpsolve-python3

USER root

RUN conda install --yes networkx

USER $NB_UID

WORKDIR /home/$NB_USER/recodis-school/

CP ./conf/jupyter_lab_config.py .

# CMD ["./scripts/entrypoint.sh"]
CMD ["jupyter", "lab", "--config", "jupyter_lab_config.py"]
# CMD ["jupyter", "lab", "--ip", "*", "--allow_origin", "recodis-school.herokuapp.com", "--port", "$PORT", "--allow_root", "True"]
