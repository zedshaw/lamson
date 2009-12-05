import os

author = 'Zed A. Shaw' # Default author name. Overridden in individual document
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
input_dir = os.path.join(THIS_DIR, 'input')
output_dir = os.path.join(THIS_DIR, 'output')
template_dir = THIS_DIR
template = os.path.join(template_dir, 'template.html')

### Optional parameters
options = { 'baseurl':"", # if not set, relative URLs will be generated
            'sitename':"Lamson Project(TM)",
            'slogan': "Lamson The Python SMTP Server and Framework",
            'extensions':['.txt'],
            'format': 'text/x-textile',
            'siteurl': 'http://lamsonproject.org',
          }
