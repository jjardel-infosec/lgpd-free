# LGPD Web App a fork from GDPR Registry Web App


Welcome to the repository. This repository is a fork, being translated and configured for use with the pt-be language

## Goals
To manage the whole LGPD process, you need a central point where information about LGPD procedures are stored and can be updated on a regular basis by dedicated personnel, including your Data Protection Officer. 

This central place is of fundamental importance to keep track of your current compliance status, identify issues and mitigate them. And this is exactly the role of the so-called Registry of Data Processing Activities, described in the GDPR Article 30 "Records of processing activities". It can also demonstrate that GDPR is a continuous process that has become an integral part of your business. 

This is a key step towards an enhanced security posture.

The LGPD Web App application allows you to track all activities of data processing with a hierarchical structure and the various stages for implementation of LGPD highlighted 

**Key Features**
* **Open Source**: You may freely use and modify it according to our licence.
* **Sound framework and suggestion mechanisms**: We implemented the Registry App exploiting to our expertise in the field of cybersecurity, and a thorough study of GDPR (which nowadays, it is essentially a cybersecurity problem) to build a comprehensive framework. As you fill in the registry, the app can suggest you how to proceed. We have inserted some useful suggestions that come from our GDPR framework and expertise.
* **Report Generation**: You can generate, anytime, an updated, high-quality PDF report with all your data registry. This is a very useful feature especially if you organization is under investigation by LGPD supervisory authorities.

## Demo
You can see a live demo of our application @ [https://registry-app.pluribus-one.it/en](https://registry-app.pluribus-one.it/en). Please note that the demo app has some limitation with respect the original one:

* is locked: does not allow any modification for security reasons. Anyway you can navigate and build a PDF report for the "Acme Inc." organization.
* embeds predefined lists in english language only.
* does not show login accesses in the dashboard for privacy reasons (the access controll app has been removed from the dashboard).

That is, Security & Privacy are important for us.

#### Demo Credentials
* Username: gdpr
* Password: pluribusone


#### Production Use
Please note that the provided virtual appliance is provided "as is" without warranty of any kind. It is not ready for production, especially if you plan to host your appliance with a public IP address. 
To this end, you may need to:

    
When running **python manage.py populate** you may choose to populate the database with predefined lists in

* italian (list.it.json)
* english (list.en.json)
* português brasileiro (list.brasil.json)

depending on your target language.

### Manual installation: Ubuntu (tested version: server [ Minimal .iso) x64, 20.04 LTS)
http://archive.ubuntu.com/ubuntu/dists/focal/main/installer-amd64/current/legacy-images/netboot/mini.iso

### Base Installation
The base installation can be used for testing purposes, as it runs the interface
locally @ http://127.0.0.1:29058. Open a shell and insert the following instructions (let's assume we created a **lgpd** user and we open a shell in its home: **/home/gdpr**):

    sudo apt update
    sudo apt install git python3-pip virtualenv
    git clone git clone https://github.com/housekore/lgpd-free
    virtualenv -p python3 python-venv
    source python-venv/bin/activate
    cd lgpd-free
    pip install -r requirements.txt
    python manage.py makemigrations axes audit jet dashboard
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py populate
    python manage.py collectstatic
    python manage.py runserver 0.0.0.0:29058 # For access out virtual machine

Now you can go to: `http://[server-ip]:29058/admin` with your browser. To log in use the (superuser) credentials previously created while executing `python manage.py createsuperuser`.

### Apache web server
In order to make your gdpr registry app available to other machines, you may use the Apache web server. Open a shell inside */home/lgpd* and digit:

    sudo apt install apache2 libapache2-mod-wsgi-py3
    sudo chown -R www-data:lgpd lgpd-free
    sudo a2enmod ssl
    sudo a2enmod headers
    sudo a2enmod rewrite
    sudo systemctl restart apache2

#### SSL Certificate
In order to protect your data in transit you need to setup a HTTPS certificate. You may choose to either 
* (a) generate a self-signed certificate OR 
* (b) install a certificate signed by a trusted certificate authority (**suggested option**).

##### (a) Self-signed
You may use a self-signed certificate if your app is running on a private network. In this case, however, your browser will probably raise an alert (and you may need to add an exception), because the certificate has not been signed by a trusted certificate authority. 

To create a self-signed certificate and update the apache configuration, open a shell and run the following code (inside the */home/gdpr/gdpr-registry-app* folder)
    
    sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /etc/ssl/private/apache-selfsigned.key -out /etc/ssl/certs/apache-selfsigned.crt
    sudo cp sample.apache.https.conf sample.apache.http.conf /etc/apache2/sites-available/
    sudo a2ensite sample.apache.https
    sudo a2ensite sample.apache.http
    sudo a2dissite 000-default
    sudo service apache2 restart

##### (b) Let's Encrypt
Let's Encrypt is a public Certificate Authority that provides free HTTPS certificates for any publicly available domain name.

###### Prerequisites
* Install the Apache web server as described in previous section
* Your machine needs a public IP address reachable at TCP port 80 (HTTP)
* Create a DNS entry for your domain **gdpr-registry.yourdomain.com** that resolves to the above-mentioned public IP address

Open a shell and insert the following commands:

    sudo add-apt-repository ppa:certbot/certbot
    sudo apt install python-certbot-apache
    sudo certbot --apache -d gdpr-registry.yourdomain.com

> **Hardening**. To harden your server configuration you may consider to run

    sudo cp sample.apache.security.conf /etc/apache2/conf-available/
    sudo a2enconf sample.apache.security

### Updates
You can update your installation anytime to the latest version using the following commands (open a shell in the installation folder: **/home/gdpr/gdpr-registry-app**):

    git pull
    python manage.py makemigrations axes audit jet dashboard
    python manage.py migrate
    python manage.py populate
    python manage.py collectstatic

## Donate
I am currently unemployed. If you are interested in making a donation via pix, you can use CPF 05966998671. In the name of José Jardel
