import os

c = get_config()

c.IPKernelApp.pylab = 'inline'  # if you want plotting support always in your notebook
# Notebook config
c.NotebookApp.notebook_dir = ''
c.NotebookApp.allow_origin = u'recodis-school.herokuapp.com' # put your public IP Address here
c.NotebookApp.ip = '*'
c.NotebookApp.allow_remote_access = True
c.NotebookApp.open_browser = False
# ipython -c "from notebook.auth import passwd; passwd()"
c.NotebookApp.password = u'argon2:$argon2id$v=19$m=10240,t=10,p=8$3oqzKxtq9jybE5iWGMFu7Q$feXLs6Nlr4s8fMFOiqMQAQ'
c.NotebookApp.port = int(os.environ.get("PORT", 8888))
c.NotebookApp.open_browser = False
c.NotebookApp.allow_root = True
c.NotebookApp.allow_password_change = True
c.ConfigurableHTTPProxy.command = ['configurable-http-proxy', '--redirect-port', '80']
