FROM igormaraujo/lpsolve-python3

USER root

# conda update -n base conda
RUN conda install --yes networkx \
	&& mkdir -p /home/$NB_USER/recodis-school/models \
	&& mkdir -p /home/$NB_USER/recodis-school/results \
	&& chown -R $NB_USER /home/$NB_USER/recodis-school/

USER $NB_UID

WORKDIR /home/$NB_USER/recodis-school/

COPY topologies ./topologies/
COPY figures ./figures/
COPY ["cdn_functions.py", "cross_solver.py", "reader.py", "aca.ipynb", "clsd.ipynb", "explore-topologies.ipynb", "rpp-clsd.ipynb", "./"]
COPY ./conf/jupyter_lab_config.py /home/$NB_USER/jupyter_lab_config.py

# CMD ["./scripts/entrypoint.sh"]
CMD ["jupyter", "lab", "--config", "/home/$NB_USER/jupyter_lab_config.py"]
# CMD ["jupyter", "lab", "--ip", "*", "--allow_origin", "recodis-school.herokuapp.com", "--port", "$PORT", "--allow_root", "True"]
