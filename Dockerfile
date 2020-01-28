FROM igormaraujo/lpsolve-python3

# Copy project files
COPY ./* /home/$NB_USER/recodis-school/

USER root

# Fix the permission on files and folders
RUN chown -R $NB_USER:$NB_GID /home/$NB_USER

RUN conda install --yes networkx

USER $NB_UID

WORKDIR /home/$NB_USER/recodis-school/
