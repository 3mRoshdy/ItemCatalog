Overview :
- Item Catalog Using OAuth2 authentication Project Submission for udacity full stack course.

Dependences:
- Udacity Vagrantfile : https://github.com/udacity/fullstack-nanodegree-vm
- Vagrant : https://www.vagrantup.com/
- VirtualBox : https://www.virtualbox.org/wiki/Downloads

Requirements:
- Installing Vagrant
- Installing Virtual Machine
- Clone udacity vagrant file from github
- Launch Vagrant using "vagrant up"
- Logging in the Virtual machine using "vagrant ssh"
- Navigate through cd/vagrant
- Navigate through Project Submission folder
- Run Database Setup using terminal command "python database_setup.py"
- Run The data samples using terminal command "python lotsofmenus.py"
- Initiate the application using terminal command "python finalproject.py"
- Open the local host on web browser using http://localhost:5000

Accessing JSON Api :
- Catalog : /catalog/JSON
- Catalog Category : /catalog/<int:category_id>/JSON
- Catalog items : /catalog/<catalog_id>/item/JSON
- Certain Catalog item : /catalog/<catalog_id>/item/<item_id>/JSON
